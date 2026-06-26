import time
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Tuple, Union

import numpy as np
from loguru import logger

from voxgo.audio.capture import AudioConfig, SpeechSegment, calculate_rms_dbfs


@dataclass(frozen=True)
class BenchmarkAudioOptions:
    path: Path
    speech_seconds: float = 4.0
    gap_seconds: float = 3.0
    duration_seconds: float = 300.0
    sample_rate: int = 16000


def resolve_benchmark_audio_path(value: str, project_root: Path = None, cwd: Path = None) -> Path:
    requested = Path(value).expanduser()
    if requested.is_absolute():
        return requested

    cwd = cwd or Path.cwd()
    project_root = project_root or Path(__file__).resolve().parents[2]
    cwd_candidate = cwd / requested
    if cwd_candidate.exists():
        return cwd_candidate
    return project_root / requested


def load_benchmark_audio(path: Union[str, Path], target_sample_rate: int = 16000) -> Tuple[np.ndarray, int]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"benchmark audio not found: {source}")

    suffix = source.suffix.lower()
    if suffix == ".wav":
        samples, sample_rate = _load_wav_audio(source)
        if sample_rate != target_sample_rate:
            samples = _resample_int16(samples, sample_rate, target_sample_rate)
            sample_rate = target_sample_rate
        return samples, sample_rate

    return _load_compressed_audio(source, target_sample_rate)


class BenchmarkAudioSource:
    """Inject a fixed audio file as repeatable speech segments for performance tests."""

    def __init__(self, config: AudioConfig, options: BenchmarkAudioOptions):
        self.config = config
        self.options = options
        self._on_speech_callback: Optional[Callable[[SpeechSegment], None]] = None
        self._running = False
        self._started_at = 0.0
        self._next_emit_at = 0.0
        self._cursor = 0
        self._emitted_segments = 0
        self._complete_logged = False
        self._audio, self._sample_rate = load_benchmark_audio(options.path, options.sample_rate)
        self.config.sample_rate = self._sample_rate
        self.config.channels = 1
        duration = len(self._audio) / max(1, self._sample_rate)
        self.selected_device = {
            "index": "benchmark",
            "name": str(options.path),
            "device_id": f"benchmark:{options.path}",
            "type": "基准音频",
            "sample_rate": self._sample_rate,
            "channels": 1,
            "is_loopback": False,
        }
        logger.info(
            "benchmark audio loaded: path={}, duration={:.1f}s, sample_rate={}Hz, speech={}s, gap={}s, test_duration={}s",
            options.path,
            duration,
            self._sample_rate,
            options.speech_seconds,
            options.gap_seconds,
            options.duration_seconds,
        )

    def start(self):
        self._running = True
        self._started_at = time.monotonic()
        self._next_emit_at = self._started_at + max(0.01, float(self.options.speech_seconds))
        self._complete_logged = False
        logger.info("benchmark audio source started: {}", self.options.path)

    def stop(self):
        self._running = False
        logger.info("benchmark audio source stopped")

    def set_speech_callback(self, callback: Callable[[SpeechSegment], None]):
        self._on_speech_callback = callback

    def current_noise_gate(self):
        return None, float(getattr(self.config, "silence_threshold", -40.0) or -40.0), True

    def clear_pending_audio(self) -> int:
        logger.info("benchmark audio pending buffers cleared")
        return 0

    def process_audio(self) -> Optional[SpeechSegment]:
        if not self._running:
            return None

        now = time.monotonic()
        duration_limit = max(0.0, float(self.options.duration_seconds or 0.0))
        if duration_limit > 0 and now - self._started_at >= duration_limit:
            if not self._complete_logged:
                self._complete_logged = True
                logger.info(
                    "benchmark audio completed: elapsed={:.1f}s, emitted_segments={}",
                    now - self._started_at,
                    self._emitted_segments,
                )
            return None

        if now < self._next_emit_at:
            return None

        segment = self._next_segment()
        self._emitted_segments += 1
        interval = max(0.01, float(self.options.speech_seconds)) + max(0.0, float(self.options.gap_seconds))
        self._next_emit_at = now + interval
        logger.info(
            "benchmark speech segment injected: #{} {:.1f}s, next_in={:.1f}s",
            self._emitted_segments,
            segment.duration_seconds,
            interval,
        )
        if self._on_speech_callback:
            self._on_speech_callback(segment)
        return segment

    def _next_segment(self) -> SpeechSegment:
        speech_seconds = max(0.05, float(self.options.speech_seconds))
        sample_count = max(1, int(round(self._sample_rate * speech_seconds)))
        samples = self._slice_looped_audio(sample_count)
        peak_rms = calculate_rms_dbfs(samples)
        return SpeechSegment(
            audio_data=samples.astype(np.int16, copy=False).tobytes(),
            sample_rate=self._sample_rate,
            duration_seconds=len(samples) / max(1, self._sample_rate),
            voice_duration_seconds=len(samples) / max(1, self._sample_rate),
            block_count=1,
            voice_blocks=1,
            peak_rms_dbfs=float(peak_rms),
            energy_threshold_dbfs=float(getattr(self.config, "silence_threshold", -40.0) or -40.0),
            noise_floor_dbfs=None,
            reason="benchmark_audio",
            vad_voice_blocks=1,
            energy_voice_blocks=1,
            vad_confidence=1.0,
            activity_source="benchmark",
        )

    def _slice_looped_audio(self, sample_count: int) -> np.ndarray:
        if len(self._audio) == 0:
            return np.zeros(sample_count, dtype=np.int16)

        remaining = sample_count
        chunks = []
        while remaining > 0:
            available = len(self._audio) - self._cursor
            take = min(remaining, available)
            chunks.append(self._audio[self._cursor:self._cursor + take])
            self._cursor += take
            remaining -= take
            if self._cursor >= len(self._audio):
                self._cursor = 0
        if len(chunks) == 1:
            return chunks[0].copy()
        return np.concatenate(chunks).astype(np.int16, copy=False)


