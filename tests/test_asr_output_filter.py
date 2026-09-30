import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voxgo.asr.whisper_engine import (
    SpeechRecognizer, TranscriptionResult, WhisperConfig, should_drop_transcription_result,
)


def _result(text, avg_logprob=-0.2, no_speech_prob=0.2):
    return TranscriptionResult(
        text,
        "en",
        0.95,
        avg_logprob=avg_logprob,
        no_speech_prob=no_speech_prob,
        compression_ratio=1.0,
        segment_count=1,
    )


class ASROutputFilterTest(unittest.TestCase):
    def test_high_no_speech_short_phrase_is_filtered(self):
        reason = should_drop_transcription_result(_result("Thank you.", avg_logprob=-0.89, no_speech_prob=0.80))

        self.assertIn("global_asr_no_speech_short", reason)

    def test_low_logprob_short_noise_is_filtered(self):
        reason = should_drop_transcription_result(_result("Got it.", avg_logprob=-1.27, no_speech_prob=0.20))

        self.assertIn("global_asr_low_logprob_short", reason)

    def test_yoy_noise_token_is_filtered(self):
        reason = should_drop_transcription_result(_result("Yoy.", avg_logprob=-1.27, no_speech_prob=0.40))

        self.assertIn("global_asr_noise_token", reason)

    def test_short_noise_token_is_filtered(self):
        reason = should_drop_transcription_result(_result("BAM", avg_logprob=-0.97, no_speech_prob=0.36))

        self.assertIn("global_asr_noise_token", reason)

    def test_repeated_noise_word_is_filtered(self):
        reason = should_drop_transcription_result(_result("Shoooooo", avg_logprob=-0.09, no_speech_prob=0.52))

        self.assertIn("global_asr_repeated_noise", reason)

    def test_real_short_sentence_is_kept(self):
        reason = should_drop_transcription_result(_result("I don't know.", avg_logprob=-0.47, no_speech_prob=0.14))

        self.assertEqual(reason, "")

    def test_game_command_is_not_filtered_just_for_being_short(self):
        reason = should_drop_transcription_result(_result("push", avg_logprob=-0.2, no_speech_prob=0.2))

        self.assertEqual(reason, "")

    def test_short_spoken_repetitions_remain_valid(self):
        for text in ("go go go", "Go! Go! Go!", "go go go go", "Push, push, push!"):
            with self.subTest(text=text):
                self.assertEqual(should_drop_transcription_result(_result(text)), "")
                self.assertEqual(
                    should_drop_transcription_result(_result(text, no_speech_prob=0.69)), ""
                )

    def test_high_no_speech_repeated_phrase_is_still_filtered(self):
        self.assertIn(
            "global_asr_no_speech_repeated_phrase",
            should_drop_transcription_result(_result("Okay. " * 6, no_speech_prob=0.69)),
        )

    def test_long_multilingual_phrase_loops_are_still_filtered(self):
        for text in ("Roger that. " * 6, "我在中路。" * 10):
            with self.subTest(text=text):
                self.assertIn("global_asr_repeated_phrase", should_drop_transcription_result(_result(text)))

    def test_whisper_repetition_guard_keeps_raw_diagnostic(self):
        recognizer = SpeechRecognizer(WhisperConfig())
        repeated = " ".join(["The site is southwest."] * 40)
        recognizer._model = SimpleNamespace(transcribe=lambda *_args, **_kwargs: (
            [SimpleNamespace(text=repeated, avg_logprob=-0.08,
                             no_speech_prob=0.01, compression_ratio=22.24)],
            SimpleNamespace(language="en", language_probability=0.99),
        ))
        result = recognizer._transcribe_audio_array(np.zeros(32000, dtype=np.float32), "en", "")
        self.assertEqual(result.text, "")
        self.assertEqual(result.raw_text, repeated)
        self.assertTrue(result.runaway_guarded)
        self.assertEqual(should_drop_transcription_result(result), "global_asr_runaway_repetition")

    def test_whisper_guard_preserves_natural_repetition(self):
        recognizer = SpeechRecognizer(WhisperConfig())
        text = "Go! Go! Go!"
        recognizer._model = SimpleNamespace(transcribe=lambda *_args, **_kwargs: (
            [SimpleNamespace(text=text, avg_logprob=-0.08,
                             no_speech_prob=0.01, compression_ratio=2.0)],
            SimpleNamespace(language="en", language_probability=0.99),
        ))
        result = recognizer._transcribe_audio_array(np.zeros(16000, dtype=np.float32), "en", "")
        self.assertEqual(result.text, text)
        self.assertFalse(result.runaway_guarded)


if __name__ == "__main__":
    unittest.main()
