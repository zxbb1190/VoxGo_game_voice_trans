import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voxgo.asr.runaway_repetition import analyze_repetition, is_runaway_repetition


class RunawayRepetitionTest(unittest.TestCase):
    def test_detects_repeated_multiword_game_callout(self):
        text = " ".join(["The site is southwest."] * 40)
        analysis = analyze_repetition(text)

        self.assertEqual(analysis.word_count, 160)
        self.assertGreaterEqual(analysis.max_repeat_count, 4)
        self.assertGreaterEqual(analysis.repeated_ngram_words, 2)
        self.assertTrue(is_runaway_repetition(text))

    def test_detects_repeated_phrase_with_punctuation(self):
        text = " ".join(["I heard two sets of footsteps, but"] * 25)
        self.assertTrue(is_runaway_repetition(text))

    def test_detects_repeated_phrase_with_contractions(self):
        text = " ".join(["I'm going to go."] * 28)
        self.assertTrue(is_runaway_repetition(text))

    def test_detects_extreme_single_word_repetition(self):
        analysis = analyze_repetition("and " * 100)

        self.assertEqual(analysis.word_count, 100)
        self.assertEqual(analysis.repeated_ngram_words, 1)
        self.assertEqual(analysis.max_repeat_count, 100)
        self.assertTrue(is_runaway_repetition("and " * 100))

    def test_detects_numeric_loop_seen_in_fast_capture(self):
        # A captured SAPI phrase was followed by 27 repeated "8" tokens.
        # Digits must count as words even though they are not alphabetic.
        text = "8 " * 27
        self.assertEqual(analyze_repetition(text).word_count, 27)
        self.assertTrue(is_runaway_repetition(text, duration_seconds=2.0))

    def test_detects_qualifying_phrase_when_another_run_repeats_more_often(self):
        text = "and " * 8 + " ".join(["Enemy at the east site."] * 5)
        analysis = analyze_repetition(text)

        self.assertEqual(analysis.max_repeat_span_words, 25)
        self.assertEqual(analysis.max_repeat_count, 5)
        self.assertEqual(analysis.repeated_ngram_words, 5)
        self.assertTrue(is_runaway_repetition(text))

    def test_ignores_short_natural_repetitions(self):
        for text in ("go go go", "Go! Go! Go!", "Push, push, push!"):
            with self.subTest(text=text):
                self.assertFalse(is_runaway_repetition(text))

    def test_ignores_normal_long_text(self):
        text = (
            "The team moved through the western corridor while the captain called "
            "for everyone to check the next room. One player watched the stairs, "
            "another covered the door, and the rest waited for the signal to push. "
            "They heard a short burst of fire in the distance and rotated toward "
            "the objective together."
        )
        self.assertGreaterEqual(analyze_repetition(text).word_count, 30)
        self.assertFalse(is_runaway_repetition(text))

    def test_dominant_long_loop_is_blocked_even_at_normal_word_rate(self):
        text = " ".join(["The site is southwest."] * 40)

        self.assertTrue(is_runaway_repetition(text, duration_seconds=5))
        self.assertTrue(is_runaway_repetition(text, duration_seconds=30))

    def test_brief_repeat_inside_normal_speech_still_requires_high_word_rate(self):
        text = ("Check the stairs and watch the door. "
                + "Enemy at the east site. " * 5
                + "I will cover you while you move across the road.")
        self.assertTrue(is_runaway_repetition(text, duration_seconds=3))
        self.assertFalse(is_runaway_repetition(text, duration_seconds=30))

    def test_ordinary_short_multilingual_callouts_are_preserved(self):
        for text in ("go go go", "Push, push, push!", "No, no, no!", "Cover me!",
                     "走走走", "快快快", "行け、行け！", "빨리 빨리", "Давай, давай!"):
            with self.subTest(text=text):
                self.assertFalse(is_runaway_repetition(text, duration_seconds=0.5))

    def test_empty_and_non_string_input_are_safe(self):
        self.assertEqual(analyze_repetition("").word_count, 0)
        self.assertEqual(analyze_repetition(None).word_count, 0)
        self.assertFalse(is_runaway_repetition(""))


if __name__ == "__main__":
    unittest.main()