def _load_wav_audio(path: Path) -> Tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wf:
        channels = wf.getnchannels()
        sample_rate = wf.getframerate()
        sample_width = wf.getsampwidth()
        frames = wf.readframes(wf.getnframes())

    if sample_width == 1:
        audio = (np.frombuffer(frames, dtype=np.uint8).astype(np.int16) - 128) << 8
    elif sample_width == 2:
        audio = np.frombuffer(frames, dtype=np.int16)
    elif sample_width == 4:
        audio = (np.frombuffer(frames, dtype=np.int32) >> 16).astype(np.int16)
    else:
        raise RuntimeError(f"unsupported WAV sample width: {sample_width} bytes")

    return _to_mono_int16(audio, channels), sample_rate


def _load_compressed_audio(path: Path, target_sample_rate: int) -> Tuple[np.ndarray, int]:
    try:
        import av
    except Exception as exc:
        raise RuntimeError(
            f"{path.suffix or 'compressed audio'} benchmark input requires PyAV. "
            "Install av or convert the file to WAV first."
        ) from exc

    chunks = []
    with av.open(str(path)) as container:
        audio_streams = [stream for stream in container.streams if stream.type == "audio"]
        if not audio_streams:
            raise RuntimeError(f"benchmark audio has no audio stream: {path}")
        stream = audio_streams[0]
        resampler = av.AudioResampler(format="s16", layout="mono", rate=target_sample_rate)
        for frame in container.decode(stream):
            for output_frame in _resample_av_frame(resampler, frame):
                arr = output_frame.to_ndarray()
                chunks.append(arr.reshape(-1).astype(np.int16, copy=False))
        for output_frame in _flush_av_resampler(resampler):
            arr = output_frame.to_ndarray()
            chunks.append(arr.reshape(-1).astype(np.int16, copy=False))

    if not chunks:
        raise RuntimeError(f"benchmark audio decoded to no samples: {path}")
    return np.concatenate(chunks).astype(np.int16, copy=False), target_sample_rate


def _resample_av_frame(resampler, frame):
    frames = resampler.resample(frame)
    if frames is None:
        return []
    if isinstance(frames, (list, tuple)):
        return frames
    return [frames]


def _flush_av_resampler(resampler):
    try:
        frames = resampler.resample(None)
    except Exception:
        return []
    if frames is None:
        return []
    if isinstance(frames, (list, tuple)):
        return frames
    return [frames]


def _to_mono_int16(audio: np.ndarray, channels: int) -> np.ndarray:
    channels = max(1, int(channels or 1))
    if channels <= 1:
        return audio.astype(np.int16, copy=False)
    frame_count = len(audio) // channels
    if frame_count <= 0:
        return np.array([], dtype=np.int16)
    trimmed = audio[:frame_count * channels].reshape(-1, channels)
    return trimmed.astype(np.float32).mean(axis=1).clip(-32768, 32767).astype(np.int16)


def _resample_int16(audio: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    source_rate = int(source_rate or target_rate)
    target_rate = int(target_rate or source_rate)
    if source_rate == target_rate:
        return audio.astype(np.int16, copy=False)
    if len(audio) == 0:
        return audio.astype(np.int16, copy=False)
    try:
        import soxr

        resampled = soxr.resample(
            audio.astype(np.float32) / 32768.0,
            source_rate,
            target_rate,
            quality="soxr_hq",
        )
    except Exception as exc:
        logger.warning("benchmark soxr resample failed, using linear interpolation: {}", exc)
        target_len = max(1, int(round(len(audio) * target_rate / source_rate)))
        x_old = np.linspace(0, 1, len(audio), dtype=np.float32)
        x_new = np.linspace(0, 1, target_len, dtype=np.float32)
        resampled = np.interp(x_new, x_old, audio.astype(np.float32) / 32768.0)
    return np.clip(resampled * 32768.0, -32768, 32767).astype(np.int16)
