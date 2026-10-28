"""UI localization contracts. No downloads, external API, real settings or audio."""
import ast
import copy
import json
import os
from pathlib import Path
from string import Formatter
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication, QLabel, QMessageBox, QTabWidget
from voxgo.i18n import (
    UI_LANGUAGE_OPTIONS, normalize_ui_language, ui_text, language_label, localize_text, set_qt_ui_language,
)
from voxgo.i18n_messages import MESSAGES
from voxgo.config.loader import load_config, save_user_settings
from voxgo.translation import TranslationConfig
from voxgo.ui.config_models import OverlayConfig, HotkeyConfig, RuntimeConfig, WhisperDeviceConfig, _build_feedback_report, DebugConfig
from voxgo.ui.settings_dialog import SettingsDialog
from voxgo.ui.dialogs import FirstRunWizard, FullscreenHelpDialog, UpdatePromptDialog
from voxgo.ui.overlay_window import GameOverlay, TranslationItem
from voxgo.asr.model_download_notice import ModelDownloadNoticeFormatter
from voxgo.asr.whisper_engine import ModelDownloadProgress
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
NEW = ('ja-JP','ko-KR','ru-RU')


class UiFiveLanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def tearDown(self):
        set_qt_ui_language('zh-CN')
        self.qt.processEvents()

    def test_language_codes_autonyms_and_legacy_settings_roundtrip(self):
        self.assertEqual([c for c,_ in UI_LANGUAGE_OPTIONS],['zh-CN','en-US',*NEW])
        for alias,code in (('ja_JP','ja-JP'),('日本語','ja-JP'),('한국어','ko-KR'),('ru','ru-RU'),('Русский','ru-RU'),('zh_CN','zh-CN'),('English','en-US')):
            self.assertEqual(normalize_ui_language(alias),code)
        for language in ('zh-CN','en-US',*NEW):
            with tempfile.TemporaryDirectory() as tmp:
                app=load_config(runtime_dir=Path(tmp))
                before=copy.deepcopy(app.translation.__dict__)
                # The existing settings loader canonicalizes an absent cache.
                before['local_phrase_cache'] = before['local_phrase_cache'] or {}
                app.app.language=language
                save_user_settings(app,runtime_dir=Path(tmp))
                loaded=load_config(runtime_dir=Path(tmp))
                self.assertEqual(loaded.app.language,language)
                self.assertEqual(loaded.translation.__dict__,before)

    def test_catalog_preserves_every_format_field_and_translates_all_new_locales(self):
        fields=lambda s: sorted(f for _,f,_,_ in Formatter().parse(s) if f is not None)
        for english,values in MESSAGES.items():
            self.assertEqual(fields(english),fields(values[0]))
            for language,translated in zip(NEW,values[1:]):
                with self.subTest(key=english,locale=language):
                    self.assertTrue(translated.strip())
                    self.assertEqual(fields(english),fields(translated))
                    self.assertNotIn('当前语言质量',translated)

    def test_ui_text_call_sites_have_no_untranslated_catalog_keys(self):
        def texts(node):
            if isinstance(node,ast.Constant) and isinstance(node.value,str):return [node.value]
            if isinstance(node,ast.IfExp):return texts(node.body)+texts(node.orelse)
            if isinstance(node,ast.JoinedStr):
                parts=[];n=0
                for value in node.values:
                    if isinstance(value,ast.Constant):parts.append(value.value.replace('{','{{').replace('}','}}'))
                    else:parts.append('{'+str(n)+'}');n+=1
                return [''.join(parts)]
            return []
        missing=[]
        for path in (ROOT/'voxgo').rglob('*.py'):
            if path.name.startswith('i18n'):continue
            for node in ast.walk(ast.parse(path.read_text('utf-8-sig'))):
                if not isinstance(node,ast.Call):continue
                name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else ''
                if name not in ('_tr','ui_text','tr_text'):continue
                args=node.args[1:] if name in ('_tr','ui_text') else node.args
                if len(args)!=2:continue
                for english in texts(args[1]):
                    if english.strip() and english not in MESSAGES:missing.append((str(path.relative_to(ROOT)),node.lineno,english))
        self.assertEqual(missing,[])

    def test_dynamic_notices_keep_data_and_real_subtitles_verbatim(self):
        raw='[翻译错误 503] request ID abc {literal}; https://localhost/test'
        for language in NEW:
            notice=localize_text(language,raw)
            self.assertNotIn('翻译错误',notice)
            self.assertIn('503',notice)
            self.assertIn('request ID abc {literal}; https://localhost/test',notice)
            self.assertNotIn('Offline translation model is not ready',localize_text(language,
                '[翻译失败] Offline translation model is not ready; download it in Settings first'))
            self.assertNotEqual(notice,raw)
            overlay=GameOverlay(app_config=RuntimeConfig(language=language))
            self.addCleanup(overlay.close)
            normal=TranslationItem('source','Test failed: player callsign',10,copyable=True)
            html=overlay._format_item(normal,1.)
            self.assertIn('Test failed: player callsign',html)
            self.assertEqual(normal.translated,'Test failed: player callsign')
            error=TranslationItem('original speech','[翻译不完整] 服务商达到输出上限，未显示截断译文。请检查 max_tokens 设置。',10)
            self.assertNotIn('翻译不完整',overlay._format_item(error,1.))
            self.assertFalse(error.copyable)
            self.assertIn('翻译不完整',error.translated)  # presentation only
            overlay.close()

    def test_settings_and_wizard_show_five_languages_without_consent_or_route_changes(self):
        for language in NEW:
            with self.subTest(language=language):
                runtime=RuntimeConfig(language=language,telemetry_consent='denied')
                translation=TranslationConfig(source_lang='ja',target_lang='ru')
                whisper=WhisperDeviceConfig(multilingual_asr_strategy='legacy')
                dialog=SettingsDialog(OverlayConfig(),HotkeyConfig(),translation_config=translation,app_config=runtime,whisper_config=whisper)
                self.addCleanup(dialog.close)
                self.assertEqual(dialog.ui_language_combo.count(),5)
                self.assertEqual(dialog.windowTitle(),ui_text(language,'浮窗设置','Overlay Settings'))
                self.assertEqual(dialog.provider_combo.currentText(),localize_text(language,'OpenAI-compatible'))
                self.assertEqual(dialog.local_model_panel.models.currentText(),localize_text(language,'OPUS-MT English ↔ Chinese (CPU)'))
                self.assertNotEqual(dialog.findChild(QTabWidget).tabText(0),'Appearance')
                self.assertEqual(dialog.privacy_title.text(),ui_text(language,'愿意帮助 VoxGo 改进体验','Help improve VoxGo'))
                self.assertFalse(dialog.telemetry_consent_check.isChecked())
                self.assertNotIn('Optional Full',dialog.privacy_notice.toolTip())
                self.assertEqual(translation.source_lang,'ja');self.assertEqual(translation.target_lang,'ru')
                self.assertEqual(whisper.multilingual_asr_strategy,'legacy')
                self.assertEqual(runtime.telemetry_consent,'denied')
                dialog.close()
                wizard=FirstRunWizard(None,translation,app_config=runtime,whisper_config=whisper)
                self.addCleanup(wizard.close)
                for code in NEW:
                    wizard.wizard_language_combo.setCurrentIndex(wizard.wizard_language_combo.findData(code))
                    self.assertEqual(wizard.wizard_language_title.text(),ui_text(code,'选择界面语言','Choose Your Interface Language'))
                    self.assertEqual((translation.source_lang,translation.target_lang),('ja','ru'))
                    self.assertEqual(runtime.telemetry_consent,'denied')
                wizard.close()

    def test_qt_buttons_and_unowned_text_never_become_blank(self):
        original_family=self.qt.font().family()
        for language in NEW:
            set_qt_ui_language(language)
            box=QMessageBox(QMessageBox.Question,'VoxGo','fixture',QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
            for flag,key in ((QMessageBox.Yes,'&Yes'),(QMessageBox.No,'&No'),(QMessageBox.Cancel,'Cancel')):
                self.assertEqual(box.button(flag).text(),localize_text(language,key))
            self.assertEqual(QCoreApplication.translate('unowned','do not blank me'),'do not blank me')
            box.close()
        set_qt_ui_language('en-US')
        self.assertEqual(self.qt.font().family(),original_family)

    def test_settings_picker_reopens_in_new_language_preserving_tab_fields_and_direction(self):
        current=['zh-CN']
        def changed(*configs):
            app_config=configs[5]
            if app_config.language != current[0]:
                current[0]=app_config.language
                overlay.app_config=app_config
                overlay.refresh_language()
        translation=TranslationConfig(source_lang='ja',target_lang='ru',model='ui-fixture-only',api_key='')
        overlay=GameOverlay(translation_config=translation,on_settings_changed=changed)
        self.addCleanup(overlay.close)
        overlay.show_settings();self.qt.processEvents()
        for language in (*NEW,'en-US','zh-CN'):
            dialog=overlay._settings_dialog
            dialog.findChild(QTabWidget).setCurrentIndex(1)
            dialog.ui_language_combo.setCurrentIndex(dialog.ui_language_combo.findData(language))
            self.qt.processEvents();self.qt.processEvents()
            fresh=overlay._settings_dialog
            self.assertIsNot(fresh,dialog)
            self.assertEqual(fresh.windowTitle(),ui_text(language,'浮窗设置','Overlay Settings'))
            self.assertEqual(fresh.findChild(QTabWidget).currentIndex(),1)
            self.assertEqual(fresh.model_input.text(),'ui-fixture-only')
            self.assertEqual((translation.source_lang,translation.target_lang),('ja','ru'))
            self.assertEqual(fresh.api_key_input.text(),'')
        overlay._settings_dialog.close()
        overlay.close()

    def test_open_update_dialog_relocalizes_without_restarting_installation_or_rewriting_notes(self):
        from voxgo.update.checker import UpdateInfo
        update=UpdateInfo(latest='9.0.0',notes_en=['External release note: keep exactly.'])
        dialog=UpdatePromptDialog(update,'0.5.3',lambda version:None,ui_language='en-US')
        self.addCleanup(dialog.close)
        dialog.install_panel.busy=True
        dialog.install_panel.status.setText('Downloading: 50% · 1 MB/s · elapsed 2s · about 2s left')
        for language in NEW:
            dialog.refresh_language(language)
            self.assertEqual(dialog.windowTitle(),ui_text(language,'发现新版本','Update Available'))
            self.assertIn('External release note: keep exactly.',dialog.message_label.text())
            self.assertTrue(dialog.install_panel.busy)
            self.assertNotIn('Downloading:',dialog.install_panel.status.text())
        dialog.install_panel.busy=False
        dialog.close()

    def test_model_progress_feedback_and_help_are_localized_with_metadata_kept(self):
        for language in NEW:
            cfg=SimpleNamespace(app=SimpleNamespace(language=language),whisper=SimpleNamespace(model_size='base',model_download_source='modelscope'))
            formatter=ModelDownloadNoticeFormatter(lambda:cfg)
            progress=ModelDownloadProgress(status='checking',model_name='base',repo_id='repo/base',source='ModelScope 国内源')
            message=formatter.format(progress)
            self.assertIn('repo/base',message);self.assertNotIn('正在检查',message);self.assertNotIn('Checking the local cache',message)
            self.assertNotIn('Model:',message);self.assertNotIn('Repository:',message)
            feedback=_build_feedback_report(TranslationConfig(),WhisperDeviceConfig(),DebugConfig(),'0.5.3','unused',{},'',language)
            self.assertNotIn('### Basic Info',feedback)
            help=FullscreenHelpDialog(HotkeyConfig(),language)
            self.addCleanup(help.close)
            self.assertNotIn('If the overlay does not appear',' '.join(x.text() for x in help.findChildren(QLabel)))
            help.close()
