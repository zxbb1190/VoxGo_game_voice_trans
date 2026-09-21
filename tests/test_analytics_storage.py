import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from voxgo.analytics import DailyMetrics, DailySnapshotStore


class AnalyticsStorageTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.today = date(2026, 9, 17)
        self.store = DailySnapshotStore(self.root, today=lambda: self.today)

    def test_acknowledgement_requires_closed_day_and_exact_revision(self):
        day = self.today.isoformat()
        first = {'metrics': {'app_starts': 1}}
        self.store.save(day, first)
        revision = self.store.revision(first)
        self.assertFalse(self.store.mark_uploaded(day, revision))
        self.today += timedelta(days=1)
        self.store.save(day, {'metrics': {'app_starts': 2}})
        self.assertFalse(self.store.mark_uploaded(day, revision))
        current = self.store.load(day)
        self.assertTrue(self.store.mark_uploaded(day, self.store.revision(current)))
        self.assertFalse(self.store.path_for(day).exists())

    def test_rollover_and_reload(self):
        metrics = DailyMetrics(self.store, '0.4.3')
        metrics.increment('app_starts')
        self.today += timedelta(days=1)
        metrics.increment('app_starts', 2)
        self.assertTrue(metrics.flush())
        self.assertEqual(self.store.load('2026-09-17')['metrics']['app_starts'], 1)
        reloaded = DailyMetrics(self.store, '0.4.3')
        self.assertEqual(reloaded.snapshot['metrics']['app_starts'], 2)

    def test_concurrent_counters_do_not_write_per_event(self):
        metrics = DailyMetrics(self.store, '0.4.3')
        with patch.object(self.store, 'save', wraps=self.store.save) as save:
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(lambda _: metrics.increment('translation_success'), range(1000)))
            save.assert_not_called()
            metrics.flush()
        self.assertEqual(self.store.load('2026-09-17')['metrics']['translation_success'], 1000)

    def test_all_owned_files_share_count_and_byte_budget(self):
        self.store.max_files = 3
        self.store.max_bytes = 150
        self.store.save('2026-09-17', {'metrics': {}})
        for index in range(10):
            (self.root / f'2026-09-17.json.corrupt-{index}').write_text('x' * 60)
            (self.root / f'.snapshot-{index}').write_text('x' * 60)
        self.store.cleanup()
        files = list(self.root.iterdir())
        self.assertLessEqual(len(files), 3)
        self.assertLessEqual(sum(p.stat().st_size for p in files), 150)
        self.assertTrue(self.store.path_for('2026-09-17').exists())

    def test_expiry_without_upload_and_unrelated_file_preserved(self):
        self.store.save('2026-09-17', {'metrics': {}})
        (self.root / 'personal.json').write_text('{}')
        self.today += timedelta(days=30)
        self.store.cleanup()
        self.assertFalse(self.store.path_for('2026-09-17').exists())
        self.assertTrue((self.root / 'personal.json').exists())

    def test_corrupt_and_schema_invalid_data(self):
        self.store.path_for('2026-09-17').write_text('{bad')
        self.assertEqual(self.store.load('2026-09-17'), {})
        self.assertTrue(list(self.root.glob('*.corrupt-*')))
        self.store.save('2026-09-17', {'metrics': []})
        metrics = DailyMetrics(self.store, '0.4.3')
        self.assertTrue(metrics.increment('app_starts'))

    def test_unwritable_root_and_failed_replace(self):
        blocked = self.root / 'blocked'
        blocked.write_text('x')
        store = DailySnapshotStore(blocked / 'child', today=lambda: self.today)
        self.assertFalse(store.save('2026-09-17', {}))
        self.store.save('2026-09-17', {'old': True})
        with patch('voxgo.analytics.storage.os.replace', side_effect=OSError('denied')):
            self.assertFalse(self.store.save('2026-09-17', {'new': True}))
        self.assertEqual(self.store.load('2026-09-17'), {'old': True})
        self.assertFalse(list(self.root.glob('.snapshot-*')))

    def test_invalid_values_and_size_limits(self):
        metrics = DailyMetrics(self.store, '0.4.3')
        for value in [-1, float('nan'), float('inf'), True, '12']:
            self.assertFalse(metrics.observe('asr', value))
        self.assertFalse(metrics.increment('api_key'))
        self.assertFalse(self.store.save('2026-09-18', {}))
        self.assertFalse(self.store.save('2026-09-17', {'large': 'x' * 33000}))
        metrics.observe('asr', 12)
        metrics.observe('asr', 8)
        self.assertEqual(metrics.snapshot['metrics']['asr_latency_sum_ms'], 20)
        self.assertEqual(metrics.snapshot['metrics']['asr_latency_samples'], 2)
