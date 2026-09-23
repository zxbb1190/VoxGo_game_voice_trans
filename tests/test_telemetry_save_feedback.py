import unittest
from unittest.mock import Mock, patch

from voxgo.app import VoxGoApp
from voxgo.config.loader import default_app_config


class TelemetrySaveFeedbackTests(unittest.TestCase):
    def owner(self):
        owner = VoxGoApp.__new__(VoxGoApp)
        owner.config = default_app_config()
        owner._runtime_dir = Mock(return_value='unused')
        owner._ui_language = Mock(return_value='en')
        owner._notify_user = Mock()
        return owner

    def test_failed_consent_save_is_visible_and_returned(self):
        owner = self.owner()
        owner.config.app._telemetry_save_error = 'consent_not_saved'
        with patch('voxgo.app.save_user_settings', return_value=False):
            self.assertIs(owner._save_user_settings(), False)
        message = owner._notify_user.call_args.args[1]
        self.assertIn('previous choice', message)

    def test_failed_setup_save_does_not_open_full_gate(self):
        owner = self.owner()
        owner._sync_language_flow = Mock()
        owner._sync_whisper_vad_limit = Mock()
        owner._refresh_cached_settings = Mock()
        owner._start_backend_thread = Mock()
        owner._save_user_settings = Mock(return_value=False)
        owner._start_backend_after_setup()
        self.assertIs(owner.config.app.setup_completed, False)
        self.assertEqual(owner._notify_user.call_args.args[0], 'Settings Not Saved')
        owner._start_backend_thread.assert_called_once()
