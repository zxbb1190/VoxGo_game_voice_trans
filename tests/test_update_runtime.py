"""Update scheduling and result handoff on a real worker thread, without network."""
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from voxgo.update.checker import UpdateCheckResult, UpdateSettings
from voxgo.update.runtime import UpdateRuntime


class UpdateRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.config = SimpleNamespace(update=UpdateSettings())
        self.save, self.notify, self.migrate, self.overlay = Mock(), Mock(), Mock(), Mock()
        self.stopping = threading.Event()
        self.runtime = UpdateRuntime('0.6.0', lambda: self.config, self.migrate, self.save, self.notify)
        self.addCleanup(self.join_worker)

    def join_worker(self):
        if self.runtime._thread:
            self.runtime._thread.join(3)
            self.assertFalse(self.runtime._thread.is_alive())

    def request(self, manual=False):
        return self.runtime.request(manual, self.overlay, self.stopping.is_set)

    def test_disabled_recent_or_stopping_automatic_checks_do_not_start(self):
        with patch('voxgo.update.runtime.check_for_update') as check:
            self.config.update.enabled = False
            self.assertFalse(self.request())
            self.config.update.enabled = True
            self.config.update.last_check_at = 1000
            with patch('voxgo.update.checker.time.time', return_value=1001):
                self.assertFalse(self.request())
            self.stopping.set()
            self.assertFalse(self.request(manual=True))
            check.assert_not_called()
        self.save.assert_not_called()

    def test_manual_override_deduplicates_and_uses_a_settings_snapshot(self):
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)
        result = UpdateCheckResult('up_to_date', checked_at=1234)
        seen = []

        def check(version, settings, **kwargs):
            seen.append((version, settings, kwargs))
            entered.set()
            self.assertTrue(release.wait(3))
            return result

        self.config.update.enabled = False
        self.config.update.channel = 'beta'
        with patch('voxgo.update.runtime.check_for_update', side_effect=check) as checker:
            self.assertTrue(self.request(manual=True))
            self.assertTrue(entered.wait(3))
            self.assertFalse(self.request(manual=True))
            self.config.update.channel = 'stable'
            release.set()
            self.join_worker()
            checker.assert_called_once()
        self.assertEqual(seen[0][1].channel, 'beta')
        self.assertTrue(seen[0][2]['manual'])
        self.assertEqual(self.config.update.last_check_at, 1234)
        self.save.assert_called_once()
        self.overlay.handle_update_check_result.assert_called_once_with(result, True)
        self.notify.assert_not_called()

    def test_exception_becomes_error_and_manual_notification(self):
        with patch('voxgo.update.runtime.check_for_update', side_effect=OSError('offline')):
            self.assertTrue(self.request(manual=True))
            self.join_worker()
        result, manual = self.overlay.handle_update_check_result.call_args.args
        self.assertEqual((result.status, result.message, manual), ('error', 'offline', True))
        self.assertGreater(self.config.update.last_check_at, 0)
        self.save.assert_called_once()
        self.notify.assert_called_once_with('更新检查失败', 'offline', '错误')

    def test_shutdown_suppresses_late_ui_and_notifications_but_saves_check_time(self):
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)

        def delayed(*args, **kwargs):
            entered.set()
            self.assertTrue(release.wait(3))
            return UpdateCheckResult('error', message='offline', checked_at=5678)

        with patch('voxgo.update.runtime.check_for_update', side_effect=delayed):
            self.assertTrue(self.request(manual=True))
            self.assertTrue(entered.wait(3))
            self.stopping.set()
            release.set()
            self.join_worker()
        self.assertEqual(self.config.update.last_check_at, 5678)
        self.save.assert_called_once()
        self.overlay.handle_update_check_result.assert_not_called()
        self.notify.assert_not_called()

    def test_background_error_is_delivered_without_a_manual_popup(self):
        result = UpdateCheckResult('error', message='offline', checked_at=1234)
        with patch('voxgo.update.runtime.check_for_update', return_value=result):
            self.assertTrue(self.request())
            self.join_worker()
        self.overlay.handle_update_check_result.assert_called_once_with(result, False)
        self.notify.assert_not_called()

    def test_ignored_version_is_normalized_and_persisted(self):
        self.runtime.ignore_version(' v0.7.0 ')
        self.assertEqual(self.config.update.ignored_version, '0.7.0')
        self.save.assert_called_once()
        snapshot = self.runtime.snapshot_settings()
        self.assertIsNot(snapshot, self.config.update)
        self.assertEqual(snapshot.ignored_version, '0.7.0')
