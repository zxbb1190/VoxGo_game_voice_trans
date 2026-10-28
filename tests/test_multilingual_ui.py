"""Offscreen UI routing checks; no provider requests or quality claims."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from voxgo.i18n import UI_LANGUAGE_EN, UI_LANGUAGE_ZH, language_label
from voxgo.translation import TranslationConfig
from voxgo.ui.config_models import HotkeyConfig, OverlayConfig, RuntimeConfig, WhisperDeviceConfig
from voxgo.ui.overlay_window import GameOverlay
from voxgo.ui.settings_dialog import SettingsDialog
from voxgo.ui.widgets import TranslationTestRunner
from voxgo.languages import ONLINE_DIRECTIONS


class MultilingualUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt_app = QApplication.instance() or QApplication([])

    def make_overlay(self, **kwargs):
        widget = GameOverlay(**kwargs)
        self.addCleanup(widget.close)
        return widget

    def test_five_source_choices_legal_targets_and_change_callback(self):
        changed = []
        config = TranslationConfig(provider="google")
        overlay = self.make_overlay(translation_config=config,
            on_settings_changed=lambda *args: changed.append((args[3].source_lang, args[3].target_lang)))
        self.assertEqual([overlay._source_lang_combo.itemData(i) for i in range(5)], ["en", "zh", "ja", "ko", "ru"])
        for source, target in (("ja", "zh"), ("ko", "zh"), ("ru", "zh"), ("zh", "en"), ("en", "zh")):
            overlay._source_lang_combo.setCurrentIndex(overlay._source_lang_combo.findData(source))
            self.assertEqual((config.source_lang, config.target_lang), (source, target))
            self.assertEqual(overlay._target_lang_combo.count(), 4)
            self.assertEqual(overlay._target_lang_combo.currentData(), target)
            self.assertEqual(changed[-1], (source, target))
        self.assertEqual(len(changed), 5)

    def test_english_chinese_swap_remains_bidirectional(self):
        overlay = self.make_overlay()
        overlay._swap_lang_button.click()
        self.assertEqual((overlay.translation_config.source_lang, overlay.translation_config.target_lang), ("zh", "en"))
        overlay._swap_lang_button.click()
        self.assertEqual((overlay.translation_config.source_lang, overlay.translation_config.target_lang), ("en", "zh"))

    def test_every_online_pair_has_exact_target_choices_and_reversible_swap(self):
        for provider in ('google', 'openai_compatible'):
            for source, target in sorted(ONLINE_DIRECTIONS):
                with self.subTest(provider=provider,source=source,target=target):
                    config = TranslationConfig(provider=provider,source_lang=source,target_lang=target)
                    overlay = self.make_overlay(translation_config=config)
                    targets = {overlay._target_lang_combo.itemData(i) for i in range(overlay._target_lang_combo.count())}
                    self.assertEqual(targets,{t for s,t in ONLINE_DIRECTIONS if s==source})
                    self.assertTrue(overlay._swap_lang_button.isEnabled())
                    overlay._swap_lang_button.click()
                    self.assertEqual((config.source_lang,config.target_lang,config.provider),(target,source,provider))
                    overlay.close()

    def test_speech_strategy_checkbox_preserves_legacy_preference_without_network(self):
        for source in ('en','zh','ja','ko','ru'):
            whisper = WhisperDeviceConfig(multilingual_asr_strategy='legacy')
            dialog = SettingsDialog(OverlayConfig(),HotkeyConfig(),
                translation_config=TranslationConfig(source_lang=source,target_lang='en' if source=='zh' else 'zh'),
                whisper_config=whisper)
            self.addCleanup(dialog.close)
            self.assertEqual(dialog.multilingual_strategy_check.isHidden(),source in {'en','zh'})
            self.assertFalse(dialog.multilingual_strategy_check.isChecked())
            dialog._collect_values()
            self.assertEqual(whisper.multilingual_asr_strategy,'legacy')
            if source in {'ja','ko','ru'}:
                dialog.multilingual_strategy_check.setChecked(True)
                self.assertEqual(whisper.multilingual_asr_strategy,'language_aware')
            dialog.close()

    def test_chinese_japanese_is_explicit_online_choice_with_reverse_swap(self):
        config = TranslationConfig(provider="google", source_lang="zh", target_lang="en")
        overlay = self.make_overlay(translation_config=config, app_config=RuntimeConfig(language=UI_LANGUAGE_EN))
        overlay._target_lang_combo.setCurrentIndex(overlay._target_lang_combo.findData("ja"))
        self.assertEqual((config.source_lang, config.target_lang, config.provider), ("zh", "ja", "google"))
        self.assertTrue(overlay._swap_lang_button.isEnabled())
        self.assertIn("your own API key", overlay._language_notice.text())
        overlay._toggle_lock()
        overlay._toggle_lock()
        self.assertTrue(overlay._swap_lang_button.isEnabled())
        overlay._swap_lang_button.click()
        self.assertEqual((config.source_lang, config.target_lang, config.provider), ("ja", "zh", "google"))

    def test_new_languages_cannot_swap_and_do_not_switch_local_provider(self):
        for source in ("ja", "ko", "ru"):
            with self.subTest(source=source):
                config = TranslationConfig(provider="local", source_lang=source, target_lang="zh")
                overlay = self.make_overlay(translation_config=config, app_config=RuntimeConfig(language=UI_LANGUAGE_EN))
                self.assertFalse(overlay._swap_lang_button.isEnabled())
                self.assertIn("unavailable", overlay._swap_lang_button.toolTip())
                overlay._swap_language_flow()
                self.assertEqual((config.provider, config.source_lang, config.target_lang), ("local", source, "zh"))
                self.assertIn("Offline supports English", overlay._language_notice.text())
                self.assertFalse(overlay._language_notice.isHidden())

    def test_explicit_invalid_direction_is_preserved_and_explained(self):
        config = TranslationConfig(provider="google", source_lang="ja", target_lang="fr")
        overlay = self.make_overlay(translation_config=config, app_config=RuntimeConfig(language=UI_LANGUAGE_EN))
        self.assertEqual(config.target_lang, "fr")
        self.assertEqual(overlay._target_lang_combo.currentData(), "fr")
        self.assertIn("unsupported", overlay._target_lang_combo.currentText())
        self.assertIn("Unsupported direction", overlay._language_notice.text())

    def test_bilingual_language_names_and_online_provider_notice(self):
        overlay = self.make_overlay(translation_config=TranslationConfig(provider="google", source_lang="ko", target_lang="zh"))
        self.assertEqual(language_label("ko", UI_LANGUAGE_ZH), "韩语")
        self.assertEqual(overlay._language_notice.text(), "日/韩/俄相关方向仅支持在线直译，需自配 API Key。")
        overlay.app_config.language = UI_LANGUAGE_EN
        overlay.refresh_language()
        self.assertEqual(overlay._source_lang_combo.currentText(), "Korean")
        self.assertEqual(overlay._language_notice.text(), "Directions involving Japanese/Korean/Russian require direct online translation with your own API key.")
        self.assertTrue(overlay._swap_lang_button.isEnabled())
        self.assertIn("Swap recognition", overlay._swap_lang_button.toolTip())

    def test_settings_block_incompatible_local_test_preserve_english_preference(self):
        config = TranslationConfig(provider="local", source_lang="ja", target_lang="zh")
        whisper = WhisperDeviceConfig(pure_english_environment=True, enable_english_model=True)
        dialog = SettingsDialog(OverlayConfig(), HotkeyConfig(), translation_config=config,
            whisper_config=whisper, app_config=RuntimeConfig(language=UI_LANGUAGE_EN))
        self.addCleanup(dialog.close)
        self.assertFalse(dialog.translation_test_button.isEnabled())
        self.assertFalse(dialog.pure_english_environment_check.isEnabled())
        self.assertTrue(dialog.pure_english_environment_check.isChecked())
        self.assertIn("preserved and ignored", dialog.pure_english_environment_check.toolTip())
        with patch("voxgo.ui.settings_dialog.TranslationTestRunner") as runner:
            dialog._test_translation()
            runner.assert_not_called()
        self.assertEqual(config.provider, "local")
        self.assertTrue(whisper.pure_english_environment)
        dialog.provider_combo.setCurrentIndex(dialog.provider_combo.findData("google"))
        self.assertTrue(dialog.translation_test_button.isEnabled())
        self.assertIn("your own API key", dialog.provider_hint.text())

    def test_connectivity_probe_uses_actual_source_once_and_only_on_run(self):
        calls = []
        class FakeTranslator:
            def __init__(self, config):
                calls.append(("config", config.source_lang, config.target_lang))
            async def translate(self, text, source):
                calls.append(("request", text, source))
                return "测试输出"
            async def close(self):
                pass
        for source, marker in (("ja", "こんにちは"), ("ko", "안녕하세요"), ("ru", "Здравствуйте"), ("zh", "请在")):
            with self.subTest(source=source), patch("voxgo.ui.widgets.GameTranslator", FakeTranslator):
                calls.clear()
                results = []
                target = "en" if source == "zh" else "zh"
                runner = TranslationTestRunner(TranslationConfig(provider="google", source_lang=source, target_lang=target),
                    lambda ok, message: results.append((ok, message)), UI_LANGUAGE_EN)
                self.assertEqual(calls, [])
                runner._run()
                self.assertEqual(calls[0], ("config", source, target))
                self.assertEqual(len(calls), 2)
                self.assertEqual(calls[1][2], source)
                self.assertTrue(calls[1][1].startswith(marker))
                self.assertTrue(results[0][0])
                self.assertIn("Test succeeded", results[0][1])

    def test_incompatible_runner_never_constructs_provider(self):
        results = []
        runner = TranslationTestRunner(TranslationConfig(provider="local", source_lang="ru", target_lang="zh"),
            lambda ok, message: results.append((ok, message)))
        with patch("voxgo.ui.widgets.GameTranslator") as translator:
            runner._run()
            translator.assert_not_called()
        self.assertFalse(results[0][0])


if __name__ == "__main__":
    unittest.main()
