import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt5.QtWidgets import QApplication

from voxgo.app import VoxGoApp
from voxgo.i18n import UI_LANGUAGE_EN
from voxgo.translation import TranslationConfig
from voxgo.ui.config_models import AudioDeviceConfig, DebugConfig, OverlayConfig, RuntimeConfig
from voxgo.ui.dialogs import FirstRunWizard
from voxgo.ui.overlay_window import GameOverlay
from voxgo.ui.tray_controller import TrayController


class Issue2UiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt_app = QApplication.instance() or QApplication([])

    def test_english_pause_notice_and_overlay_state(self):
        notices = []

        class OverlayStub:
            def __init__(self):
                self.paused = None

            def set_paused(self, paused):
                self.paused = paused

        owner = VoxGoApp.__new__(VoxGoApp)
        owner.config = SimpleNamespace(app=RuntimeConfig(language=UI_LANGUAGE_EN))
        owner._paused = False
        owner._overlay = OverlayStub()
        owner._clear_realtime_buffers = lambda reason: (0, 0)
        owner._sync_tray_state = lambda: None
        owner._notify_user = lambda title, message, level: notices.append((title, message, level))

        owner._toggle_translation()

        self.assertTrue(owner._paused)
        self.assertTrue(owner._overlay.paused)
        self.assertEqual(
            notices,
            [("Translation Status", "Translation paused", "Status")],
        )

    def test_overlay_has_pause_button_and_persistent_paused_label(self):
        callbacks = []
        overlay = GameOverlay(
            config=OverlayConfig(),
            app_config=RuntimeConfig(language=UI_LANGUAGE_EN),
            on_pause_toggle_requested=lambda: callbacks.append("toggle"),
        )
        try:
            self.assertTrue(overlay._paused_status_label.isHidden())
            overlay.set_paused(True)
            self.assertFalse(overlay._paused_status_label.isHidden())
            self.assertEqual(overlay._paused_status_label.text(), "PAUSED")
            self.assertEqual(overlay._pause_button.toolTip(), "Resume translation")

            overlay._pause_button.click()
            self.assertEqual(callbacks, ["toggle"])
        finally:
            overlay.close()

    def test_first_run_wizard_starts_with_language_page_and_switches_to_english(self):
        app_config = RuntimeConfig()
        wizard = FirstRunWizard(
            AudioDeviceConfig(),
            TranslationConfig(),
            app_config=app_config,
            debug_config=DebugConfig(),
        )
        try:
            self.assertEqual(wizard.stack.count(), 4)
            self.assertEqual(wizard.stack.currentIndex(), 0)
            english_row = wizard.wizard_language_combo.findData(UI_LANGUAGE_EN)
            wizard.wizard_language_combo.setCurrentIndex(english_row)
            self.qt_app.processEvents()

            self.assertEqual(app_config.language, UI_LANGUAGE_EN)
            self.assertEqual(wizard.windowTitle(), "VoxGo First-Run Setup")
            self.assertEqual(wizard.wizard_language_title.text(), "Choose Your Interface Language")
            self.assertEqual(wizard.wizard_translation_title.text(), "Check Your Translation Provider")
            self.assertEqual(wizard.wizard_audio_title.text(), "Check Your Game Audio")
            self.assertEqual(wizard.wizard_audio_device_combo.itemText(0), "Auto select")
            self.assertEqual(wizard.wizard_finish_title.text(), "Ready to Start Live Translation")
            self.assertEqual(wizard.next_button.text(), "Next")
        finally:
            wizard._completed = True
            wizard.close()

    def test_tray_setup_reports_unavailable_environment(self):
        class UnavailableTray:
            @staticmethod
            def isSystemTrayAvailable():
                return False

        owner = SimpleNamespace(config=SimpleNamespace())
        controller = TrayController(owner)

        self.assertFalse(controller.setup(UnavailableTray, object, object(), None, None))
        self.assertEqual(controller.setup_error, "system tray is not available")

    def test_tray_setup_and_restore_hint_use_current_language(self):
        class Signal:
            def connect(self, callback):
                self.callback = callback

        class Action:
            def __init__(self, text):
                self.text = text
                self.triggered = Signal()

            def setText(self, text):
                self.text = text

        class Menu:
            def __init__(self, parent):
                self.parent = parent

            def addAction(self, text):
                return Action(text)

            def addSeparator(self):
                pass

        class Tray:
            @staticmethod
            def isSystemTrayAvailable():
                return True

            def __init__(self, icon, parent):
                self.activated = Signal()
                self.visible = False
                self.messages = []

            def setToolTip(self, text):
                self.tooltip = text

            def setContextMenu(self, menu):
                self.menu = menu

            def show(self):
                self.visible = True

            def hide(self):
                self.visible = False

            def isVisible(self):
                return self.visible

            def showMessage(self, title, message):
                self.messages.append((title, message))

        class QtApp:
            def windowIcon(self):
                return object()

            def activeWindow(self):
                return None

        class Overlay:
            def isVisible(self):
                return True

        owner = SimpleNamespace(
            config=SimpleNamespace(
                app=RuntimeConfig(language=UI_LANGUAGE_EN),
                hotkeys=SimpleNamespace(toggle_overlay="ctrl+shift+t"),
                overlay=SimpleNamespace(compact_mode=False),
            ),
            _paused=False,
            _tray_toggle_overlay=lambda: None,
            _tray_reset_overlay_position=lambda: None,
            _toggle_translation=lambda: None,
            _clear_history=lambda: None,
            _tray_toggle_compact_mode=lambda: None,
            _tray_open_settings=lambda: None,
            _tray_show_fullscreen_help=lambda: None,
            _request_shutdown=lambda: None,
            _handle_tray_activated=lambda reason: None,
        )
        controller = TrayController(owner)

        self.assertTrue(controller.setup(Tray, Menu, QtApp(), None, Overlay()))
        self.assertEqual(controller.actions["toggle_translation"].text, "Pause Translation")
        controller.show_restore_hint()
        self.assertIn("ctrl+shift+t", controller.icon.messages[0][1])


if __name__ == "__main__":
    unittest.main()
