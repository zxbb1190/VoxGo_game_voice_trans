import asyncio
import concurrent.futures
import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock

from tests.test_runtime_services import FakeTranslator
from voxgo.runtime.events import EventBus
from voxgo.translation.runtime import TranslationRuntime
from voxgo.analytics.client import LocalAnalytics


class AnalyticsIntegrationTests(unittest.TestCase):
    def runtime(self):
        runtime = TranslationRuntime(EventBus(), {'errors': 0}, {}, lambda: None)
        runtime.client = FakeTranslator()
        runtime.analytics = Mock()
        return runtime

    def test_success_records_once_and_no_text_is_passed(self):
        runtime = self.runtime()
        asyncio.run(runtime._translate_and_publish('one', 'private speech', 'en'))
        runtime.analytics.translation_result.assert_called_once()
        success, elapsed, mode = runtime.analytics.translation_result.call_args.args
        self.assertTrue(success)
        self.assertGreaterEqual(elapsed, 0)
        self.assertEqual(mode, 'api')
        self.assertNotIn('private speech', str(runtime.analytics.mock_calls))

    def test_empty_result_counts_failure(self):
        runtime = self.runtime()
        async def empty(*args, **kwargs):
            return None
        runtime._translate_with_config_snapshot = empty
        asyncio.run(runtime._translate_and_publish('one', 'private speech', 'en'))
        runtime.analytics.translation_result.assert_called_once()
        self.assertFalse(runtime.analytics.translation_result.call_args.args[0])

    def test_error_counts_failure_but_cancel_and_shutdown_do_not(self):
        runtime = self.runtime()
        future = concurrent.futures.Future()
        future.set_exception(RuntimeError('network failed'))
        runtime._handle_task_done('one', future)
        runtime.analytics.translation_result.assert_called_once_with(False, None, None)
        runtime.analytics.reset_mock()
        cancelled = concurrent.futures.Future()
        cancelled.cancel()
        runtime._handle_task_done('two', cancelled)
        runtime.begin_shutdown()
        runtime._handle_error('three', RuntimeError('cancelled'))
        runtime.analytics.translation_result.assert_not_called()

    def test_stale_result_does_not_count(self):
        runtime = self.runtime()
        runtime.set_language_revision_getter(lambda: 2)
        asyncio.run(runtime._translate_and_publish('one', 'private speech', 'en', language_revision=1))
        runtime.analytics.translation_result.assert_not_called()

    def test_analytics_failure_cannot_break_translation(self):
        runtime = self.runtime()
        runtime.analytics.translation_result.side_effect = OSError('disk failure')
        asyncio.run(runtime._translate_and_publish('one', 'private speech', 'en'))
        self.assertEqual(runtime._stats['errors'], 0)

    def test_translation_results_reach_local_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = self.runtime()
            collector = LocalAnalytics(directory, 'test', flush_interval=0.1)
            runtime.analytics = collector
            collector.set_active(True, 'offline')
            collector.observe('asr', 35)
            asyncio.run(runtime._translate_and_publish('one', 'private speech', 'en'))
            runtime._handle_error('two', RuntimeError('secret endpoint'))
            collector.stop()
            collector._thread.join(timeout=3)
            self.assertFalse(collector._thread.is_alive())
            files = list((Path(directory) / 'analytics').rglob('*.json'))
            self.assertEqual(len(files), 1)
            content = files[0].read_text(encoding='utf-8')
            metrics = json.loads(content)['metrics']
            self.assertEqual(metrics['translation_success'], 1)
            self.assertEqual(metrics['translation_failed'], 1)
            self.assertEqual(metrics['asr_latency_sum_ms'], 35)
            self.assertEqual(metrics['offline_sessions'], 1)
            self.assertNotIn('private speech', content)
            self.assertNotIn('secret endpoint', content)
