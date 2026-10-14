import asyncio
import hashlib
import json
import queue
import tempfile
import threading
import unittest
import uuid
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import aiohttp

from tests import test_asr_diagnostics as asr_helpers
from tests import test_capture_speech_reentry as capture_helpers
from voxgo.analytics.aggregation import AggregateStore
from voxgo.analytics.client import AuthorizedAnalytics, LocalAnalytics
from voxgo.analytics.daily_metrics import (API_FAILURE_REASONS, ASR_MODES, CLASSIFIED_COUNTERS,
                                           DailyMetrics, METRICS)
from voxgo.analytics.storage import DailySnapshotStore
from voxgo.runtime.events import EventBus
from voxgo.translation.base import TranslationConfig, TranslationRequest, TranslationResult
from voxgo.translation.failures import classify_api_failure
from voxgo.translation.google import GoogleCloudProvider
from voxgo.translation.openai_compatible import OpenAICompatibleProvider
from voxgo.translation.runtime import TranslationRuntime


def fixture_metrics(metrics):
    """Synthetic mixed-history day, produced through the real collector contract."""
    metrics.asr_segment(700, mode=None)  # Historical unclassified segment.
    for i, mode in enumerate(ASR_MODES):
        metrics.asr_segment(1000 + i * 500, i % 2 == 0, i % 2 == 1, mode)
    # Historical failures keep their old counters without inferred categories.
    metrics.increment('translation_failed', 3)
    metrics.increment('api_translation_failed', 3)
    for provider in ('google', 'openai_compatible'):
        for reason in API_FAILURE_REASONS:
            metrics.translation_result(False, 501, 'api', reason, provider)
    metrics.translation_result(True, 120, 'api')
    metrics.translation_result(True, 10, 'offline')


