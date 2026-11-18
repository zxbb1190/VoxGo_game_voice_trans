"""Real Qt delivery and persistence for first-use checks and a single invitation."""
import os
import copy
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5.QtWidgets import QApplication

from voxgo.config.loader import default_app_config, load_user_settings, save_user_settings, serialize_user_settings
from voxgo.runtime.first_success import LiveCheck
from voxgo.ui.dialogs import FirstRunWizard
from voxgo.ui.live_check import FirstSuccessController
from voxgo.ui.overlay_window import GameOverlay


class LiveCheckEvidenceTests(unittest.TestCase):
    def test_long_check_has_bounded_evidence(self):
        check = LiveCheck(1, started_at=0)
        for index in range(1000):
            check.transcript(str(index), 1, index + 1)
        self.assertLessEqual(len(check.transcripts), 128)

    def test_source_switch_discards_context_noise_gate_and_stale_dialog_state(self):
        from voxgo.app import VoxGoApp
        from voxgo.asr.whisper_engine import SpeechRecognizer
        from voxgo.runtime.settings_controller import OverlaySettingsController
        app = VoxGoApp.__new__(VoxGoApp)
        app.config = default_app_config()
        app._running, app._overlay, app._language_flow_revision = True, None, 1
        app._speech_recognizer = SpeechRecognizer(copy.deepcopy(app.config.whisper))
        app._audio, app._speech_pipeline, app._translation = Mock(), Mock(), Mock()
        app._audio.clear_pending_audio.return_value = 0
        for name in ('_setup_hotkeys', '_save_user_settings', '_analytics_call', '_notify_user',
                     '_sync_tray_state', '_restart_audio_capture'):
            setattr(app, name, Mock())
        app._refresh_cached_settings()
        old_dialog = copy.deepcopy(app.config.app)
        app.config.app.community_invitation_dismissed = True
        app.config.app.first_subtitle_at = "2026-11-11"
        app.config.app.community_invitation_seen = True
        app.config.audio.source_mode = "process"
        app.config.audio.process_path = r"C:\game.exe"
        app.config.audio.process_id, app.config.audio.process_started = 12, 34
        OverlaySettingsController(app).apply(app.config.overlay, app.config.hotkeys, app.config.audio,
            app.config.translation, copy.deepcopy(app.config.whisper), old_dialog, app.config.update)
        self.assertEqual(app._language_flow_revision, 2)
        app._restart_audio_capture.assert_called_once_with(reuse_noise_gate=False)
        app._translation.clear_context.assert_called_once()
        app._speech_pipeline.reset_for_language_switch.assert_called_once_with('en', 'zh', 2)
        self.assertTrue(app.config.app.community_invitation_seen)
        self.assertTrue(app.config.app.community_invitation_dismissed)
        self.assertEqual(app.config.app.first_subtitle_at, "2026-11-11")

    def test_old_audio_and_stale_revision_cannot_complete_new_check(self):
        check = LiveCheck(3, started_at=100)
        self.assertFalse(check.transcript("old", 3, 99))
        self.assertFalse(check.transcript("stale", 2, 101))
        self.assertFalse(check.translation("unknown", 3))
        self.assertFalse(check.present("unknown"))
        self.assertFalse(check.complete)

    def test_translation_failure_and_probe_never_mean_visible_subtitle(self):
        check = LiveCheck(1, started_at=10, models=True)
        check.transcript("a", 1, 11)
        self.assertFalse(check.translation("a", 1, "401"))
        self.assertFalse(check.present("a"))
        check.translation("a", 1)
        self.assertFalse(check.complete)
        self.assertTrue(check.present("a"))
        self.assertTrue(check.complete)

    def test_settings_persist_path_but_never_stale_pid(self):
        config = default_app_config()
        config.audio.source_mode = "process"
        config.audio.process_path = r"C:\Games\game.exe"
        config.audio.process_id = 444
        config.audio.process_started = 123456
        config.app.first_subtitle_at = "2026-11-11T00:00:00+00:00"
        config.app.subtitle_check_completed = config.app.community_invitation_seen = True
        with tempfile.TemporaryDirectory() as directory:
            save_user_settings(config, Path(directory))
            loaded = default_app_config()
            load_user_settings(loaded, Path(directory))
        self.assertEqual(loaded.audio.source_mode, "process")
        self.assertEqual(loaded.audio.process_path, config.audio.process_path)
        self.assertEqual(loaded.audio.process_id, 0)
        self.assertNotIn("process_started", serialize_user_settings(config)["audio"])
        self.assertEqual(loaded.app.first_subtitle_at, config.app.first_subtitle_at)
        self.assertTrue(loaded.app.subtitle_check_completed)
        self.assertTrue(loaded.app.community_invitation_seen)


class FirstSuccessQtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self):
        config = default_app_config()
        config.app.setup_completed = True
        self.overlay = GameOverlay(config=config.overlay, app_config=config.app)
        self.app = SimpleNamespace(config=config, _overlay=self.overlay, _language_flow_revision=1,
            _stopping=False, _paused=False, _backend_ready=True, _save_user_settings=Mock(),
            _ui_language=lambda: config.app.language, _toggle_translation=Mock(),
            _request_model_recovery=Mock(), _start_backend_after_setup=Mock(),
            _restart_audio_capture=Mock(),
            _audio=SimpleNamespace(capture=SimpleNamespace(selected_device={"name": "Fixture source"},
                last_level_dbfs=-120, last_level_at=0), last_error=""))
        self.controller = FirstSuccessController(self.app)
        self.overlay.show()
        self.qt.processEvents()

    def tearDown(self):
        self.controller.stop()
        self.overlay._fade_timer.stop()
        self.overlay.hide()
        self.overlay.deleteLater()
        self.qt.processEvents()

    def result(self, item="a", text="测试译文", error="", revision=1):
        self.controller.transcript_received.emit(item, revision, time.time())
        self.overlay.add_translation_with_id(item, "Fixture speech", "...正在翻译")
        self.controller.translation_received.emit(item, revision, text, error)
        self.overlay.update_translation(item, text, copyable=not error)
        self.qt.processEvents()

    def test_actual_queued_translation_render_completes_check_and_invites_once(self):
        self.controller.show_check()
        self.result()
        self.controller.poll()
        self.assertTrue(self.controller.check.complete)
        self.assertTrue(self.controller.dialog.seen.isEnabled())
        self.assertTrue(self.app.config.app.first_subtitle_at)
        self.assertTrue(self.app.config.app.community_invitation_seen)
        self.assertTrue(self.controller.banner.isVisible())
        self.controller.banner.dismiss_button.click()
        self.result("b")
        self.controller.poll()
        self.assertFalse(self.controller.banner.isVisible())
        self.controller.confirm_visible()
        self.assertTrue(self.app.config.app.subtitle_check_completed)

    def test_no_invitation_or_success_for_failure_empty_or_stale_result(self):
        self.controller.show_check()
        self.result("failure", "[翻译失败] 401", "401")
        self.result("empty", "", "empty")
        self.result("stale", revision=2)
        self.controller.poll()
        self.assertFalse(self.app.config.app.first_subtitle_at)
        self.assertIsNone(self.controller.banner)
        self.assertFalse(self.controller.check.complete)
        self.controller.confirm_visible()
        self.assertFalse(self.app.config.app.subtitle_check_completed)

    def test_hidden_overlay_waits_until_actual_show(self):
        self.overlay.hide()
        self.result()
        self.assertFalse(self.app.config.app.first_subtitle_at)
        self.overlay.show()
        self.qt.processEvents()
        self.assertTrue(self.app.config.app.first_subtitle_at)

    def test_cinema_success_requires_painted_cue_and_invite_waits_for_controls(self):
        self.overlay.set_display_mode('cinema')
        self.controller.show_check()
        self.result('cinema')
        for _ in range(5):
            self.qt.processEvents()
        self.controller.poll()
        self.assertTrue(self.controller.check.complete)
        self.assertTrue(self.app.config.app.first_subtitle_at)
        self.assertFalse(self.app.config.app.community_invitation_seen)
        self.overlay._cinema_hovered = True
        self.overlay._refresh_display_controls()
        self.controller.poll()
        self.assertTrue(self.controller.banner.isVisible())
        self.assertTrue(self.app.config.app.community_invitation_seen)
        self.controller.banner.dismiss_button.click()
        self.result('second')
        self.controller.poll()
        self.assertFalse(self.controller.banner.isVisible())

    def test_remove_pending_row_does_not_count_as_presented(self):
        self.controller.transcript_received.emit("a", 1, time.time())
        self.controller.translation_received.emit("a", 1, "text", "")
        self.overlay.add_translation_with_id("a", "speech", "pending")
        self.overlay.remove_translation("a")
        self.qt.processEvents()
        self.assertFalse(self.app.config.app.first_subtitle_at)

    def test_compact_and_locked_defer_invitation(self):
        self.overlay.config.compact_mode = True
        self.result()
        self.assertTrue(self.app.config.app.first_subtitle_at)
        self.assertFalse(self.app.config.app.community_invitation_seen)
        self.overlay.config.compact_mode = False
        self.overlay.config.locked = True
        self.controller.poll()
        self.assertIsNone(self.controller.banner)
        self.overlay.config.locked = False
        self.controller.poll()
        self.assertTrue(self.controller.banner.isVisible())

    def test_dismissal_survives_controller_restart(self):
        self.app.config.app.first_subtitle_at = "2026-11-11"
        self.app.config.app.community_invitation_seen = True
        self.app.config.app.community_invitation_dismissed = True
        self.controller.poll()
        self.assertIsNone(self.controller.banner)

    def test_source_change_and_retry_require_fresh_audio(self):
        self.controller.show_check()
        self.result()
        self.app._language_flow_revision = 2
        self.controller.poll()
        self.assertFalse(self.controller.check.complete)
        self.result("old", revision=1)
        self.assertFalse(self.controller.check.complete)
        self.controller.restart_check()
        self.assertFalse(self.controller.check.audio)

    def test_stage_hints_pause_failure_and_recovery(self):
        self.controller.show_check()
        self.controller.poll()
        self.assertIn("尚未收到声音", self.controller.dialog.hint.text())
        self.app._audio.capture.last_level_at = time.monotonic()
        self.app._audio.capture.last_level_dbfs = -55
        self.controller.poll()
        self.assertTrue(self.controller.check.audio)
        self.assertIn("尚未识别", self.controller.dialog.hint.text())
        self.result("fail", "[翻译失败] 401", "401")
        self.controller.poll()
        self.assertIn("401", self.controller.dialog.hint.text())
        self.app._paused = True
        self.controller.poll()
        self.assertTrue(self.controller.dialog.resume.isVisible())
        self.assertIn("暂停", self.controller.dialog.hint.text())
        self.app._paused = False
        self.app._backend_ready = False
        self.controller.poll()
        self.assertTrue(self.controller.dialog.model_retry.isVisible())
        self.controller.dialog.model_retry.click()
        self.app._request_model_recovery.assert_called_once_with(False)
        self.app._backend_ready = True
        self.app._audio.capture = None
        self.app._audio.last_error = "target exited"
        self.app.config.audio.source_mode = "process"
        self.controller.poll()
        self.assertIn("target exited", self.controller.dialog.hint.text())

    def test_close_and_shutdown_do_not_confirm_or_open_browser(self):
        with patch("voxgo.ui.live_check.webbrowser.open") as browser:
            self.controller.show_check()
            self.controller.dialog.close()
            self.assertFalse(self.app.config.app.subtitle_check_completed)
            self.controller.stop()
            self.result()
            self.assertFalse(self.app.config.app.first_subtitle_at)
            browser.assert_not_called()

    def test_retry_reconnects_only_when_capture_is_unavailable(self):
        self.controller.show_check()
        self.controller.dialog.retry.click()
        self.app._restart_audio_capture.assert_not_called()
        self.app._audio.capture = None
        self.controller.dialog.retry.click()
        self.app._restart_audio_capture.assert_called_once()

    def test_unsaved_setup_can_check_without_reopening_wizard(self):
        self.app.config.app.setup_completed = False
        self.app._setup_attempted = True
        with patch.object(self.overlay, "show_first_run_wizard") as wizard:
            self.controller.show_check()
            self.assertTrue(self.controller.dialog.isVisible())
            wizard.assert_not_called()

    def test_settings_and_wizard_share_application_selection(self):
        from voxgo.ui.audio_source import AudioSourceSelector
        from voxgo.ui.settings_dialog import SettingsDialog
        apps = [{"pid": 41, "path": r"C:\Games\game.exe", "started": 99, "title": "Game"}]
        with patch("voxgo.ui.audio_source.list_applications", return_value=apps):
            dialog = SettingsDialog(self.app.config.overlay, self.app.config.hotkeys,
                                    audio_config=self.app.config.audio, app_config=self.app.config.app)
            selector = dialog.audio_source_selector
            self.assertIsInstance(selector, AudioSourceSelector)
            selector.mode.setCurrentIndex(1)
            selector.apps.setCurrentIndex(1)
            dialog._collect_values()
            self.assertEqual(self.app.config.audio.process_id, 41)
            self.assertFalse(dialog.audio_device_combo.isEnabled())
            selector.refresh_button.click()
            self.assertEqual(selector.apps.currentData()["started"], 99)
            selector.set_language("ja-JP")
            self.assertIn("アプリ", selector.mode.itemText(1))
            selector.mode.setCurrentIndex(0)
            self.assertTrue(dialog.audio_device_combo.isEnabled())
            dialog.close()
            dialog.deleteLater()

    def test_wizard_close_is_not_setup_completion_and_can_reopen(self):
        config = default_app_config()
        wizard = FirstRunWizard(audio_config=config.audio, translation_config=config.translation,
                                app_config=config.app)
        completed = Mock()
        wizard.setup_completed.connect(completed)
        wizard.show()
        wizard.close()
        self.assertFalse(config.app.setup_completed)
        completed.assert_not_called()
        wizard.show()
        wizard._complete_setup()
        completed.assert_called_once()
        self.assertTrue(config.app.setup_completed)
        wizard.deleteLater()

    def test_wizard_reject_cancels_tests_without_completing_setup(self):
        config = default_app_config()
        wizard = FirstRunWizard(audio_config=config.audio, translation_config=config.translation,
                                app_config=config.app)
        monitor, runner = Mock(), Mock()
        wizard.wizard_audio_test_panel._monitor = monitor
        wizard._translation_test_runner = runner
        wizard.show()
        wizard.reject()
        monitor.stop.assert_called_once()
        runner.cancel.assert_called_once()
        self.assertFalse(config.app.setup_completed)
        wizard.deleteLater()

    def test_settings_reject_cancels_tests(self):
        from voxgo.ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.app.config.overlay, self.app.config.hotkeys,
                                audio_config=self.app.config.audio, app_config=self.app.config.app)
        monitor, runner = Mock(), Mock()
        dialog.audio_test_panel._monitor = monitor
        dialog._translation_test_runner = runner
        dialog.show()
        dialog.reject()
        monitor.stop.assert_called_once()
        runner.cancel.assert_called_once()
        dialog.deleteLater()

    def test_multilingual_check_and_invitation(self):
        for language in ("en-US", "ja-JP", "ko-KR", "ru-RU"):
            self.app.config.app.language = language
            self.controller.show_check()
            self.controller.poll()
            self.assertNotIn("尚未收到声音", self.controller.dialog.hint.text())
            if language != "en-US":
                self.assertNotIn("Play speech", self.controller.dialog.instruction.text())
