import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voxgo.audio.capture import AudioConfig, SystemAudioCapture


class CaptureVoiceCandidateTest(unittest.TestCase):
    def test_raw_audio_queue_drops_oldest_block_when_full(self):
        config = AudioConfig(audio_queue_max_blocks=2)
        capture = SystemAudioCapture(config)

        capture._enqueue_audio_block(b"one")
        capture._enqueue_audio_block(b"two")
        capture._enqueue_audio_block(b"three")

        self.assertEqual(capture._audio_queue.get_nowait(), b"two")
        self.assertEqual(capture._audio_queue.get_nowait(), b"three")
        self.assertEqual(capture._dropped_audio_queue_blocks, 1)

    def test_short_vad_segment_is_emitted_not_reset_before_pipeline(self):
        config = AudioConfig(
            sample_rate=16000,
            chunk_duration_ms=100,
            speech_threshold_blocks=3,
            silence_limit_blocks=1,
            noise_calibration_seconds=0,
            silence_threshold=-10,
        )
        capture = SystemAudioCapture(config)
        capture._audio_queue.put(b"\x01\x00" * 1600)

        with patch.object(capture, "_is_vad_speech", side_effect=[(True, 1.0), (False, 0.0)]):
            self.assertIsNone(capture.process_audio())
            capture._audio_queue.put(b"\x00\x00" * 1600)
            segment = capture.process_audio()

        self.assertIsNotNone(segment)
        self.assertIn("candidate_short_segment", segment.reason)
        self.assertEqual(segment.vad_voice_blocks, 1)
        self.assertEqual(segment.activity_source, "vad")

    def test_energy_only_activity_is_candidate_metadata_not_voice_blocks(self):
        config = AudioConfig(
            sample_rate=16000,
            chunk_duration_ms=100,
            speech_threshold_blocks=2,
            silence_limit_blocks=1,
            noise_calibration_seconds=0,
            min_speech_threshold=-100,
            silence_threshold=-80,
        )
        capture = SystemAudioCapture(config)
        capture._audio_queue.put(b"\x20\x00" * 1600)

        with patch.object(capture, "_is_vad_speech", side_effect=[(False, 0.0), (False, 0.0)]):
            self.assertIsNone(capture.process_audio())
            capture._audio_queue.put(b"\x00\x00" * 1600)
            segment = capture.process_audio()

        self.assertIsNotNone(segment)
        self.assertEqual(segment.vad_voice_blocks, 0)
        self.assertGreaterEqual(segment.energy_voice_blocks, 1)
        self.assertEqual(segment.activity_source, "energy")


if __name__ == "__main__":
    unittest.main()
