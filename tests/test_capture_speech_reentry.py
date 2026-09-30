import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voxgo.audio.capture import AudioConfig, SystemAudioCapture


class CaptureSpeechReentryTest(unittest.TestCase):
    SAMPLE_RATE = 16000
    BLOCK_SAMPLES = SAMPLE_RATE // 5  # 200 ms capture windows

    def make_capture(self, **overrides):
        values = dict(
            sample_rate=self.SAMPLE_RATE,
            chunk_duration_ms=200,
            speech_threshold_blocks=2,
            silence_limit_blocks=3,
            noise_calibration_seconds=0,
            silence_threshold=-40,
            min_speech_threshold=-45,
            pre_roll_ms=0,
        )
        values.update(overrides)
        config = AudioConfig(**values)
        capture = SystemAudioCapture(config)
        self.addCleanup(capture.stop)
        return capture

    @classmethod
    def block(cls, amplitude):
        samples = np.full(cls.BLOCK_SAMPLES, amplitude, dtype=np.int16)
        return samples.tobytes()

    @staticmethod
    def process(capture, block):
        capture._audio_queue.put(block)
        return capture.process_audio()

    def test_reentry_after_two_inactive_windows_starts_new_segment_without_losing_pcm(self):
        # Cover both accepted activity paths: a below-peak onset accepted by
        # the energy gate, and a quieter onset accepted by VAD alone.
        for onset_amplitude, onset_vad in ((1800, False), (200, True)):
            with self.subTest(onset_amplitude=onset_amplitude, onset_vad=onset_vad):
                capture = self.make_capture()
                frames = [
                    self.block(5800),  # prior speech, roughly -15 dBFS
                    self.block(5800),
                    self.block(900),   # quiet tail
                    self.block(0),     # silence; below the 3-window end limit
                    self.block(onset_amplitude),
                    self.block(0),
                    self.block(0),
                    self.block(0),
                ]
                vad_results = [(True, 1.0), (True, 1.0), (False, 0.0), (False, 0.0)]
                vad_results.append((onset_vad, 1.0 if onset_vad else 0.0))
                vad_results.extend([(False, 0.0)] * 3)

                segments = []
                with patch.object(capture, "_is_vad_speech", side_effect=vad_results):
                    for frame in frames:
                        segment = self.process(capture, frame)
                        if segment is not None:
                            segments.append(segment)

                self.assertEqual(len(segments), 2)
                # The first return is triggered by reentry, and must end before
                # the onset block. The onset then heads the next candidate.
                self.assertEqual(segments[0].audio_data, b"".join(frames[:4]))
                self.assertEqual(segments[1].audio_data, b"".join(frames[4:]))
                self.assertEqual(segments[0].block_count, 4)
                self.assertEqual(segments[1].block_count, 4)
                self.assertEqual(b"".join(s.audio_data for s in segments), b"".join(frames))

    def test_one_quiet_window_then_voice_stays_in_same_segment(self):
        capture = self.make_capture()
        frames = [
            self.block(5800),
            self.block(5800),
            self.block(900),  # one quiet window is shorter than end threshold
            self.block(1800), # quiet onset resumes before the segment ends
            self.block(0),
            self.block(0),
            self.block(0),
        ]

        with patch.object(
            capture,
            "_is_vad_speech",
            side_effect=[(True, 1.0), (True, 1.0), (False, 0.0), (True, 1.0)] + [(False, 0.0)] * 3,
        ):
            results = [self.process(capture, frame) for frame in frames]

        emitted = [segment for segment in results if segment is not None]
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0].audio_data, b"".join(frames))
        self.assertEqual(emitted[0].block_count, len(frames))

    def test_accurate_mode_reentry_respects_its_longer_pause_limit(self):
        # Accurate mode waits five inactive blocks to end a segment. A reentry
        # split may occur after four, but must not jump ahead after only two.
        for pause_blocks, expected_split in ((2, False), (4, True)):
            with self.subTest(pause_blocks=pause_blocks):
                capture = self.make_capture(silence_limit_blocks=5)
                frames = [self.block(5800), self.block(5800)]
                frames += [self.block(0)] * pause_blocks
                frames.append(self.block(1800))
                vad_results = [(True, 1.0), (True, 1.0)]
                vad_results += [(False, 0.0)] * pause_blocks
                vad_results.append((True, 1.0))
                with patch.object(capture, "_is_vad_speech", side_effect=vad_results):
                    results = [self.process(capture, frame) for frame in frames]
                emitted = [segment for segment in results if segment is not None]
                self.assertEqual(bool(emitted), expected_split)
                if expected_split:
                    self.assertEqual(emitted[0].audio_data, b"".join(frames[:-1]))

    def test_steady_low_energy_tail_still_reaches_silence_end(self):
        capture = self.make_capture()
        speech = self.block(5800)
        tail = self.block(900)  # Above the absolute gate, below the peak tail gate.
        frames = [speech, speech] + [tail] * 10
        vad_results = [(True, 1.0), (True, 1.0)] + [(False, 0.0)] * 10
        with patch.object(capture, "_is_vad_speech", side_effect=vad_results):
            emitted = [segment for frame in frames
                       if (segment := self.process(capture, frame)) is not None]

        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0].audio_data, b"".join(frames[:5]))
        self.assertEqual(emitted[0].block_count, 5)

    def test_reentry_callback_receives_each_segment_once(self):
        capture = self.make_capture()
        callbacks = []
        capture.set_speech_callback(callbacks.append)
        frames = [self.block(5800)] * 2 + [self.block(0)] * 2
        frames += [self.block(1800)] + [self.block(0)] * 3
        vad_results = [(True, 1.0)] * 2 + [(False, 0.0)] * 2
        vad_results += [(True, 1.0)] + [(False, 0.0)] * 3
        with patch.object(capture, "_is_vad_speech", side_effect=vad_results):
            returned = [segment for frame in frames
                        if (segment := self.process(capture, frame)) is not None]

        self.assertEqual(len(returned), 2)
        self.assertEqual(callbacks, returned)
        self.assertEqual(b"".join(segment.audio_data for segment in callbacks), b"".join(frames))

    def test_silence_end_and_force_split_still_emit(self):
        capture = self.make_capture(silence_limit_blocks=2)
        speech = self.block(5800)
        silence = self.block(0)
        with patch.object(
            capture,
            "_is_vad_speech",
            side_effect=[(True, 1.0), (True, 1.0), (False, 0.0), (False, 0.0)],
        ):
            self.assertIsNone(self.process(capture, speech))
            self.assertIsNone(self.process(capture, speech))
            self.assertIsNone(self.process(capture, silence))
            ended = self.process(capture, silence)
        self.assertIsNotNone(ended)
        self.assertIn("静音结束", ended.reason)
        self.assertEqual(ended.audio_data, speech + speech + silence + silence)

        split_capture = self.make_capture(max_buffer_blocks=2)
        with patch.object(split_capture, "_is_vad_speech", side_effect=[(True, 1.0), (True, 1.0)]):
            self.assertIsNone(self.process(split_capture, speech))
            split = self.process(split_capture, speech)
        self.assertIsNotNone(split)
        self.assertIn("达到块数上限", split.reason)
        self.assertEqual(split.audio_data, speech + speech)


if __name__ == "__main__":
    unittest.main()
