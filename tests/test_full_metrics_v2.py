import asyncio
import hashlib
import json
import tempfile
import unittest
import uuid
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from voxgo.analytics.daily_metrics import DailyMetrics, METRICS, V1_METRICS, BUCKETS
from voxgo.analytics.storage import DailySnapshotStore
from voxgo.analytics.aggregation import AggregateStore
from voxgo.runtime.events import EventBus
from voxgo.translation import TranslationConfig
from voxgo.translation.runtime import TranslationRuntime


class FullV2Tests(unittest.TestCase):
    def test_raw_latency_bucket_boundaries(self):
        with tempfile.TemporaryDirectory() as root:
            metrics = DailyMetrics(DailySnapshotStore(root), 'test')
            values = (0, 499, 499.9, 500, 999, 999.9, 1000, 1999, 1999.9,
                      2000, 4999, 4999.9, 5000)
            for prefix in ('asr', 'translation'):
                for value in values:
                    self.assertTrue(metrics.observe(prefix, value))
                for value in (-1, float('nan'), float('inf'), True, 3600001):
                    self.assertFalse(metrics.observe(prefix, value))
                snap = metrics.snapshot_copy()['metrics']
                self.assertEqual([snap[prefix + '_latency_' + b] for b in BUCKETS], [3, 3, 3, 3, 1])
                self.assertEqual(snap[prefix + '_latency_samples'], len(values))
                self.assertEqual(snap[prefix + '_latency_sum_ms'], sum(round(v) for v in values))

    def test_v1_pending_exact_until_real_delta_then_v2(self):
        with tempfile.TemporaryDirectory() as root:
            day = date.today()
            store = AggregateStore(root, 'new', today=lambda: day)
            shard = Path(root) / 'shards' / str(uuid.uuid4()) / (str(day) + '.json')
            shard.parent.mkdir(parents=True)
            shard.write_text(json.dumps(dict(schema_version=1, date=str(day), metrics={'translation_success': 4})))
            store.snapshots()
            state = store._load()
            entry = state['days'][str(day)]
            for m in (entry['totals'], *entry['seen'].values(), entry['pending']['metrics']):
                for k in set(m) - V1_METRICS:
                    del m[k]
            old = entry['pending']
            old['schema_version'] = 1
            old.pop('snapshot_id')
            old['snapshot_id'] = hashlib.sha256(json.dumps(old, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            store._save(state)
            self.assertEqual(store.snapshots(), [old])
            self.assertEqual(store.snapshots(), [old])
            self.assertEqual(set(store._load()['days'][str(day)]['totals']), METRICS)
            shard.write_text(json.dumps(dict(schema_version=2, date=str(day), metrics={
                'translation_success': 5, 'api_translation_success': 1})))
            new = store.snapshots()[0]
            self.assertEqual(new['schema_version'], 2)
            self.assertEqual(new['revision'], old['revision'] + 1)
            self.assertEqual(new['metrics']['translation_success'], 5)
            self.assertEqual(new['metrics']['api_translation_success'], 1)
            self.assertFalse(store.acknowledge(old))
            # A stale v1 writer cannot lower or recount any v2 baseline.
            shard.write_text(json.dumps(dict(schema_version=1, date=str(day), metrics={'translation_success': 4})))
            self.assertEqual(store.snapshots(), [new])
            self.assertTrue(store.acknowledge(new))
            self.assertEqual(store.snapshots(), [])
            with self.assertRaises(ValueError):
                store._metrics({'unknown_field': 1})

    def test_modes_are_task_snapshots_even_after_switch(self):
        for provider, category in (('local', 'offline'), ('google', 'api'), ('openai_compatible', 'api')):
            for fail in (False, True):
                with self.subTest(provider=provider, fail=fail):
                    runtime = TranslationRuntime(EventBus(), {'errors': 0}, {}, lambda: None)
                    runtime.analytics = Mock()
                    async def translate(text, detected, config):
                        runtime.client.config = TranslationConfig(provider='local' if provider != 'local' else 'google')
                        await asyncio.sleep(0)
                        if fail:
                            raise RuntimeError('failed')
                        return SimpleNamespace(translated='translated', source_lang='en', target_lang='zh', provider=provider)
                    runtime.client = SimpleNamespace(config=TranslationConfig(provider=provider), translate_result_with_config=translate)
                    asyncio.run(runtime._translate_and_publish('x', 'sentence', 'en'))
                    result = 'failed' if fail else 'success'
                    runtime.analytics.translation_result.assert_called_once()
                    args = runtime.analytics.translation_result.call_args.args
                    self.assertEqual((args[0], args[2]), (not fail, category))

    def test_cache_unknown_and_cancel_are_not_misclassified(self):
        for provider, result_provider in (('google', 'local_cache'), ('unknown', 'unknown')):
            runtime = TranslationRuntime(EventBus(), {'errors': 0}, {}, lambda: None)
            runtime.analytics = Mock()
            async def translate(*args):
                return SimpleNamespace(translated='translated', source_lang='en', target_lang='zh', provider=result_provider)
            runtime.client = SimpleNamespace(config=TranslationConfig(provider=provider), translate_result_with_config=translate)
            asyncio.run(runtime._translate_and_publish('x', 'sentence', 'en'))
            runtime.analytics.translation_result.assert_called_once()
            self.assertEqual(runtime.analytics.translation_result.call_args.args[::2], (True, None))
        async def cancelled(*args):
            raise asyncio.CancelledError()
        runtime.client.translate_result_with_config = cancelled
        runtime.analytics.reset_mock()
        with self.assertRaises(asyncio.CancelledError):
            asyncio.run(runtime._translate_and_publish('x', 'sentence', 'en'))
        runtime.analytics.translation_result.assert_not_called()

    def test_legacy_shard_load_and_unknown_metric_rejection(self):
        with tempfile.TemporaryDirectory() as root:
            store = DailySnapshotStore(root)
            day = store.today().isoformat()
            store.save(day, dict(schema_version=1, date=day, metrics={'translation_success': 8}))
            metrics = DailyMetrics(store, 'new')
            self.assertEqual(metrics.snapshot_copy()['metrics']['translation_success'], 8)
            self.assertFalse(metrics.increment('arbitrary_field'))
            metrics.observe('asr', 500)
            metrics.flush()
            reloaded = DailyMetrics(store, 'new')
            self.assertEqual(reloaded.snapshot_copy()['schema_version'], 2)
            self.assertEqual(reloaded.snapshot_copy()['metrics']['asr_latency_500_1000'], 1)

    def test_queue_pressure_keeps_result_components_together(self):
        import queue
        import threading
        from voxgo.analytics.client import LocalAnalytics
        collector = LocalAnalytics.__new__(LocalAnalytics)
        collector._stopped = threading.Event()
        collector._queue = queue.Queue(maxsize=1)
        with tempfile.TemporaryDirectory() as root:
            metrics = DailyMetrics(DailySnapshotStore(root), 'test')
            collector.translation_result(True, 501, 'api')
            # Saturated admission must drop the whole second result.
            collector.translation_result(False, 2001, 'offline')
            self.assertEqual(collector._queue.qsize(), 1)
            command = collector._queue.get_nowait()
            getattr(metrics, command[0])(*command[1:])
            values = metrics.snapshot_copy()['metrics']
            self.assertEqual(values['translation_success'], 1)
            self.assertEqual(values['api_translation_success'], 1)
            self.assertEqual(values['translation_latency_samples'], 1)
            self.assertEqual(values['translation_latency_500_1000'], 1)
            self.assertNotIn('translation_failed', values)
            self.assertNotIn('offline_translation_failed', values)
            # Admission after capacity returns still represents a complete event.
            collector.translation_result(False, 2001, 'offline')
            command = collector._queue.get_nowait()
            getattr(metrics, command[0])(*command[1:])
            values = metrics.snapshot_copy()['metrics']
            self.assertEqual(values['translation_failed'], values['offline_translation_failed'])
            self.assertEqual(values['translation_latency_samples'], 2)

    def test_consent_epoch_change_cannot_split_one_result(self):
        import queue
        import threading
        from voxgo.analytics.client import AuthorizedAnalytics, LocalAnalytics
        def collector():
            result = LocalAnalytics.__new__(LocalAnalytics)
            result._stopped = threading.Event()
            result._queue = queue.Queue(maxsize=1)
            return result
        authorized = AuthorizedAnalytics.__new__(AuthorizedAnalytics)
        authorized._lock = threading.RLock()
        authorized._stopping = False
        authorized.local = collector()
        old_epoch, new_epoch = collector(), collector()
        authorized.remote = old_epoch
        transitions = []
        def refresh():
            transitions.append(True)
            authorized.remote = new_epoch if len(transitions) == 1 else None
        authorized.refresh_consent = refresh
        authorized.translation_result(True, 1000, 'api')
        self.assertEqual(len(transitions), 1)
        self.assertTrue(old_epoch._queue.empty())
        self.assertEqual(new_epoch._queue.get_nowait(), ('translation_result', True, 1000, 'api'))
        authorized.translation_result(False, 1500, 'offline')
        self.assertEqual(len(transitions), 2)
        self.assertTrue(new_epoch._queue.empty())

    def test_translation_result_uses_one_day_and_one_transaction(self):
        from unittest.mock import patch
        from voxgo.analytics.daily_metrics import LIMIT
        with tempfile.TemporaryDirectory() as root:
            metrics = DailyMetrics(DailySnapshotStore(root), 'test')
            with patch.object(metrics, '_rollover', wraps=metrics._rollover) as rollover:
                metrics.translation_result(True, 500, 'offline')
                rollover.assert_called_once()
            values = metrics.snapshot_copy()['metrics']
            self.assertEqual(values['translation_success'], values['offline_translation_success'])
            self.assertEqual(values['translation_latency_samples'], 1)
            metrics.snapshot['metrics']['translation_success'] = LIMIT
            before = metrics.snapshot_copy()
            self.assertFalse(metrics.translation_result(True, 500, 'api'))
            self.assertEqual(metrics.snapshot_copy(), before)
