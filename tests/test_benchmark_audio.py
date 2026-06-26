import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voxgo.audio.benchmark import (
    BenchmarkAudioOptions,
    BenchmarkAudioSource,
    load_benchmark_audio,
    resolve_benchmark_audio_path,
)
from voxgo.audio.capture import AudioConfig, LATENCY_MODE_BALANCED, LATENCY_MODE_FAST
from voxgo.config.loader import default_app_config
from voxgo.app import VoxGoApp


class BenchmarkAudioTest(unittest.TestCase):
    def test_resolve_benchmark_audio_prefers_existing_cwd_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            cwd = Path(tmp) / "cwd"
            root.mkdir()
            cwd.mkdir()
            existing = cwd / "voice.wav"
            existing.write_bytes(b"fake")

            resolved = resolve_benchmark_audio_path("voice.wav", project_root=root, cwd=cwd)

        self.assertEqual(resolved, existing)

    def test_load_wav_audio_resamples_to_target_rate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "voice.wav"
            self._write_wav(path, sample_rate=8000, seconds=0.25, channels=2)

            samples, sample_rate = load_benchmark_audio(path, target_sample_rate=16000)

        self.assertEqual(sample_rate, 16000)
        self.assertEqual(samples.dtype, np.int16)
        self.assertGreaterEqual(len(samples), 3990)
        self.assertLessEqual(len(samples), 4010)

    def test_benchmark_source_emits_fixed_length_looped_segment(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "short.wav"
            self._write_wav(path, sample_rate=16000, seconds=0.10, channels=1)
            segments = []
            source = BenchmarkAudioSource(
                AudioConfig(),
                BenchmarkAudioOptions(
                    path=path,
                    speech_seconds=0.25,
                    gap_seconds=0.10,
                    duration_seconds=1.0,
                ),
            )
            source.set_speech_callback(segments.append)

            source.start()
            source._next_emit_at = 0.0
            segment = source.process_audio()

        self.assertIs(segment, segments[0])
        self.assertEqual(segment.reason, "benchmark_audio")
        self.assertEqual(segment.sample_rate, 16000)
        self.assertAlmostEqual(segment.duration_seconds, 0.25, places=2)
        self.assertEqual(len(segment.audio_data), int(16000 * 0.25) * 2)
        self.assertEqual(source.selected_device["type"], "基准音频")

    def test_benchmark_game_mode_clamps_runtime_without_saved_settings(self):
        app = object.__new__(VoxGoApp)
        app.config = default_app_config()
        app.config.audio.latency_mode = "balanced"
        app.config.whisper.model_size = "small"
        app.config.whisper.device = "auto"
        app.config.whisper.auto_cpu_threads = True
        app.config.translation.max_concurrent_requests = 4

        VoxGoApp._apply_benchmark_game_mode(app)

        self.assertEqual(app.config.audio.latency_mode, "fast")
        self.assertEqual(app.config.whisper.active_model_size, "base")
        self.assertEqual(app.config.whisper.device, "cpu")
        self.assertEqual(app.config.whisper.compute_type, "int8")
        self.assertFalse(app.config.whisper.auto_cpu_threads)
        self.assertEqual(app.config.whisper.cpu_threads, 2)
        self.assertEqual(app.config.whisper.num_workers, 1)
        self.assertEqual(app.config.translation.max_concurrent_requests, 1)

    def test_benchmark_profile_d_forces_cuda_float16_without_game_policy(self):
        app = object.__new__(VoxGoApp)
        app.config = default_app_config()
        app._benchmark_profile = "d"
        app.config.audio.latency_mode = LATENCY_MODE_FAST
        app.config.whisper.device = "cpu"
        app.config.whisper.compute_type = "int8"

        VoxGoApp._apply_benchmark_profile(app)

        self.assertEqual(app.config.audio.latency_mode, LATENCY_MODE_BALANCED)
        self.assertEqual(app.config.whisper.active_model_size, "")
        self.assertEqual(app.config.whisper.device, "cuda")
        self.assertEqual(app.config.whisper.compute_type, "float16")

    def test_benchmark_profile_e_forces_cuda_int8_float16_without_game_policy(self):
        app = object.__new__(VoxGoApp)
        app.config = default_app_config()
        app._benchmark_profile = "e"
        app.config.audio.latency_mode = LATENCY_MODE_FAST
        app.config.whisper.device = "cpu"
        app.config.whisper.compute_type = "int8"

        VoxGoApp._apply_benchmark_profile(app)

        self.assertEqual(app.config.audio.latency_mode, LATENCY_MODE_BALANCED)
        self.assertEqual(app.config.whisper.active_model_size, "")
        self.assertEqual(app.config.whisper.device, "cuda")
        self.assertEqual(app.config.whisper.compute_type, "int8_float16")

    @staticmethod
    def _write_wav(path: Path, sample_rate: int, seconds: float, channels: int = 1):
        sample_count = int(sample_rate * seconds)
        t = np.arange(sample_count, dtype=np.float32) / sample_rate
        mono = (np.sin(2 * np.pi * 440 * t) * 12000).astype(np.int16)
        if channels > 1:
            audio = np.repeat(mono[:, None], channels, axis=1).reshape(-1)
        else:
            audio = mono
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio.tobytes())


if __name__ == "__main__":
    unittest.main()
