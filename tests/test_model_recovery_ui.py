import os
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt5.QtWidgets import QApplication, QMessageBox
from voxgo.config.loader import default_app_config
from voxgo.ui.settings_dialog import SettingsDialog


class ModelRecoveryUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        config = default_app_config()
        self.dialog = SettingsDialog(config.overlay, config.hotkeys)
        self.events = []
        self.dialog.settings_changed.connect(lambda *args: self.events.append('settings'))
        self.dialog.model_recovery_requested.connect(lambda reset: self.events.append(reset))

    def tearDown(self):
        self.dialog.close()

    def test_real_overlay_forwards_recovery_signal(self):
        from voxgo.ui.overlay_window import GameOverlay
        config = default_app_config()
        overlay = GameOverlay(config=config.overlay, hotkeys=config.hotkeys)
        received = []
        overlay.model_recovery_requested.connect(received.append)
        try:
            overlay._open_settings()
            self.assertIsNotNone(overlay._settings_dialog)
            overlay._settings_dialog.model_retry_button.click()
            self.assertEqual(received, [False])
            with patch('voxgo.ui.settings_dialog.QMessageBox.question', return_value=QMessageBox.Yes):
                overlay._settings_dialog.model_reset_button.click()
            self.assertEqual(received, [False, True])
        finally:
            if overlay._settings_dialog:
                overlay._settings_dialog.close()
            overlay.hide()
            overlay.deleteLater()

    def test_retry_saves_selected_settings_before_request(self):
        self.dialog.model_retry_button.click()
        self.assertEqual(self.events, ['settings', False])

    def test_reset_cancel_does_not_request_recovery(self):
        with patch('voxgo.ui.settings_dialog.QMessageBox.question', return_value=QMessageBox.No) as question:
            self.dialog.model_reset_button.click()
        self.assertEqual(self.events, [])
        self.assertEqual(question.call_args.args[-1], QMessageBox.No)

    def test_confirm_reset_saves_before_request_and_explains_scope(self):
        with patch('voxgo.ui.settings_dialog.QMessageBox.question', return_value=QMessageBox.Yes) as question:
            self.dialog.model_reset_button.click()
        self.assertEqual(self.events, ['settings', True])
        self.assertIn('Whisper', question.call_args.args[2])
        self.assertIn('API', question.call_args.args[2])

    def test_recovery_actions_refresh_english_labels(self):
        self.dialog._ui_language = 'en-US'
        self.dialog._refresh_model_recovery_text()
        self.assertEqual(self.dialog.model_retry_button.text(), 'Retry Model Load')
        self.assertIn('models loading or in use cannot be reset', self.dialog.model_recovery_hint.text())


if __name__ == '__main__':
    unittest.main()
