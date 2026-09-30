import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voxgo.asr.whisper_engine import (
    GAME_EN_INITIAL_PROMPT,
    GAME_INITIAL_PROMPT,
    SpeechRecognizer,
    WhisperConfig,
)


class WhisperPromptTest(unittest.TestCase):
    def test_game_profile_uses_english_prompt_for_effective_english_model(self):
        recognizer = SpeechRecognizer(
            WhisperConfig(
                model_size="small",
                active_model_size="small.en",
                prompt_profile="game",
            )
        )

        self.assertEqual(recognizer._initial_prompt(), GAME_EN_INITIAL_PROMPT)
        self.assertNotIn("以下是", recognizer._initial_prompt())
        self.assertNotIn("This is real-time voice chat", recognizer._initial_prompt())

    def test_game_profile_keeps_multilingual_prompt_for_non_english_model(self):
        recognizer = SpeechRecognizer(
            WhisperConfig(model_size="small", prompt_profile="game")
        )

        self.assertEqual(recognizer._initial_prompt(), GAME_INITIAL_PROMPT)

    def test_explicit_game_en_profile_uses_english_prompt(self):
        recognizer = SpeechRecognizer(
            WhisperConfig(model_size="small.en", prompt_profile="game_en")
        )

        self.assertEqual(recognizer._initial_prompt(), GAME_EN_INITIAL_PROMPT)

    def test_explicit_custom_prompt_overrides_model_specific_game_prompt(self):
        recognizer = SpeechRecognizer(
            WhisperConfig(
                active_model_size="small.en",
                prompt_profile="game",
                initial_prompt="Custom vocabulary: Kestrel, B site.",
            )
        )

        self.assertEqual(
            recognizer._initial_prompt(),
            "Custom vocabulary: Kestrel, B site.",
        )


if __name__ == "__main__":
    unittest.main()
