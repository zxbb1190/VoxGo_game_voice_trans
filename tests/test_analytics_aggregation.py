import json
from datetime import date, timedelta
import tempfile
import unittest
from pathlib import Path
import uuid

from voxgo.analytics.aggregation import AggregateStore


class AggregationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.day = date(2026, 9, 17)
        self.store = AggregateStore(self.root, '0.4.3', today=lambda: self.day)
        self.shard = str(uuid.uuid4())

    def write(self, count, day=None, shard=None):
        day = (day or self.day).isoformat()
        path = self.root / 'shards' / (shard or self.shard) / (day + '.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'schema_version': 1, 'date': day,
                                  'metrics': {'translation_success': count}}))
        return path

    def test_retry_is_exact_after_restart(self):
        self.write(3)
        original = self.store.snapshots()
        restarted = AggregateStore(self.root, '0.4.4', today=lambda: self.day)
        self.assertEqual(original, restarted.snapshots())
        self.assertEqual(len(original[0]['metrics']), 27)

    def test_old_ack_cannot_erase_new_revision(self):
        self.write(3)
        old = self.store.snapshots()[0]
        self.write(7)
        new = self.store.snapshots()[0]
        self.assertFalse(self.store.acknowledge(old))
        self.assertEqual(new['revision'], old['revision'] + 1)
        self.assertTrue(self.store.acknowledge(new))
        self.assertEqual(self.store.snapshots(), [])

    def test_package_metadata_and_legacy_pending_survive_upgrade(self):
        import hashlib
        self.write(3)
        payload = self.store.snapshots()[0]
        self.assertEqual(payload['package_type'], 'source')
        state = self.store._load()
        entry = state['days'][self.day.isoformat()]
        for metrics in [entry['totals'], entry['pending']['metrics'], *entry['seen'].values()]:
            metrics.pop('clean_exits', None)
            metrics.pop('unclean_starts', None)
        unsigned = {k: v for k, v in entry['pending'].items() if k != 'snapshot_id'}
        entry['pending']['snapshot_id'] = hashlib.sha256(json.dumps(
            unsigned, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        old_pending = json.loads(json.dumps(entry['pending']))
        self.store._save(state)
        self.assertEqual(self.store.snapshots(), [old_pending])
        self.assertEqual(self.store.snapshots(), [old_pending])
        path = self.root / 'shards' / str(uuid.uuid4()) / (self.day.isoformat() + '.json')
        path.parent.mkdir()
        path.write_text(json.dumps({'schema_version': 1, 'date': self.day.isoformat(),
                                   'metrics': {'clean_exits': 1}}))
        updated = self.store.snapshots()[0]
        self.assertEqual(updated['metrics']['clean_exits'], 1)
        self.assertEqual(updated['metrics']['translation_success'], 3)
        self.assertFalse(self.store.acknowledge(old_pending))
        self.assertTrue(self.store.acknowledge(updated))

    def test_explicit_build_edition_in_new_snapshot(self):
        self.write(1)
        built = AggregateStore(self.root, '0.4.3', today=lambda: self.day, package_type='full-cuda')
        self.assertEqual(built.snapshots()[0]['package_type'], 'full-cuda')

    def test_compaction_preserves_baseline_and_watermark(self):
        path = self.write(3)
        self.store.acknowledge(self.store.snapshots()[0])
        path.unlink()
        self.write(4, shard=str(uuid.uuid4()))
        payload = self.store.snapshots()[0]
        self.assertEqual(payload['metrics']['translation_success'], 7)
        self.write(3)
        self.assertEqual(self.store.snapshots()[0], payload)
        self.write(5)
        self.assertEqual(self.store.snapshots()[0]['metrics']['translation_success'], 9)

    def test_lock_is_nonblocking(self):
        with self.store.lock() as first:
            self.assertTrue(first)
            with self.store.lock() as second:
                self.assertFalse(second)
        with self.store.lock() as third:
            self.assertTrue(third)

    def test_corruption_fails_closed(self):
        self.write(3)
        self.store.snapshots()
        (self.root / 'aggregate.json').write_text('{}')
        with self.assertRaises((ValueError, KeyError)):
            self.store.snapshots()
        (self.root / 'aggregate.json').unlink()
        with self.assertRaises(ValueError):
            self.store.snapshots()

    def test_boundary_and_scheduler_persist(self):
        expired = self.write(2, self.day - timedelta(days=7))
        boundary = self.write(4, self.day - timedelta(days=6))
        self.assertEqual(len(self.store.snapshots()), 1)
        self.assertFalse(expired.exists())
        self.assertTrue(boundary.exists())
        self.assertTrue(self.store.claim_round(100, 1000))
        self.assertFalse(self.store.claim_round(999, 1900))
        self.assertTrue(self.store.claim_round(1000, 1900))
        self.day += timedelta(days=1)
        self.assertEqual(self.store.snapshots(), [])
