import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from voxgo.app import VoxGoApp
from voxgo.config.loader import default_app_config, save_user_settings, load_user_settings
from voxgo.ui.config_models import _copy_runtime_config
from voxgo.ui.overlay_window import GameOverlay


class CloseBehaviorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def owner(self):
        owner = VoxGoApp.__new__(VoxGoApp)
        owner.config = default_app_config()
        owner._overlay = None
        owner._save_user_settings = Mock()
        owner._minimize_to_tray = Mock(return_value=True)
        return owner

    def decide(self, owner, role, remember=False):
        class Box:
            AcceptRole = QMessageBox.AcceptRole
            DestructiveRole = QMessageBox.DestructiveRole
            Cancel = QMessageBox.Cancel
            def __init__(self, parent):
                self.buttons = []
                self.selected = None
            def setWindowTitle(self, *args): pass
            def setText(self, *args): pass
            def setInformativeText(self, *args): pass
            def setEscapeButton(self, *args): pass
            def setCheckBox(self, check): self.check = check
            def addButton(self, text, button_role=QMessageBox.RejectRole):
                button = object()
                if button_role == role: self.selected = button
                return button
            def exec_(self): self.check.setChecked(remember)
            def clickedButton(self): return self.selected
        # Native Windows message boxes are exercised by desktop smoke; unit tests
        # isolate decisions and persistence without opening a native modal dialog.
        with patch('PyQt5.QtWidgets.QMessageBox', Box), patch('PyQt5.QtWidgets.QCheckBox') as check:
            check.return_value.isChecked.return_value = remember
            return owner._confirm_close_action()

    def test_cancel_does_not_exit_or_remember(self):
        owner = self.owner()
        self.assertFalse(self.decide(owner, QMessageBox.RejectRole, True))
        owner._save_user_settings.assert_not_called()
        owner._minimize_to_tray.assert_not_called()

    def test_minimize_is_remembered_only_when_tray_available(self):
        owner = self.owner()
        owner._minimize_to_tray.return_value = False
        self.assertFalse(self.decide(owner, QMessageBox.AcceptRole, True))
        owner._save_user_settings.assert_not_called()
        owner._minimize_to_tray.return_value = True
        self.assertFalse(self.decide(owner, QMessageBox.AcceptRole, True))
        self.assertEqual(owner.config.app.close_action, 'minimize')
        self.assertTrue(owner.config.app.close_action_remember)

    def test_quit_choice_persists_across_reload_and_ui_copy(self):
        owner = self.owner()
        self.assertTrue(self.decide(owner, QMessageBox.DestructiveRole, True))
        with tempfile.TemporaryDirectory() as folder:
            save_user_settings(owner.config, Path(folder))
            fresh = default_app_config()
            load_user_settings(fresh, Path(folder))
        copied = _copy_runtime_config(fresh.app)
        self.assertEqual(copied.close_action, 'quit')
        self.assertTrue(copied.close_action_remember)

    def test_native_close_and_toolbar_share_callback(self):
        overlay = GameOverlay()
        called = Mock()
        overlay._on_close_requested = called
        overlay.show()
        overlay.close()
        self.assertTrue(overlay.isVisible())
        overlay._quit_button.click()
        self.assertEqual(called.call_count, 2)
        overlay._allow_close = True
        overlay.close()
        self.assertFalse(overlay.isVisible())

    def test_saved_minimize_does_not_prompt(self):
        owner = self.owner()
        owner.config.app.close_action = 'minimize'
        owner.config.app.close_action_remember = True
        self.assertFalse(owner._confirm_close_action())
        owner._minimize_to_tray.assert_called_once()

    def test_shutdown_detaches_monitor_without_blocking_gui(self):
        overlay = GameOverlay()
        monitor = Mock()
        panel = SimpleNamespace(_monitor=monitor)
        dialog = Mock()
        dialog.audio_test_panel = panel
        dialog.wizard_audio_test_panel = None
        dialog._translation_test_runner = Mock()
        overlay._settings_dialog = dialog
        try:
            monitors = overlay.prepare_shutdown()
            self.assertEqual(monitors, [monitor])
            self.assertIsNone(panel._monitor)
            monitor.stop.assert_not_called()
            dialog._translation_test_runner.cancel.assert_called_once()
            self.assertFalse(overlay._pause_button.isEnabled())
        finally:
            overlay._settings_dialog = None
            overlay.close()
