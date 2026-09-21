import json
import tempfile
import time
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from voxgo.analytics.client import LocalAnalytics
from voxgo.analytics.aggregation import AggregateStore
from voxgo.app import VoxGoApp


class LifecycleIntegrationTests(unittest.TestCase):
    def test_disk_stall_cannot_block_clean_exit_indefinitely(self):
        with tempfile.TemporaryDirectory() as folder:
            entered, release = threading.Event(), threading.Event()
            from voxgo.analytics.daily_metrics import DailyMetrics
            original = DailyMetrics.flush
            def blocked(metrics):
                entered.set()
                release.wait(3)
                return original(metrics)
            with patch.object(DailyMetrics, 'flush', blocked):
                collector = LocalAnalytics(folder, '0.4.3', lifecycle_root=Path(folder) / 'analytics')
                self.assertTrue(entered.wait(3))
                started = time.monotonic()
                collector.stop()
                collector.mark_clean_exit()
                elapsed = time.monotonic() - started
                release.set()
                collector._thread.join(3)
                collector._clean_exit_worker.join(3)
            self.assertLess(elapsed, .5)

    def test_revocation_during_start_does_not_create_shards_or_markers(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            entered, release = threading.Event(), threading.Event()
            allowed = [True]
            original = LocalAnalytics._start_lifecycle
            def delayed(collector):
                entered.set()
                release.wait(3)
                original(collector)
            with patch.object(LocalAnalytics, '_start_lifecycle', delayed):
                collector = LocalAnalytics(root, '0.4.3', storage_root=root / 'shards',
                    lifecycle_root=root, collection_allowed=lambda: allowed[0])
                self.assertTrue(entered.wait(3))
                allowed[0] = False
                collector.stop()
                revoker = threading.Thread(target=collector.abandon_lifecycle)
                revoker.start()
                release.set()
                revoker.join(3)
                collector._thread.join(3)
            self.assertFalse(list(root.rglob('*.json')))

    def test_local_lifecycle_and_usage_share_snapshot_budget(self):
        import uuid
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(LocalAnalytics, '_run'):
                collector = LocalAnalytics(root, '0.4.3', lifecycle_root=root / 'analytics')
                collector._thread.join(3)
            for i in range(100):
                directory = root / 'analytics'
                if i % 2:
                    directory /= 'shards'
                directory /= uuid.uuid4().hex
                directory.mkdir(parents=True)
                (directory / '2026-09-21.json').write_text('{}')
            collector._cleanup()
            self.assertLessEqual(len(list((root / 'analytics').rglob('*.json'))), 90)
            collector.stop()

    def test_immediate_clean_exit_cannot_leave_late_unclean_marker(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            # Delay the daemon entirely until the clean-exit call has completed.
            with patch.object(LocalAnalytics, '_run') as run:
                collector = LocalAnalytics(root, '0.4.3', lifecycle_root=root)
                collector._thread.join(3)
            collector.stop()
            collector.mark_clean_exit()
            collector._start_lifecycle()
            self.assertFalse(list((root / 'runs').glob('*.json')))
            metrics = [json.loads(p.read_text())['metrics'] for p in (root / 'shards').glob('*/*.json')]
            self.assertEqual(metrics, [{'clean_exits': 1}])

    def test_stop_request_is_not_clean_and_completed_exit_is_durable(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            collector = LocalAnalytics(root, '0.4.3', storage_root=root / 'shards', lifecycle_root=root)
            deadline = time.monotonic() + 3
            while collector._lifecycle is None and time.monotonic() < deadline:
                time.sleep(.01)
            collector.stop()
            collector._thread.join(3)
            self.assertFalse(collector._thread.is_alive())
            aggregate = AggregateStore(root, '0.4.3')
            first = aggregate.snapshots()[0]
            self.assertEqual(first['metrics']['clean_exits'], 0)
            collector.mark_clean_exit()
            collector.mark_clean_exit()
            final = aggregate.snapshots()[0]
            self.assertEqual(final['metrics']['clean_exits'], 1)
            self.assertEqual(final['package_type'], 'source')
            self.assertFalse(aggregate.acknowledge(first))
            self.assertTrue(aggregate.acknowledge(final))
            self.assertEqual(aggregate.snapshots(), [])
            self.assertEqual(aggregate._load()['days'][final['date']]['totals']['clean_exits'], 1)

    def test_app_marks_clean_only_after_event_loop_and_successful_cleanup(self):
        for failure, cleanup in ((False, 'complete'), (False, 'failed'), (True, 'complete')):
            with self.subTest(failure=failure, cleanup=cleanup):
                app = VoxGoApp.__new__(VoxGoApp)
                app._runtime_dir = Mock(return_value=Path('.'))
                app.config = SimpleNamespace(app=SimpleNamespace(setup_completed=True))
                app._translation = SimpleNamespace()
                app._start_mobile = Mock()
                app._start_qt = Mock()
                app._start_backend_thread = Mock()
                app._notify_user = Mock()
                app._write_crash_report = Mock()
                app._show_error_dialog = Mock()
                app._qt_app = Mock()
                if failure:
                    app._qt_app.exec_.side_effect = RuntimeError('test startup failure')
                def stop():
                    app._shutdown_state = cleanup
                    app._analytics.stop()
                app.stop = stop
                with patch('voxgo.analytics.client.AuthorizedAnalytics') as analytics:
                    app.start()
                    self.assertEqual(analytics.return_value.mark_clean_exit.call_count,
                                     int(not failure and cleanup == 'complete'))