class ClassifiedDiagnosticsTests(unittest.TestCase):
    def test_all_modes_atomic_rollover_and_unknown_remains_unclassified(self):
        with tempfile.TemporaryDirectory() as root:
            day = date(2026, 10, 13)
            store = DailySnapshotStore(root, today=lambda: day)
            metrics = DailyMetrics(store, '0.5.3-dev')
            for mode in ASR_MODES:
                metrics.asr_segment(499.8, True, True, mode)
            metrics.asr_segment(1000, mode='private-mode')
            day += timedelta(days=1)
            metrics.asr_segment(2000, mode='accurate')
            metrics.flush()
            first = store.load('2026-10-13')['metrics']
            self.assertEqual(first['asr_segments'], 5)
            for mode in ASR_MODES:
                self.assertEqual(first[f'asr_{mode}_segments'], 1)
                self.assertEqual(first[f'asr_{mode}_forced_max_duration_splits'], 1)
                self.assertEqual(first[f'asr_{mode}_short_fragment_segments'], 1)
                self.assertEqual(first[f'asr_{mode}_segment_duration_sum_ms'], 500)
            second = store.load('2026-10-14')['metrics']
            self.assertEqual(second['asr_accurate_segments'], 1)
            self.assertNotIn('asr_fast_segments', second)
            self.assertNotIn('private', json.dumps(first))

    def test_capture_emission_pins_custom_before_callback_changes_settings(self):
        helper = capture_helpers.CaptureSpeechReentryTest()
        capture = helper.make_capture(latency_mode='custom')
        self.addCleanup(helper.doCleanups)
        seen = []
        def callback(segment):
            capture.config.latency_mode = 'accurate'
            seen.append(segment)
        capture._on_speech_callback = callback
        capture._speech_buffer = [helper.block(5800)]
        capture._speech_buffer_samples = helper.BLOCK_SAMPLES
        segment = capture._emit_speech_buffer('synthetic test')
        self.assertEqual(segment.latency_mode, 'custom')
        self.assertEqual(seen[0].latency_mode, 'custom')

    def test_pipeline_uses_capture_mode_not_current_policy_or_last_daily_setting(self):
        helper = asr_helpers.AsrDiagnosticsTests()
        callback = Mock()
        pipeline, _, _ = helper.pipeline(callback=callback)
        config = pipeline._config_getter()
        segment = helper.strong_segment()
        segment.latency_mode = 'custom'
        config.audio.latency_mode = 'accurate'
        pipeline.on_speech_detected(segment)
        callback.assert_called_once_with('asr_segment', 2000.0, False, False, 'custom')
        for mode in ASR_MODES:
            config.audio.latency_mode = mode
            pipeline.on_speech_detected(helper.strong_segment())
            self.assertEqual(callback.call_args.args[-1], mode)

    def test_queue_and_epoch_keep_each_classified_event_whole(self):
        def collector():
            result = LocalAnalytics.__new__(LocalAnalytics)
            result._stopped = threading.Event()
            result._queue = queue.Queue(maxsize=1)
            return result
        analytics = AuthorizedAnalytics.__new__(AuthorizedAnalytics)
        analytics._lock = threading.RLock()
        analytics._stopping = False
        analytics.local, analytics.remote = collector(), collector()
        analytics.refresh_consent = Mock()
        analytics.asr_segment(400, True, True, 'custom')
        analytics.translation_result(False, 500, 'api', 'timeout', 'google')
        # The saturated queue accepts or drops the entire event in each channel.
        self.assertEqual(analytics.local._queue.get_nowait(),
                         ('asr_segment', 400, True, True, 'custom'))
        self.assertEqual(analytics.remote._queue.get_nowait(),
                         ('asr_segment', 400, True, True, 'custom'))
        analytics.remote = None
        analytics.translation_result(False, 500, 'api', 'timeout', 'google')
        self.assertEqual(analytics.local._queue.get_nowait(),
                         ('translation_result', False, 500, 'api', 'timeout', 'google'))

    def test_35_field_pending_hash_and_watermarks_survive_classification_upgrade(self):
        with tempfile.TemporaryDirectory() as root:
            day = date(2026, 10, 13)
            store = AggregateStore(root, '0.5.3-dev', today=lambda: day)
            shard = Path(root) / 'shards' / str(uuid.uuid4()) / (str(day) + '.json')
            shard.parent.mkdir(parents=True)
            old_metrics = {'asr_segments': 10, 'asr_segment_duration_samples': 10,
                           'asr_segment_duration_sum_ms': 20000,
                           'translation_failed': 5, 'api_translation_failed': 5}
            shard.write_text(json.dumps(dict(schema_version=2, date=str(day), metrics=old_metrics)))
            store.snapshots()
            state = store._load()
            entry = state['days'][str(day)]
            for values in [entry['totals'], entry['pending']['metrics'], *entry['seen'].values()]:
                for key in CLASSIFIED_COUNTERS:
                    values.pop(key, None)
            pending = entry['pending']
            pending.pop('snapshot_id')
            pending['snapshot_id'] = hashlib.sha256(json.dumps(
                pending, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            self.assertEqual(len(pending['metrics']), 35)
            store._save(state)
            self.assertEqual(store.snapshots(), [pending])
            self.assertEqual(store.snapshots(), [pending])
            old_metrics.update(asr_segments=11, asr_segment_duration_samples=11,
                               asr_segment_duration_sum_ms=21000, asr_fast_segments=1,
                               asr_fast_segment_duration_samples=1, asr_fast_segment_duration_sum_ms=1000,
                               translation_failed=6, api_translation_failed=6,
                               api_translation_failed_timeout=1, api_translation_failed_google=1)
            shard.write_text(json.dumps(dict(schema_version=2, date=str(day), metrics=old_metrics)))
            new = store.snapshots()[0]
            self.assertEqual(len(new['metrics']), 63)
            self.assertEqual(new['metrics']['asr_fast_segments'], 1)
            self.assertEqual(new['metrics']['asr_segments'], 11)
            self.assertEqual(new['metrics']['api_translation_failed_other'], 0)
            self.assertEqual(new['metrics']['api_translation_failed_timeout'], 1)
            self.assertFalse(store.acknowledge(pending))
            self.assertEqual(store.snapshots(), [new])
            self.assertTrue(store.acknowledge(new))
            self.assertEqual(store.snapshots(), [])

    def test_shared_fixture_uses_real_client_fields_and_hash(self):
        fixture = json.loads((Path(__file__).parent / 'fixtures/telemetry-v2-classified.json').read_text())
        with tempfile.TemporaryDirectory() as root:
            metrics = DailyMetrics(DailySnapshotStore(root), '0.5.3-dev')
            fixture_metrics(metrics)
            actual = dict.fromkeys(sorted(METRICS), 0)
            actual.update(metrics.snapshot_copy()['metrics'])
        self.assertEqual(fixture['metrics'], actual)
        unsigned = {k: v for k, v in fixture.items() if k != 'snapshot_id'}
        self.assertEqual(hashlib.sha256(json.dumps(unsigned, sort_keys=True,
                         separators=(',', ':')).encode()).hexdigest(), fixture['snapshot_id'])


class ClassifiedTranslationTests(unittest.IsolatedAsyncioTestCase):
    async def test_each_provider_classifies_transport_status_empty_and_other(self):
        request = TranslationRequest('private speech', 'en', 'zh')
        for provider_type in (GoogleCloudProvider, OpenAICompatibleProvider):
            for category in API_FAILURE_REASONS:
                with self.subTest(provider=provider_type.name, category=category):
                    response = Mock()
                    response.status = {'rate_limit': 429, 'http_error': 503}.get(category, 200)
                    async def enter(*args):
                        if category == 'timeout':
                            raise asyncio.TimeoutError('private endpoint')
                        if category == 'network':
                            raise aiohttp.ClientConnectionError('private endpoint')
                        if category == 'other':
                            raise ValueError('private body')
                        return response
                    async def leave(*args):
                        return False
                    async def body():
                        return {'data': {'translations': []}, 'choices': [{'message': {'content': ''}}]}
                    async def text():
                        return 'private error body'
                    response.__aenter__ = enter
                    response.__aexit__ = leave
                    response.json = body
                    response.text = text
                    session = SimpleNamespace(post=lambda *args, **kwargs: response)
                    provider = provider_type(TranslationConfig(api_key='synthetic'))
                    result = await provider.translate(request, session)
                    self.assertEqual(result.failure_reason, category)
        self.assertEqual(classify_api_failure(ValueError('timeout 429 network')), 'other')
        self.assertEqual(classify_api_failure(OSError('local disk')), 'other')

    async def test_inflight_failure_pins_provider_and_normalizes_unknown_reason(self):
        with tempfile.TemporaryDirectory() as root:
            collector = LocalAnalytics(root, '0.5.3-dev')
            runtime = TranslationRuntime(EventBus(), {'errors': 0}, {}, lambda: None)
            runtime.analytics = collector
            async def translate(text, detected, config):
                runtime.client.config = TranslationConfig(provider='local')
                await asyncio.sleep(0)
                return TranslationResult('[翻译失败] private error body', 'en', 'zh', config.provider,
                                         failure_reason='private invalid reason')
            runtime.client = SimpleNamespace(config=TranslationConfig(provider='google'),
                                             translate_result_with_config=translate)
            await runtime._translate_and_publish('x', 'private speech', 'en')
            collector.stop()
            collector._thread.join(3)
            content = next((Path(root) / 'analytics').rglob('*.json')).read_text()
            values = json.loads(content)['metrics']
            self.assertEqual(values['api_translation_failed_google'], 1)
            self.assertEqual(values['api_translation_failed_other'], 1)
            self.assertEqual(values['api_translation_failed'], 1)
            self.assertNotIn('private', content)

    async def test_cancel_stale_exception_shutdown_and_cache_excluded(self):
        runtime = TranslationRuntime(EventBus(), {'errors': 0}, {}, lambda: None)
        runtime.analytics = Mock()
        current_revision = [1]
        runtime.set_language_revision_getter(lambda: current_revision[0])
        async def stale(*args):
            current_revision[0] = 2
            raise aiohttp.ClientConnectionError('private')
        runtime.client = SimpleNamespace(config=TranslationConfig(provider='google'),
                                         translate_result_with_config=stale)
        await runtime._translate_and_publish('x', 'private speech', 'en', language_revision=1)
        runtime.analytics.translation_result.assert_not_called()
        async def cancelled(*args):
            raise asyncio.CancelledError()
        runtime.client.translate_result_with_config = cancelled
        with self.assertRaises(asyncio.CancelledError):
            await runtime._translate_and_publish('x', 'private speech', 'en')
        runtime.analytics.translation_result.assert_not_called()
        async def cached(*args):
            return TranslationResult('[翻译失败] synthetic', 'en', 'zh', 'local_cache')
        runtime.client.translate_result_with_config = cached
        await runtime._translate_and_publish('x', 'private speech', 'en')
        runtime.analytics.translation_result.assert_called_once_with(False, unittest.mock.ANY, None)
        runtime.analytics.reset_mock()
        runtime.begin_shutdown()
        await runtime._translate_and_publish('x', 'private speech', 'en')
        runtime.analytics.translation_result.assert_not_called()
