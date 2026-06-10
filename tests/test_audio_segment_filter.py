import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voxgo.audio.capture import (
    LATENCY_MODE_ACCURATE,
    LATENCY_MODE_BALANCED,
    LATENCY_MODE_FAST,
    SAFE_MAX_SPEECH_THRESHOLD_DBFS,
    AudioConfig,
    SpeechSegment,
    SystemAudioCapture,
    apply_audio_latency_preset,
    infer_latency_mode,
    normalize_latency_mode,
    should_drop_speech_segment,
)


def _segment(**overrides):
    values = {
        "audio_data": b"\0\0" * 16000,
        "sample_rate": 16000,
        "duration_seconds": 1.2,
        "voice_duration_seconds": 0.8,
        "block_count": 8,
        "voice_blocks": 4,
        "peak_rms_dbfs": -30.0,
        "energy_threshold_dbfs": -40.0,
        "noise_floor_dbfs": -48.0,
        "reason": "test",
    }
    values.update(overrides)
    return SpeechSegment(**values)


class SpeechSegmentFilterTest(unittest.TestCase):
    def test_drops_short_active_voice_even_when_total_segment_is_longer(self):
        config = AudioConfig(min_segment_seconds=0.45, min_segment_peak_margin_db=0)
        segment = _segment(duration_seconds=1.3, voice_duration_seconds=0.2)

        reason = should_drop_speech_segment(segment, config)

        self.assertIn("语音活跃时长", reason)

    def test_drops_segments_that_only_barely_cross_the_gate(self):
        config = AudioConfig(min_segment_seconds=0.1, min_segment_peak_margin_db=2.0)
        segment = _segment(voice_duration_seconds=0.8, peak_rms_dbfs=-38.5, energy_threshold_dbfs=-40.0)

        reason = should_drop_speech_segment(segment, config)

        self.assertIn("峰值余量", reason)

    def test_keeps_segments_with_enough_duration_and_peak_margin(self):
        config = AudioConfig(min_segment_seconds=0.45, min_segment_peak_margin_db=2.0)
        segment = _segment(voice_duration_seconds=0.7, peak_rms_dbfs=-35.0, energy_threshold_dbfs=-40.0)

        self.assertEqual(should_drop_speech_segment(segment, config), "")

    def test_legacy_segments_without_capture_metadata_are_not_filtered(self):
        config = AudioConfig(min_segment_seconds=0.45, min_segment_peak_margin_db=2.0)
        segment = _segment(block_count=0, voice_blocks=0, voice_duration_seconds=0.1)

        self.assertEqual(should_drop_speech_segment(segment, config), "")


class AudioLatencyModeTest(unittest.TestCase):
    def test_normalizes_legacy_low_latency_to_fast(self):
        self.assertEqual(normalize_latency_mode("low_latency"), LATENCY_MODE_FAST)
        self.assertEqual(normalize_latency_mode("低延迟"), LATENCY_MODE_FAST)

    def test_applies_balanced_preset(self):
        config = AudioConfig(latency_mode=LATENCY_MODE_BALANCED)

        mode = apply_audio_latency_preset(config)

        self.assertEqual(mode, LATENCY_MODE_BALANCED)
        self.assertEqual(config.chunk_duration_ms, 200)
        self.assertEqual(config.speech_threshold_blocks, 2)
        self.assertEqual(config.silence_limit_blocks, 3)
        self.assertEqual(config.max_speech_seconds, 4.5)
        self.assertEqual(config.pre_roll_ms, 450)
        self.assertEqual(config.speech_idle_timeout_ms, 450)
        self.assertEqual(config.min_segment_seconds, 0.35)
        self.assertEqual(config.min_segment_peak_margin_db, 1.5)

    def test_applies_fast_preset(self):
        config = AudioConfig(latency_mode=LATENCY_MODE_FAST)

        mode = apply_audio_latency_preset(config)

        self.assertEqual(mode, LATENCY_MODE_FAST)
        self.assertEqual(config.chunk_duration_ms, 120)
        self.assertEqual(config.speech_threshold_blocks, 2)
        self.assertEqual(config.silence_limit_blocks, 3)
        self.assertEqual(config.max_speech_seconds, 3.0)
        self.assertEqual(config.pre_roll_ms, 300)
        self.assertEqual(config.speech_idle_timeout_ms, 350)
        self.assertEqual(config.min_segment_seconds, 0.30)
        self.assertEqual(config.min_segment_peak_margin_db, 1.0)

    def test_applies_accurate_preset(self):
        config = AudioConfig(latency_mode=LATENCY_MODE_ACCURATE)

        mode = apply_audio_latency_preset(config)

        self.assertEqual(mode, LATENCY_MODE_ACCURATE)
        self.assertEqual(config.chunk_duration_ms, 300)
        self.assertEqual(config.speech_threshold_blocks, 2)
        self.assertEqual(config.silence_limit_blocks, 5)
        self.assertEqual(config.max_speech_seconds, 8.0)
        self.assertEqual(config.pre_roll_ms, 600)
        self.assertEqual(config.speech_idle_timeout_ms, 900)

    def test_infers_legacy_accurate_tuning_without_mode(self):
        config = AudioConfig(
            latency_mode="",
            chunk_duration_ms=300,
            speech_threshold_blocks=2,
            silence_limit_blocks=5,
            max_buffer_blocks=120,
            max_speech_seconds=8.0,
            pre_roll_ms=600,
            speech_idle_timeout_ms=900,
        )

        self.assertEqual(infer_latency_mode(config), LATENCY_MODE_ACCURATE)


class AudioNoiseGateTest(unittest.TestCase):
    def test_caps_legacy_high_speech_gate_on_reuse(self):
        config = AudioConfig(
            max_speech_threshold=-20.0,
            initial_noise_floor_dbfs=-27.2,
            initial_energy_threshold_dbfs=-20.2,
        )

        capture = SystemAudioCapture(config)

        self.assertEqual(capture.current_noise_gate()[1], SAFE_MAX_SPEECH_THRESHOLD_DBFS)


if __name__ == "__main__":
    unittest.main()
