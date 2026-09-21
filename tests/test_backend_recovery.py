import unittest
from unittest.mock import Mock
from types import SimpleNamespace
from voxgo.app import VoxGoApp

class BackendRecoveryTests(unittest.TestCase):
    def app(self):
        app = VoxGoApp.__new__(VoxGoApp)
        app._stopping = False
        app._running = False
        app._backend_ready = False
        app._startup_thread = None
        app._speech_recognizer = SimpleNamespace(cleanup=Mock())
        app._qt_app = Mock()
        app._ui_language = lambda: 'zh'
        app._notify_user = Mock()
        app._show_error_dialog = Mock()
        app._start_backend_thread = Mock()
        return app

    def test_model_failure_keeps_ui_alive_and_explains_recovery(self):
        app = self.app()
        app._handle_backend_startup_failure('Whisper failed')
        app._qt_app.quit.assert_not_called()
        self.assertFalse(app._backend_ready)
        self.assertIn('Whisper failed', app._show_error_dialog.call_args.args[1])
        self.assertIn('设置', app._show_error_dialog.call_args.args[1])

    def test_reset_after_failure_releases_recognizer_and_starts_background_retry(self):
        app = self.app()
        app._request_model_recovery(True)
        app._speech_recognizer.cleanup.assert_called_once()
        self.assertTrue(app._reset_whisper_cache)
        app._start_backend_thread.assert_called_once()

    def test_active_download_or_model_never_deleted(self):
        app = self.app()
        app._startup_thread = SimpleNamespace(is_alive=lambda: True)
        app._request_model_recovery(True)
        app._start_backend_thread.assert_not_called()
        app._speech_recognizer.cleanup.assert_not_called()
        app._startup_thread = None
        app._running = True
        app._request_model_recovery(True)
        app._start_backend_thread.assert_not_called()
