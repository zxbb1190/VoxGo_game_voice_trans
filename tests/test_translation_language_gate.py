import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voxgo.translation import TranslationConfig, should_skip_translation_for_language


class TranslationLanguageGateTest(unittest.TestCase):
    def test_en_to_zh_skips_high_confidence_chinese(self):
        reason = should_skip_translation_for_language(
            "你好",
            "en",
            "zh",
            0.95,
            TranslationConfig(source_lang="en", target_lang="zh"),
        )

        self.assertIn("language_mismatch:zh->en", reason)

    def test_zh_to_en_skips_high_confidence_english(self):
        reason = should_skip_translation_for_language(
            "push left",
            "zh",
            "en",
            0.90,
            TranslationConfig(source_lang="zh", target_lang="en"),
        )

        self.assertIn("language_mismatch:en->zh", reason)

    def test_low_confidence_language_mismatch_is_allowed(self):
        reason = should_skip_translation_for_language(
            "push left",
            "en",
            "zh",
            0.50,
            TranslationConfig(source_lang="en", target_lang="zh"),
        )

        self.assertEqual(reason, "")

    def test_short_text_uses_higher_probability_threshold(self):
        reason = should_skip_translation_for_language(
            "go",
            "zh",
            "en",
            0.70,
            TranslationConfig(source_lang="zh", target_lang="en"),
        )

        self.assertEqual(reason, "")

    def test_script_mismatch_catches_fixed_whisper_language(self):
        reason = should_skip_translation_for_language(
            "你好",
            "en",
            "en",
            0.95,
            TranslationConfig(source_lang="en", target_lang="zh"),
        )

        self.assertIn("text_script_mismatch:zh->en", reason)

    def test_disabled_gate_allows_mismatch(self):
        reason = should_skip_translation_for_language(
            "你好",
            "en",
            "zh",
            0.95,
            TranslationConfig(source_lang="en", target_lang="zh", skip_language_mismatch=False),
        )

        self.assertEqual(reason, "")


if __name__ == "__main__":
    unittest.main()
