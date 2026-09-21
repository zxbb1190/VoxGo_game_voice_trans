import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from voxgo.analytics.client import LocalAnalytics


class LocalAnalyticsTests(unittest.TestCase):
    def finish(self, client):
        client.stop()
        client._thread.join(timeout=3)
        self.assertFalse(client._thread.is_alive())

    def snapshots(self, root):
        return [json.loads(p.read_text()) for p in Path(root).glob('analytics/*/*.json')]

    def test_real_events_and_modes_survive_stop(self):
        with tempfile.TemporaryDirectory() as root:
            client = LocalAnalytics(root, 'test')
            client.set_active(True, 'offline')
            client.set_active(False)
            client.set_active(True, 'offline')
            client.set_active(True, 'api')
            client.increment('translation_success')
            client.increment('translation_failed')
            client.observe('translation', 12.6)
            client.observe('asr', 8)
            client.observe('translation', -1)
            self.finish(client)
            values = self.snapshots(root)[0]['metrics']
            self.assertEqual(values['app_starts'], 1)
            self.assertEqual(values['sessions'], 1)
            self.assertEqual(values['offline_sessions'], 1)
            self.assertEqual(values['api_sessions'], 1)
            self.assertEqual(values['translation_success'], 1)
            self.assertEqual(values['translation_failed'], 1)
            self.assertEqual(values['translation_latency_samples'], 1)
            self.assertEqual(values['translation_latency_sum_ms'], 13)
            self.assertEqual(values['asr_latency_samples'], 1)

    def test_utc_midnight_counts_continuing_session_and_active_mode(self):
        from datetime import datetime, timezone
        current = [datetime(2026, 9, 17, 23, 59, 59, tzinfo=timezone.utc)]

        def wait_for(predicate):
            deadline = time.monotonic() + 3
            while not predicate():
                if time.monotonic() >= deadline:
                    self.fail('analytics did not flush expected UTC day')
                time.sleep(0.02)

        with tempfile.TemporaryDirectory() as root:
            with patch('voxgo.analytics.client.datetime') as clock:
                clock.now.side_effect = lambda tz: current[0]
                client = LocalAnalytics(root, 'test', flush_interval=0.1)
                try:
                    client.set_active(True, 'api')
                    wait_for(lambda: any(s['metrics'].get('api_sessions') == 1
                                         for s in self.snapshots(root)))
                    current[0] = datetime(2026, 9, 18, tzinfo=timezone.utc)
                    wait_for(lambda: any(s['date'] == '2026-09-18'
                                         and s['metrics'].get('api_sessions') == 1
                                         for s in self.snapshots(root)))
                    client.set_active(False)
                    # Ensure paused state has reached the worker before next midnight.
                    time.sleep(0.2)
                    current[0] = datetime(2026, 9, 19, tzinfo=timezone.utc)
                    wait_for(lambda: any(s['date'] == '2026-09-19'
                                         for s in self.snapshots(root)))
                    paused = next(s['metrics'] for s in self.snapshots(root)
                                  if s['date'] == '2026-09-19')
                    self.assertEqual(paused['sessions'], 1)
                    self.assertEqual(paused.get('api_sessions', 0), 0)
                    client.set_active(True, 'api')
                    client.set_active(True, 'offline')
                    client.set_active(True, 'api')
                finally:
                    self.finish(client)
                snapshots = {s['date']: s['metrics'] for s in self.snapshots(root)}
                self.assertEqual(sum(s.get('app_starts', 0) for s in snapshots.values()), 1)
                self.assertTrue(all(s['sessions'] == 1 for s in snapshots.values()))
                self.assertEqual(snapshots['2026-09-19']['api_sessions'], 1)
                self.assertEqual(snapshots['2026-09-19']['offline_sessions'], 1)

    def test_instances_do_not_overwrite_each_other(self):
        with tempfile.TemporaryDirectory() as root:
            first = LocalAnalytics(root, 'test')
            second = LocalAnalytics(root, 'test')
            first.increment('translation_success', 2)
            second.increment('translation_success', 3)
            self.finish(first)
            self.finish(second)
            self.assertEqual(sorted(s['metrics']['translation_success']
                                    for s in self.snapshots(root)), [2, 3])

    def test_runtime_excludes_paused_time_and_flushes_periodically(self):
        with tempfile.TemporaryDirectory() as root:
            client = LocalAnalytics(root, 'test', flush_interval=0.1)
            client.set_active(True, 'api')
            time.sleep(1.25)
            client.set_active(False)
            time.sleep(1.25)
            self.assertEqual(self.snapshots(root)[0]['metrics']['session_seconds'], 1)
            self.finish(client)
            self.assertEqual(self.snapshots(root)[0]['metrics']['session_seconds'], 1)

    def test_stop_does_not_wait_for_blocked_disk(self):
        import threading
        entered, release = threading.Event(), threading.Event()

        def blocked_flush(_):
            entered.set()
            release.wait(3)

        with tempfile.TemporaryDirectory() as root:
            with patch('voxgo.analytics.client.DailyMetrics.flush', blocked_flush):
                client = LocalAnalytics(root, 'test')
                self.assertTrue(entered.wait(1))
                start = time.monotonic()
                client.increment('translation_success')
                client.stop()
                self.assertLess(time.monotonic() - start, 0.2)
                release.set()
                self.finish(client)

    def test_storage_failure_is_isolated(self):
        with tempfile.TemporaryDirectory() as root:
            with patch('voxgo.analytics.client.DailySnapshotStore', side_effect=OSError):
                client = LocalAnalytics(root, 'test')
                client.increment('translation_success')
                client.observe('asr', 10)
                client.set_active(True, 'api')
                self.finish(client)
                self.assertEqual(self.snapshots(root), [])

    def test_revoked_collector_does_not_recreate_removed_shards(self):
        import shutil
        import threading
        allowed = threading.Event()
        allowed.set()
        with tempfile.TemporaryDirectory() as root:
            client = LocalAnalytics(root, 'test', flush_interval=0.1,
                                    collection_allowed=allowed.is_set)
            deadline = time.monotonic() + 3
            while not self.snapshots(root):
                self.assertLess(time.monotonic(), deadline)
                time.sleep(0.01)
            allowed.clear()
            client.increment('translation_success')
            client._thread.join(timeout=3)
            self.assertFalse(client._thread.is_alive())
            shutil.rmtree(Path(root) / 'analytics')
            client.increment('translation_success')
            self.finish(client)
            self.assertFalse((Path(root) / 'analytics').exists())

    def test_gate_failure_writes_nothing(self):
        def broken():
            raise OSError('consent unavailable')
        with tempfile.TemporaryDirectory() as root:
            client = LocalAnalytics(root, 'test', collection_allowed=broken)
            self.finish(client)
            self.assertEqual(self.snapshots(root), [])

    def test_aggregate_budget_includes_previous_instances(self):
        with tempfile.TemporaryDirectory() as root:
            old = Path(root) / 'analytics' / ('a' * 32)
            old.mkdir(parents=True)
            for index in range(100):
                (old / f'2026-01-01.json.corrupt-{index}').write_text('{}')
            client = LocalAnalytics(root, 'test')
            self.finish(client)
            self.assertLessEqual(len(list(Path(root).glob('analytics/*/*'))), 90)


if __name__ == '__main__':
    unittest.main()
