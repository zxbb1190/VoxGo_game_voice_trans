"""Real local HTTP contracts; responses are fixtures, never quality evidence."""
import asyncio
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import aiohttp
from aiohttp import web

from voxgo.languages import ONLINE_DIRECTIONS, SPEECH_LANGUAGE_CODES, normalize_language_code, normalize_language_flow, whisper_model_error
from voxgo.config.loader import default_app_config, sync_language_flow, apply_language_runtime_policy, serialize_user_settings
from voxgo.translation import GameTranslator, TranslationConfig
from voxgo.translation.base import TranslationRequest, detect_language, should_skip_translation_for_language
from voxgo.translation.openai_compatible import OpenAICompatibleProvider
from voxgo.translation.google import GoogleCloudProvider
from voxgo.translation.prompt import SYSTEM_PROMPT, translation_system_prompt
from voxgo.asr.whisper_engine import WhisperConfig, SpeechRecognizer, TranscriptionResult, should_drop_transcription_result, WhisperLanguageCapabilityError


class MultilingualCapabilitiesTest(unittest.TestCase):
    def test_local_remains_only_two_directions_with_no_online_switch(self):
        from voxgo.languages import translation_direction_error,LOCAL_DIRECTIONS
        unsupported=ONLINE_DIRECTIONS-LOCAL_DIRECTIONS
        self.assertEqual(len(unsupported),18)
        for source,target in unsupported:
            self.assertIn('Offline supports English',translation_direction_error('local',source,target))

    def test_all_twenty_distinct_directions_and_mandarin_alias(self):
        self.assertEqual(ONLINE_DIRECTIONS, frozenset((s,t) for s in SPEECH_LANGUAGE_CODES for t in SPEECH_LANGUAGE_CODES if s!=t))
        self.assertEqual(len(ONLINE_DIRECTIONS),20)
        for code in ('zh','zh_CN','zh-CN'):
            self.assertEqual(normalize_language_code(code),'zh')
        self.assertEqual(normalize_language_flow('zh_CN','ru'),('zh','ru'))

    def test_config_preserves_pair_settings_and_formal_tuning(self):
        for source, target in ONLINE_DIRECTIONS:
            with self.subTest(source=source, target=target):
                config = default_app_config()
                config.translation.source_lang, config.translation.target_lang = source, target
                config.whisper.pure_english_environment = True
                config.whisper.enable_english_model = True
                before = copy.deepcopy(config.whisper)
                self.assertEqual(sync_language_flow(config), (source, target))
                apply_language_runtime_policy(config)
                self.assertEqual(config.whisper.source_language, source)
                if source in {"ja", "ko", "ru"}:
                    self.assertEqual(config.whisper.language, "auto")
                    self.assertFalse(config.whisper.active_model_size.endswith(".en"))
                for key in ("initial_prompt", "prompt_profile", "temperature", "no_speech_threshold", "log_prob_threshold", "compression_ratio_threshold"):
                    self.assertEqual(getattr(config.whisper, key), getattr(before, key))
                self.assertNotIn("source_language", serialize_user_settings(config)["whisper"])

    def test_invalid_settings_are_not_reinterpreted_as_english(self):
        self.assertEqual(normalize_language_flow("xx", "ja"), ("xx", "ja"))
        self.assertEqual(normalize_language_flow("ja", "en"), ("ja", "en"))
        self.assertEqual(detect_language("bonjour", "fr", "fr"), "fr")
        self.assertEqual(detect_language("敵が右にいる", "", ""), "ja")
        self.assertEqual(detect_language("오른쪽 두 명", "", ""), "ko")
        self.assertEqual(detect_language("Двое справа", "", ""), "ru")

    def test_language_gate_handles_multilingual_scripts_and_ambiguity(self):
        for source, text in (("ja", "右側の敵を狙え"), ("ko", "오른쪽 두 명"), ("ru", "Двое справа")):
            self.assertEqual(should_skip_translation_for_language(text, source, source, .99), "")
            self.assertIn("language_mismatch", should_skip_translation_for_language(text, source, "fr", .99))
        self.assertEqual(should_skip_translation_for_language("敵発見", "ja", "", 0), "")
        self.assertEqual(should_skip_translation_for_language("B", "ko", "en", .5), "")
        self.assertIn("text_script_mismatch", should_skip_translation_for_language("뒤에 적", "en", "en", 1))
        self.assertEqual(should_skip_translation_for_language("让「アリス」守住右边的门。", "zh", "zh", .99), "")
        self.assertEqual(should_skip_translation_for_language("Use the オペレーター after round three.", "en", "en", .99), "")

    def test_short_callouts_are_not_dropped_for_alphabet(self):
        for lang, text in (("ja", "右だ"), ("ko", "뒤에"), ("ru", "нет")):
            result = TranscriptionResult(text=text, language=lang, language_probability=.99)
            self.assertEqual(should_drop_transcription_result(result, lang, config=WhisperConfig()), "")

    def test_english_only_models_are_rejected_before_loading(self):
        for source in ("ja", "ko", "ru", "zh"):
            config = WhisperConfig(model_size="base.en", source_language=source)
            with patch("voxgo.asr.whisper_engine.WhisperModel") as load:
                with self.assertRaisesRegex(ValueError, "multilingual"):
                    SpeechRecognizer(config).initialize()
                load.assert_not_called()
        self.assertTrue(whisper_model_error("Systran/faster-whisper-small.en", "ja"))
        recognizer = SpeechRecognizer(WhisperConfig(source_language="ko"))
        recognizer._model = SimpleNamespace(model=SimpleNamespace(is_multilingual=False))
        with self.assertRaisesRegex(ValueError, "multilingual"):
            recognizer._validate_native_model_language("ko")

    def test_legacy_prompt_exact_and_new_prompt_direct(self):
        self.assertEqual(translation_system_prompt("en", "zh"), SYSTEM_PROMPT)
        self.assertEqual(translation_system_prompt("zh", "en"), SYSTEM_PROMPT)
        for pair in ONLINE_DIRECTIONS - {("en", "zh"), ("zh", "en")}:
            prompt = translation_system_prompt(*pair)
            self.assertIn("不要经英语或其他语言中转", prompt)
            self.assertNotIn("如果原文是英文", prompt)

    def test_renamed_english_model_preserves_actionable_error_without_device_retry(self):
        recognizer = SpeechRecognizer(WhisperConfig(model_size="renamed-local", source_language="ja"))
        model = SimpleNamespace(model=SimpleNamespace(is_multilingual=False))
        with patch.object(recognizer, "_ensure_model_downloaded"), patch.object(recognizer, "_model_load_candidates", return_value=[("cpu", "int8"), ("cpu", "float32")]), patch("voxgo.asr.whisper_engine.WhisperModel", return_value=model) as load:
            with self.assertRaisesRegex(WhisperLanguageCapabilityError, "multilingual Whisper"):
                recognizer.initialize()
            self.assertEqual(load.call_count, 1)


class MultilingualHTTPTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.requests = []
        async def chat(request):
            body = await request.json()
            self.requests.append(body)
            return web.json_response({"choices": [{"message": {"content": "协议夹具译文"}}]})
        async def google(request):
            self.requests.append(dict(request.query))
            return web.json_response({"data": {"translations": [{"translatedText": "协议夹具译文"}]}})
        app = web.Application()
        app.router.add_post("/chat/completions", chat)
        app.router.add_post("/google", google)
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "127.0.0.1", 0)
        await self.site.start()
        self.url = "http://127.0.0.1:" + str(self.site._server.sockets[0].getsockname()[1])

    async def asyncTearDown(self):
        await self.runner.cleanup()

    async def test_direct_source_target_over_http_each_provider(self):
        for provider in ("google", "openai_compatible"):
            for source, target in sorted(ONLINE_DIRECTIONS):
                config = TranslationConfig(provider=provider, source_lang=source, target_lang=target,
                    endpoint=self.url, api_key="fixture", enable_local_phrase_cache=False)
                client = GameTranslator(config)
                with patch("voxgo.translation.google.GOOGLE_TRANSLATE_ENDPOINT", self.url + "/google"):
                    try:
                        result = await client.translate_result("independent fixture", source)
                    finally:
                        await client.close()
                self.assertEqual((result.source_lang, result.target_lang), (source, target))
                body = self.requests[-1]
                if provider == "google":
                    self.assertEqual(body["source"], "zh-CN" if source == "zh" else source)
                    self.assertEqual(body["target"], "zh-CN" if target == "zh" else target)
                    self.assertEqual(body["q"], "independent fixture")
                else:
                    self.assertEqual(len(body["messages"]), 2)
                    self.assertEqual(body["messages"][0]["content"], translation_system_prompt(source, target))
                self.assertEqual(len(self.requests), (len(ONLINE_DIRECTIONS) if provider == "openai_compatible" else 0) + sorted(ONLINE_DIRECTIONS).index((source,target)) + 1)

    async def test_capability_guard_precedes_cache_and_network(self):
        for provider, source, target in (("local", "ja", "zh"), ("google", "ru", "ru"), ("openai_compatible", "fr", "zh")):
            config = TranslationConfig(provider=provider, source_lang=source, target_lang=target,
                endpoint=self.url, api_key="fixture", local_phrase_cache={f"{source}:{target}": {"hello": "bad override"}})
            client = GameTranslator(config)
            try:
                result = await client.translate_result("hello", source)
                self.assertTrue(result.translated.startswith("[未翻译]"))
                self.assertIsNone(client._session)
                snapshot = copy.deepcopy(config)
                result = await client.translate_result_with_config("hello", source, snapshot)
                self.assertTrue(result.translated.startswith("[未翻译]"))
            finally:
                await client.close()
        self.assertEqual(self.requests, [])
        async with aiohttp.ClientSession() as session:
            for provider in (GoogleCloudProvider(TranslationConfig()), OpenAICompatibleProvider(TranslationConfig())):
                result = await provider.translate(TranslationRequest("x", "ja", "ja"), session)
                self.assertTrue(result.translated.startswith("[未翻译]"))

    async def test_context_is_partitioned_and_clear_drops_all_pairs(self):
        config = TranslationConfig(endpoint=self.url, context_messages=2)
        provider = OpenAICompatibleProvider(config)
        async with aiohttp.ClientSession() as session:
            await provider.translate(TranslationRequest("初めまして", "ja", "zh"), session)
            await provider.translate(TranslationRequest("안녕하세요", "ko", "zh"), session)
            self.assertEqual(len(self.requests[-1]["messages"]), 2)
            await provider.translate(TranslationRequest("戻って", "ja", "zh"), session)
            self.assertEqual(len(self.requests[-1]["messages"]), 4)
            provider.clear_context()
            await provider.translate(TranslationRequest("下がれ", "ja", "zh"), session)
            self.assertEqual(len(self.requests[-1]["messages"]), 2)
