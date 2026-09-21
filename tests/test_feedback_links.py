import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from unittest.mock import patch
from PyQt5.QtWidgets import QApplication
from voxgo.ui.config_models import OverlayConfig, HotkeyConfig
from voxgo.ui.settings_dialog import SettingsDialog
from voxgo.ui.dialogs import FeedbackDialog


class FeedbackLinksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_only_configured_https_community_links_are_shown(self):
        with patch('voxgo.app_info.KOOK_URL', ''), patch('voxgo.app_info.DISCORD_URL', 'javascript:alert(1)'):
            dialog = SettingsDialog(OverlayConfig(), HotkeyConfig())
        try:
            self.assertEqual(set(dialog.feedback_link_buttons), {'GitHub Issues'})
            with patch('webbrowser.open') as browser:
                dialog.feedback_link_buttons['GitHub Issues'].click()
                browser.assert_called_once_with('https://github.com/zxbb1190/VoxGo_game_voice_trans/issues/new')
        finally:
            dialog.close()

    def test_valid_invitation_links_and_manual_copy(self):
        with patch('voxgo.app_info.KOOK_URL', 'https://kook.vip/example'), patch('voxgo.app_info.DISCORD_URL', 'https://discord.gg/example'):
            dialog = SettingsDialog(OverlayConfig(), HotkeyConfig())
        try:
            self.assertEqual(len(dialog.feedback_link_buttons), 3)
        finally:
            dialog.close()
        preview = FeedbackDialog('safe diagnostics')
        try:
            preview._copy()
            self.assertEqual(self.app.clipboard().text(), 'safe diagnostics')
        finally:
            preview.close()
