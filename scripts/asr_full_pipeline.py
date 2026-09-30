"""Wall-clock replay through VoxGo's real capture and speech worker."""

from __future__ import annotations

import itertools
import time
from collections import defaultdict

from voxgo.asr.pipeline import SpeechPipeline
from voxgo.audio.capture import AudioConfig, apply_audio_latency_preset, apply_english_realtime_latency_bias
from voxgo.config.loader import default_app_config
from voxgo.runtime.events import EventBus, TranscriptReady


class RecordingRecognizer:
    def __init__(self, recognizer):
        self.recognizer = recognizer
        self.calls = []

    def __getattr__(self, name):
        return getattr(self.recognizer, name)

    def transcribe_audio_bytes_with_language(self, audio_bytes, sample_rate=44100, language_override=None):
        started = time.perf_counter()
        result = self.recognizer.transcribe_audio_bytes_with_language(
            audio_bytes, sample_rate=sample_rate, language_override=language_override
        )
        self.calls.append((audio_bytes, result, time.perf_counter() - started))
        return result


def run_full_pipeline(samples, preset: str, recognizer):
    """Return actual TranscriptReady output and ASR calls for one isolated clip."""
    # Keep the same English audio bias as the capture_cut path.
    audio = AudioConfig(latency_mode=preset, sample_rate=16000, channels=1)
    apply_audio_latency_preset(audio)
    apply_english_realtime_latency_bias(audio, preset)
    config = default_app_config()
    config.audio = audio
    config.whisper = recognizer.config
    config.whisper.pure_english_environment = True
    config.whisper.language = "en"
    config.translation.source_lang = "en"
    config.translation.target_lang = "zh"

    events = []
    notices = []
    bus = EventBus()
    bus.subscribe(TranscriptReady, events.append)
    recorded = RecordingRecognizer(recognizer)
    stats = defaultdict(int)
    ids = itertools.count(1)
    pipeline = SpeechPipeline(
        lambda: config, lambda: recorded, bus, stats,
        lambda: True, lambda: False, lambda: str(next(ids)), {},
        lambda *args: notices.append(args),
    )
    # Import here to avoid a circular import with the benchmark runner.
    from scripts.run_asr_benchmark import capture_segments

    pipeline.start()
    try:
        captured = capture_segments(
            samples, preset,
            on_segment=lambda segment, _source_seconds: pipeline.on_speech_detected(segment),
            pace_realtime=True,
        )
        # Pending candidates are released by the real worker's timeout loop.
        # Keep the worker alive until every queued item has passed ASR/filtering.
        deadline = time.monotonic() + max(60.0, len(samples) / 16000 * 4 + 20)
        while time.monotonic() < deadline:
            if (pipeline._queue.empty() and not pipeline._recognition_busy
                    and not pipeline._pending_buffer.has_pending()
                    and not pipeline._busy_weak_buffer.has_pending()):
                time.sleep(0.25)
                if (pipeline._queue.empty() and not pipeline._recognition_busy
                        and not pipeline._pending_buffer.has_pending()
                        and not pipeline._busy_weak_buffer.has_pending()):
                    break
            time.sleep(0.05)
        else:
            raise TimeoutError("speech pipeline did not drain")
    finally:
        if not pipeline.stop():
            raise TimeoutError("speech worker did not stop")
    if stats.get("errors", 0):
        raise RuntimeError(f"speech pipeline reported {stats['errors']} recognition errors")
    return {
        "hypothesis": " ".join(event.text for event in events).strip(),
        "raw_hypothesis": " ".join(str(getattr(result, "raw_text", getattr(result, "text", "")) or "")
                                   for _, result, _ in recorded.calls).strip(),
        "events": events,
        "calls": recorded.calls,
        "captured_segments": captured,
        "stats": dict(stats),
        "notices": notices,
    }
