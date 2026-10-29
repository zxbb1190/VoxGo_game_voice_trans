"""Product labels must never become routing, prompt or persisted language codes."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PyQt5.QtWidgets import QApplication, QStyle
from PyQt5.QtWidgets import QStyleOptionComboBox
from voxgo.config.loader import default_app_config, load_config, save_user_settings
from voxgo.i18n import UI_LANGUAGE_OPTIONS, language_label
from voxgo.languages import LOCAL_DIRECTIONS, ONLINE_DIRECTIONS, SPEECH_LANGUAGES
from voxgo.translation import TranslationConfig
from voxgo.ui.config_models import (
    AudioDeviceConfig, HotkeyConfig, OverlayConfig, RuntimeConfig,
    _beta_language_notice, _speech_language_options,
)
from voxgo.ui.dialogs import FirstRunWizard
from voxgo.ui.overlay_window import GameOverlay
from voxgo.ui.settings_dialog import SettingsDialog


class BetaLanguagePresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def test_metadata_and_bare_names_remain_separate_from_selector_labels(self):
        self.assertEqual({c for c, info in SPEECH_LANGUAGES.items() if info.beta}, {'ja', 'ko', 'ru'})
        for ui, _ in UI_LANGUAGE_OPTIONS:
            for code, label in _speech_language_options(ui):
                self.assertNotIn('Beta', language_label(code, ui))
                self.assertEqual('Beta' in label, SPEECH_LANGUAGES[code].beta)
        self.assertEqual(dict(_speech_language_options('zh-CN'))['ja'], '日语（Beta）')
        self.assertEqual(dict(_speech_language_options('en-US'))['ja'], 'Japanese (Beta)')

    def test_all_20_routes_keep_codes_and_swap_in_each_ui_language(self):
        for ui, _ in UI_LANGUAGE_OPTIONS:
            for provider in ('google', 'openai_compatible'):
                overlay = GameOverlay(translation_config=TranslationConfig(provider=provider),
                                      app_config=RuntimeConfig(language=ui))
                try:
                    for source in SPEECH_LANGUAGES:
                        overlay._source_lang_combo.setCurrentIndex(overlay._source_lang_combo.findData(source))
                        self.assertEqual(overlay._target_lang_combo.count(), 4)
                        for target in SPEECH_LANGUAGES:
                            if source == target:
                                continue
                            with self.subTest(ui=ui, provider=provider, source=source, target=target):
                                overlay._target_lang_combo.setCurrentIndex(overlay._target_lang_combo.findData(target))
                                self.assertEqual((overlay.translation_config.source_lang, overlay.translation_config.target_lang), (source, target))
                                self.assertEqual(overlay._source_lang_combo.currentText(), language_label(source, ui, include_beta=True))
                                self.assertEqual(overlay._target_lang_combo.currentText(), language_label(target, ui, include_beta=True))
                                overlay._swap_language_flow()
                                self.assertEqual((overlay.translation_config.source_lang, overlay.translation_config.target_lang), (target, source))
                                overlay._swap_language_flow()
                    overlay._apply_language_flow('en', 'zh')
                    self.assertTrue(overlay._beta_notice.isHidden())
                    self.assertEqual(overlay._beta_notice.text(), '')
                finally:
                    overlay.close()

    def test_notices_distinguish_source_target_both_and_neither(self):
        for ui, _ in UI_LANGUAGE_OPTIONS:
            notices = [_beta_language_notice(TranslationConfig(source_lang=s, target_lang=t), ui)
                       for s, t in (('ja', 'en'), ('en', 'ko'), ('ru', 'ja'), ('en', 'zh'))]
            self.assertEqual(notices[-1], '')
            self.assertEqual(len(set(notices)), 4)
            if ui in ('ja-JP', 'ko-KR', 'ru-RU'):
                self.assertTrue(all('still being improved' not in n for n in notices))

    def test_beta_and_local_restriction_do_not_replace_each_other(self):
        overlay = GameOverlay(translation_config=TranslationConfig(provider='local', source_lang='ja', target_lang='zh'))
        try:
            self.assertIn('API Key', overlay._language_notice.text())
            self.assertIn('Beta', overlay._beta_notice.text())
            overlay.translation_config.provider = 'google'
            overlay._refresh_language_notice()
            self.assertEqual(overlay._language_notice.text(), '')
            self.assertIn('Beta', overlay._beta_notice.text())
            self.assertEqual(LOCAL_DIRECTIONS, {('en', 'zh'), ('zh', 'en')})
            self.assertEqual(len(ONLINE_DIRECTIONS), 20)
        finally:
            overlay.close()

    def test_settings_wizard_and_overlay_use_same_notice_not_ui_language_beta(self):
        for ui, _ in UI_LANGUAGE_OPTIONS:
            config = TranslationConfig(source_lang='ja', target_lang='ru')
            runtime = RuntimeConfig(language=ui)
            settings = SettingsDialog(OverlayConfig(), HotkeyConfig(), translation_config=copy.deepcopy(config), app_config=runtime)
            wizard = FirstRunWizard(audio_config=AudioDeviceConfig(), translation_config=copy.deepcopy(config), app_config=copy.deepcopy(runtime))
            try:
                expected = _beta_language_notice(config, ui)
                self.assertEqual(settings.beta_language_hint.text(), expected)
                self.assertEqual(wizard.wizard_beta_hint.text(), expected)
                # These selectors choose the interface, not a Beta speech language.
                self.assertTrue(all('Beta' not in wizard.wizard_language_combo.itemText(i)
                                    for i in range(wizard.wizard_language_combo.count())))
                settings.translation_config.source_lang, settings.translation_config.target_lang = 'en', 'zh'
                settings._refresh_translation_provider_ui()
                self.assertTrue(settings.beta_language_hint.isHidden())
                wizard.translation_config.source_lang, wizard.translation_config.target_lang = 'en', 'zh'
                wizard._refresh_wizard_translation_provider_ui()
                self.assertTrue(wizard.wizard_beta_hint.isHidden())
            finally:
                settings.close()
                wizard.close()

    def test_label_does_not_mutate_strategy_or_persisted_config(self):
        for strategy in ('legacy', 'language_aware'):
            for ui, _ in UI_LANGUAGE_OPTIONS:
                with tempfile.TemporaryDirectory() as tmp:
                    config = default_app_config()
                    config.app.language = ui
                    config.translation.source_lang, config.translation.target_lang = 'ja', 'ru'
                    config.whisper.multilingual_asr_strategy = strategy
                    before = copy.deepcopy(config)
                    _speech_language_options(ui)
                    _beta_language_notice(config.translation, ui)
                    self.assertEqual(config, before)
                    save_user_settings(config, runtime_dir=Path(tmp))
                    saved = json.loads((Path(tmp) / 'user_settings.json').read_text('utf-8'))
                    self.assertEqual((saved['translation']['source_lang'], saved['translation']['target_lang']), ('ja', 'ru'))
                    restored = load_config(runtime_dir=Path(tmp))
                    self.assertEqual((restored.translation.source_lang, restored.translation.target_lang), ('ja', 'ru'))
                    # Existing release serializer/loader deliberately retire the
                    # old shared experiment toggle; labels must not revive it.
                    self.assertEqual(saved['whisper']['multilingual_asr_strategy'], 'legacy')
                    self.assertEqual(restored.whisper.multilingual_asr_strategy, 'legacy')

    def test_visible_long_labels_fit_the_toolbar_and_edit_fields(self):
        for ui, _ in UI_LANGUAGE_OPTIONS:
            overlay = GameOverlay(translation_config=TranslationConfig(source_lang='ja', target_lang='ru'),
                                  app_config=RuntimeConfig(language=ui))
            try:
                overlay.resize(360, 220)
                overlay.show()
                self.qt.processEvents()
                for combo in (overlay._source_lang_combo, overlay._target_lang_combo):
                    option = QStyleOptionComboBox()
                    combo.initStyleOption(option)
                    rect = combo.style().subControlRect(QStyle.CC_ComboBox, option, QStyle.SC_ComboBoxEditField, combo)
                    self.assertGreaterEqual(rect.width(), combo.fontMetrics().horizontalAdvance(combo.currentText()))
                    self.assertLessEqual(combo.geometry().right(), overlay._toolbar.width())
                self.assertLessEqual(overlay._quit_button.geometry().right(), overlay._toolbar.width())
            finally:
                overlay.close()


if __name__ == '__main__':
    unittest.main()
