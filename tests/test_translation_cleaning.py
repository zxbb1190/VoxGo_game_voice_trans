import asyncio
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voxgo.runtime.events import EventBus, TranslationReady
from voxgo.runtime.work_items import LatencyTrace
from voxgo.translation import GameTranslator, TranslationConfig
from voxgo.translation.base import TranslationResult, clean_translation_output, local_phrase_cache_lookup
from voxgo.translation.runtime import TranslationRuntime


class TaggedTranslator:
    async def translate_result(self, text, detected_language=""):
        return TranslationResult("<target_text>你好</target_text>", "en", "zh", "fake")


class TranslationCleaningTest(unittest.TestCase):
    def test_clean_translation_output_removes_target_text_tags(self):
        self.assertEqual(clean_translation_output("<target_text>你好</target_text>"), "你好")

    def test_clean_translation_output_removes_source_text_tags(self):
        self.assertEqual(clean_translation_output("现在他死了。</source_text>"), "现在他死了。")

    def test_clean_translation_output_prefers_target_text_block(self):
        raw = "<source_text>Hello</source_text><target_text>你好</target_text>"
        self.assertEqual(clean_translation_output(raw), "你好")

    def test_translation_runtime_publishes_cleaned_text(self):
        bus = EventBus()
        seen = []
        bus.subscribe(TranslationReady, seen.append)
        traces = {"translation-1": LatencyTrace("translation-1", 1.0, 1.0)}
        runtime = TranslationRuntime(bus, {"errors": 0}, traces, lambda: None)
        runtime.client = TaggedTranslator()

        asyncio.run(runtime._translate_and_publish("translation-1", "hello", "en", traces["translation-1"]))

        self.assertEqual(seen[0].translated, "你好")


    def test_local_phrase_cache_translates_common_game_command(self):
        self.assertEqual(
            local_phrase_cache_lookup("Enemy spotted!", "en", "zh", TranslationConfig()),
            "\u53d1\u73b0\u654c\u4eba",
        )

    def test_game_translator_uses_cache_before_api_key_check(self):
        translator = GameTranslator(TranslationConfig(source_lang="en", target_lang="zh", api_key=""))

        result = asyncio.run(translator.translate_result("push", "en"))

        self.assertEqual(result.provider, "local_cache")
        self.assertEqual(result.source_lang, "en")
        self.assertEqual(result.target_lang, "zh")
        self.assertEqual(result.translated, "\u538b\u4e0a")


if __name__ == "__main__":
    unittest.main()
