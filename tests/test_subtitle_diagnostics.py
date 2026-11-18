"""Settings-only diagnostics, help, and an explicit persistent community opt-out."""
import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QTabWidget

from voxgo.app import VoxGoApp
from voxgo.config.loader import default_app_config, load_user_settings, save_user_settings, serialize_user_settings
from voxgo.i18n import ui_text
from voxgo.runtime.first_success import LiveCheck
from voxgo.runtime.subtitle_diagnostics import collect_diagnostics
from voxgo.ui.config_models import _copy_runtime_config
from voxgo.ui.detection_help import HELP_SECTIONS
from voxgo.ui.download_panels import LocalModelRequiredDialog
from voxgo.ui.live_check import FirstSuccessController
from voxgo.ui.overlay_window import GameOverlay
from voxgo.update.installer import PRESERVE_PATHS


class DiagnosticRulesTests(unittest.TestCase):
    def diagnose(self, check=None, **changes):
        options = dict(setup_complete=True, paused=False, model_state="ready", capture_available=True,
                       audio_error="", overlay_visible=True)
        options.update(changes)
        return collect_diagnostics(check or LiveCheck(1, started_at=0), **options)

    def test_silence_and_pending_stages_are_not_reported_as_proven_faults(self):
        check = LiveCheck(1, started_at=0, models=True)
        for expected, advance in (
                ("audio_waiting", lambda: setattr(check, "audio", True)),
                ("speech_waiting", lambda: check.transcript("a", 1, 1)),
                ("translation_waiting", lambda: check.translation("a", 1)),
                ("display_waiting", lambda: check.present("a"))):
            issues = self.diagnose(check)
            self.assertEqual([issue.code for issue in issues], [expected])
            self.assertFalse(issues[0].confirmed)
            advance()
        self.assertTrue(check.complete)
        self.assertEqual(self.diagnose(check), [])

    def test_multiple_real_problems_remain_visible_together(self):
        check = LiveCheck(1, error="HTTP 401")
        issues = self.diagnose(check, setup_complete=False, paused=True, model_state="error",
                              capture_available=False, audio_error="target exited", overlay_visible=False)
        self.assertEqual({issue.code for issue in issues},
            {"setup", "paused", "model_error", "capture_error", "translation_error", "overlay_hidden"})
        self.assertTrue(all(issue.confirmed for issue in issues))
        self.assertEqual(next(issue.detail for issue in issues if issue.code == "translation_error"), "HTTP 401")

    def test_missing_local_model_and_loading_are_different_states(self):
        self.assertEqual(self.diagnose(model_state="missing_translation")[0].code, "local_model_missing")
        loading = self.diagnose(model_state="preparing")
        self.assertEqual([item.code for item in loading], ["model_waiting"])
        self.assertFalse(loading[0].confirmed)

    def test_no_capture_and_hidden_overlay_are_detected_without_audio_evidence(self):
        self.assertEqual({issue.code for issue in self.diagnose(capture_available=False, overlay_visible=False)},
                         {"capture_missing", "overlay_hidden"})

    def test_help_and_issue_messages_cover_all_five_languages(self):
        issues = self.diagnose(LiveCheck(1, error="401"), setup_complete=False, paused=True,
                              model_state="error", capture_available=False, audio_error="lost", overlay_visible=False)
        for language in ("zh-CN", "ja-JP", "ko-KR", "ru-RU"):
            for issue in issues:
                self.assertNotEqual(ui_text(language, issue.zh, issue.en), issue.en)
            for zh_title, en_title, zh_text, en_text in HELP_SECTIONS:
                self.assertNotEqual(ui_text(language, zh_title, en_title), en_title)
                self.assertNotEqual(ui_text(language, zh_text, en_text), en_text)


class DiagnosticsQtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self):
        self.config = default_app_config()
        self.config.app.language = "zh-CN"
        self.config.app.setup_completed = True
        self.overlay = GameOverlay(config=self.config.overlay, app_config=self.config.app,
            translation_config=self.config.translation, audio_config=self.config.audio)
        self.app = SimpleNamespace(config=self.config, _overlay=self.overlay, _language_flow_revision=1,
            _stopping=False, _paused=False, _backend_ready=True, _save_user_settings=Mock(),
            _ui_language=lambda: self.config.app.language, _toggle_translation=Mock(),
            _request_model_recovery=Mock(), _start_backend_after_setup=Mock(), _restart_audio_capture=Mock(),
            _audio=SimpleNamespace(capture=SimpleNamespace(selected_device={"name": "Fixture"},
                last_level_dbfs=-120, last_level_at=0), last_error=""))
        self.controller = FirstSuccessController(self.app)
        self.overlay.show()
        self.qt.processEvents()

    def tearDown(self):
        self.controller.stop()
        if self.overlay._settings_dialog:
            self.overlay._settings_dialog.close()
        self.overlay.close()
        self.overlay.deleteLater()
        self.qt.processEvents()

    def translation(self, item="a", text="译文", error="", revision=1):
        self.controller.transcript_received.emit(item, revision, time.time())
        self.controller.translation_received.emit(item, revision, text, error)
        self.qt.processEvents()

    def test_startup_and_setup_completion_never_open_diagnostics_or_a_hint(self):
        for ready in (False, True):
            self.app._backend_ready = ready
            self.controller.poll()
            self.assertIsNone(self.controller.dialog)
            self.assertFalse(hasattr(self.controller, "guidance"))
            self.assertFalse(hasattr(self.overlay, "_live_check_button"))
        owner = VoxGoApp.__new__(VoxGoApp)
        owner.config = self.config
        owner._first_success = self.controller
        owner._ui_language = self.app._ui_language
        for name in ("_sync_language_flow", "_sync_whisper_vad_limit", "_refresh_cached_settings",
                     "_notify_user", "_start_backend_thread", "_save_user_settings"):
            setattr(owner, name, Mock())
        owner._start_backend_after_setup()
        self.assertIsNone(self.controller.dialog)

    def test_settings_help_button_is_the_working_entry_and_help_opens(self):
        self.overlay._open_settings()
        settings = self.overlay._settings_dialog
        tabs = settings.findChild(QTabWidget)
        index = next(i for i in range(tabs.count()) if tabs.tabText(i) == "帮助与反馈")
        tabs.setCurrentIndex(index)
        self.assertTrue(settings.live_check_button.isVisible())
        self.assertEqual(settings.live_check_button.text(), "自动检测")
        settings.live_check_button.click()
        dialog = self.controller.dialog
        self.assertTrue(dialog.isVisible())
        self.assertEqual(dialog.windowTitle(), "自动检测")
        self.assertFalse(dialog.windowFlags() & Qt.WindowContextHelpButtonHint)
        dialog.help_button.click()
        self.assertTrue(dialog.help_dialog.isVisible())
        text = "\n".join(label.text() for label in dialog.help_dialog.findChildren(QLabel))
        for section in ("模型", "收音", "语音识别", "翻译", "字幕显示", "没有语音不代表故障"):
            self.assertIn(section, text)
        dialog.close()
        self.assertFalse(dialog.help_dialog.isVisible())
        self.assertFalse(self.config.app.subtitle_check_completed)

    def test_missing_model_prompt_has_no_inert_titlebar_help(self):
        prompt = LocalModelRequiredDialog("zh-CN")
        self.assertFalse(prompt.windowFlags() & Qt.WindowContextHelpButtonHint)
        prompt.deleteLater()

    def test_manual_check_before_setup_explains_problem_instead_of_opening_wizard(self):
        self.config.app.setup_completed = False
        self.app._backend_ready = False
        with patch.object(self.overlay, "show_first_run_wizard") as wizard:
            self.controller.show_check()
            wizard.assert_not_called()
            self.assertIn("首次设置尚未完成", self.controller.dialog.hint.text())
            self.assertTrue(self.controller.dialog.setup.isVisible())
            self.controller.dialog.setup.click()
            wizard.assert_called_once_with(self.app._start_backend_after_setup)

    def test_multiple_problems_are_rendered_with_stage_markers(self):
        self.controller.show_check()
        self.app._paused = True
        self.app._audio.capture = None
        self.app._audio.last_error = "target exited"
        self.controller.check.error = "HTTP 429"
        self.controller.poll()
        hint = self.controller.dialog.hint.text()
        for expected in ("暂停", "target exited", "HTTP 429"):
            self.assertIn(expected, hint)
        self.assertTrue(self.controller.dialog.rows[1].text().startswith("!"))
        self.assertTrue(self.controller.dialog.rows[3].text().startswith("!"))
        self.assertFalse(self.controller.dialog.seen.isEnabled())

    def test_local_model_missing_is_reported_without_retrying_asr(self):
        self.config.translation.provider = "local"
        with patch("voxgo.ui.live_check.model_files_present", return_value=False):
            self.controller.show_check()
            self.assertFalse(self.controller.check.models)
            self.assertIn("本地翻译模型尚未就绪", self.controller.dialog.hint.text())
            self.assertFalse(self.controller.dialog.model_retry.isVisible())
        with patch("voxgo.ui.live_check.model_files_present", return_value=True):
            self.controller.poll()
            self.assertTrue(self.controller.check.models)

    def test_successful_translation_invites_without_requiring_a_check_or_render(self):
        self.translation()
        self.assertTrue(self.config.app.first_translation_at)
        self.assertFalse(self.config.app.first_subtitle_at)
        self.assertIsNone(self.controller.dialog)
        self.assertTrue(self.controller.banner.isVisible())
        self.assertTrue(self.config.app.community_invitation_seen)
        self.assertFalse(self.config.app.community_invitation_dismissed)
        self.overlay.config.locked = True
        self.controller.poll()
        self.assertFalse(self.controller.banner.isVisible())
        self.overlay.config.locked = False
        self.controller.poll()
        self.assertTrue(self.controller.banner.isVisible())

    def test_failed_empty_unknown_and_stale_translation_do_not_invite(self):
        self.translation("failed", "[翻译失败]", "401")
        self.translation("empty", "")
        self.translation("old", revision=2)
        self.controller.translation_received.emit("unknown", 1, "text", "")
        self.qt.processEvents()
        self.assertFalse(self.config.app.first_translation_at)
        self.assertIsNone(self.controller.banner)

    def test_only_explicit_dismissal_blocks_invitation_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            self.app._save_user_settings = lambda: save_user_settings(self.config, path)
            self.translation()
            loaded = default_app_config()
            load_user_settings(loaded, path)
            self.assertFalse(loaded.app.community_invitation_dismissed)
            self.controller.stop()
            self.controller.deleteLater()
            self.qt.processEvents()
            self.config.app = loaded.app
            self.controller = FirstSuccessController(self.app)
            self.controller.poll()
            self.assertTrue(self.controller.banner.isVisible())
            self.assertEqual(self.controller.banner.dismiss_button.text(), "不再显示")
            self.controller.banner.dismiss_button.click()
            load_user_settings(loaded, path)
            self.assertTrue(loaded.app.community_invitation_dismissed)
            self.translation("b")
            self.controller.poll()
            self.assertFalse(self.controller.banner.isVisible())


