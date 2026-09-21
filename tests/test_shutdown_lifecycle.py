import asyncio
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from voxgo.app import VoxGoApp
from voxgo.translation.runtime import TranslationRuntime


class ShutdownLifecycleTests(unittest.TestCase):
    def setUp(self):
        cleanup = patch("voxgo.translation.local.shutdown_local_translation", return_value=True)
        cleanup.start()
        self.addCleanup(cleanup.stop)
        threads = patch("voxgo.app.threading.enumerate", return_value=[threading.main_thread()])
        threads.start()
        self.addCleanup(threads.stop)

    def make_app(self):
        app = VoxGoApp.__new__(VoxGoApp)
        app._audio = SimpleNamespace(stop=Mock())
        app._stop_speech_worker = Mock(return_value=True)
        app._remove_hotkeys = Mock()
        app._mobile = SimpleNamespace(stop=Mock())
        app._translation = SimpleNamespace(close=Mock(return_value=True))
        app._startup_thread = None
        app._speech_recognizer = SimpleNamespace(cleanup=Mock())
        return app

    def test_cleanup_continues_after_failure_and_can_retry(self):
        app = self.make_app()
        app._audio.stop.side_effect = RuntimeError('device stuck')
        app._cleanup_services()
        self.assertTrue(app._shutdown_errors)
        app._mobile.stop.assert_called_once()
        app._translation.close.assert_called_once()
        app._audio.stop.side_effect = None
        app._cleanup_services()
        self.assertEqual(app._shutdown_errors, [])

    def test_active_startup_preserves_models_and_reports_incomplete(self):
        app = self.make_app()
        app._startup_thread = SimpleNamespace(is_alive=lambda: True, join=Mock())
        app._cleanup_services()
        app._speech_recognizer.cleanup.assert_not_called()
        app._translation.close.assert_called_with(cleanup_allowed=False)
        self.assertTrue(app._shutdown_errors)

    def test_native_inference_keeps_shutdown_incomplete(self):
        app = self.make_app()
        with patch("voxgo.translation.local.shutdown_local_translation", return_value=False):
            app._cleanup_services()
        self.assertTrue(any("local translation" in error for error in app._shutdown_errors))

    def test_shutdown_cannot_be_resumed(self):
        app = self.make_app()
        app._stopping = True
        app._paused = True
        app._toggle_translation()
        self.assertTrue(app._paused)

    def test_cancel_inflight_and_reject_new_translation(self):
        runtime = TranslationRuntime(Mock(), {'errors': 0}, {}, lambda: None)
        started = threading.Event()
        cancelled = threading.Event()
        async def translate(*args):
            started.set()
            try:
                await asyncio.sleep(60)
            finally:
                cancelled.set()
        runtime.client = SimpleNamespace(config=SimpleNamespace(), close=Mock())
        async def close():
            pass
        runtime.client.close = close
        runtime._translate_and_publish = translate
        runtime.start_loop()
        try:
            runtime.translate_async('one', 'hello')
            self.assertTrue(started.wait(3))
            runtime.begin_shutdown()
            self.assertTrue(cancelled.wait(3))
            runtime.translate_async('two', 'ignored')
            self.assertTrue(runtime.close())
            self.assertFalse(runtime.thread.is_alive())
            self.assertEqual(runtime._stats['errors'], 0)
        finally:
            runtime.close()


if __name__ == '__main__':
    unittest.main()

class ShutdownRecoveryTests(unittest.TestCase):
    def app(self):
        owner = VoxGoApp.__new__(VoxGoApp)
        owner.config = SimpleNamespace(app=SimpleNamespace(language='en-US'))
        owner._shutdown_state = 'stopping'
        owner._shutdown_started_at = 0
        owner._shutdown_timer = Mock()
        owner._overlay = Mock()
        owner._tray = Mock()
        owner._qt_app = Mock()
        owner._sync_tray_state = Mock()
        owner._notify_user = Mock()
        owner._show_shutdown_recovery = Mock()
        return owner

    def test_timeout_keeps_event_loop_and_exposes_recovery_without_tray(self):
        owner = self.app()
        owner._shutdown_thread = Mock()
        owner._shutdown_thread.is_alive.return_value = True
        owner._poll_shutdown()
        self.assertEqual(owner._shutdown_state, 'failed')
        owner._show_shutdown_recovery.assert_called_once()
        owner._tray.hide.assert_not_called()
        owner._qt_app.quit.assert_not_called()

    def test_cleanup_error_keeps_tray_and_window_until_retry(self):
        owner = self.app()
        owner._shutdown_thread = None
        owner._shutdown_errors = ['audio timeout']
        owner._poll_shutdown()
        self.assertEqual(owner._shutdown_state, 'failed')
        owner._overlay.show.assert_called_once()
        owner._tray.hide.assert_not_called()
        owner._qt_app.quit.assert_not_called()
        owner._shutdown_errors = []
        owner._poll_shutdown()
        self.assertEqual(owner._shutdown_state, 'complete')
        self.assertTrue(owner._overlay._allow_close)
        owner._qt_app.quit.assert_called_once()

    def test_fallback_loop_closing_during_cancellation_does_not_abort_shutdown(self):
        runtime = TranslationRuntime(Mock(), {}, {}, lambda: None)
        loop = Mock()
        loop.is_running.return_value = True
        loop.call_soon_threadsafe.side_effect = RuntimeError('Event loop is closed')
        runtime._fallback_loops.add(loop)
        runtime.begin_shutdown()
        self.assertTrue(runtime._shutdown_requested.is_set())