class CommunityPersistenceTests(unittest.TestCase):
    def test_old_opt_out_is_preserved_but_explicit_new_seen_only_is_not_an_opt_out(self):
        for data, expected in (({"community_invitation_seen": True}, True),
                ({"community_invitation_seen": True, "community_invitation_dismissed": False}, False)):
            with tempfile.TemporaryDirectory() as directory:
                data["first_subtitle_at"] = "2026-11-17"
                path = Path(directory)
                (path / "user_settings.json").write_text(json.dumps({"app": data}), encoding="utf-8")
                config = default_app_config()
                load_user_settings(config, path)
                self.assertEqual(config.app.community_invitation_dismissed, expected)
                self.assertEqual(config.app.first_translation_at, "2026-11-17")

    def test_upgrade_preserves_opt_out_and_clean_install_resets_it(self):
        self.assertIn("user_settings.json", PRESERVE_PATHS)
        with tempfile.TemporaryDirectory() as directory:
            old, updated, fresh = (Path(directory) / name for name in ("old", "new", "fresh"))
            for path in (old, updated, fresh):
                path.mkdir()
            config = default_app_config()
            config.app.first_translation_at = "2026-11-17"
            config.app.community_invitation_dismissed = True
            save_user_settings(config, old)
            shutil.copy2(old / "user_settings.json", updated / "user_settings.json")
            loaded = default_app_config()
            load_user_settings(loaded, updated)
            self.assertTrue(loaded.app.community_invitation_dismissed)
            fresh_config = default_app_config()
            load_user_settings(fresh_config, fresh)
            self.assertFalse(fresh_config.app.community_invitation_dismissed)
            self.assertFalse(fresh_config.app.first_translation_at)

    def test_settings_copy_retains_new_fields_and_retired_hint_is_not_saved(self):
        config = default_app_config()
        config.app.first_translation_at = "2026-11-17"
        config.app.community_invitation_dismissed = True
        copied = _copy_runtime_config(config.app)
        self.assertEqual(copied.first_translation_at, config.app.first_translation_at)
        self.assertTrue(copied.community_invitation_dismissed)
        snapshot = copy.deepcopy(serialize_user_settings(config))
        self.assertNotIn("subtitle_check_prompted", snapshot["app"])
