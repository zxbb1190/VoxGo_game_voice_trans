import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

from tests.test_speech_pipeline_candidates import FakeRecognizer, _segment
from voxgo.analytics.client import AuthorizedAnalytics, LocalAnalytics
from voxgo.analytics.daily_metrics import ASR_COUNTERS, DailyMetrics
from voxgo.analytics.storage import DailySnapshotStore
from voxgo.asr.pipeline import SpeechPipeline
from voxgo.asr.whisper_engine import (SpeechRecognizer, TranscriptionResult, WhisperConfig,
                                     should_drop_transcription_result)
from voxgo.audio.capture import AudioConfig
from voxgo.config.schema import AppConfig
from voxgo.runtime.events import EventBus, TranscriptReady
from voxgo.runtime.work_items import LatencyTrace, SpeechWorkItem


class AsrDiagnosticsTests(unittest.TestCase):
    def pipeline(self, result=None, callback=None):
        config = AppConfig(audio=AudioConfig(), whisper=WhisperConfig(language='en'))
        seen = []
        bus = EventBus()
        bus.subscribe(TranscriptReady, seen.append)
        stats = {'speech_detected': 0, 'filtered_speech': 0, 'dropped_speech': 0, 'errors': 0}
        recognizer = FakeRecognizer(result=result)
        pipeline = SpeechPipeline(lambda: config, lambda: recognizer, bus, stats,
                                  lambda: True, lambda: False, lambda: 'id', {},
                                  lambda *args: None, diagnostics_callback=callback)
        return pipeline, stats, seen

    @staticmethod
    def strong_segment(**overrides):
        values = dict(duration_seconds=2.0, voice_duration_seconds=1.4,
                      block_count=10, voice_blocks=7, vad_voice_blocks=7,
                      vad_confidence=0.7, peak_rms_dbfs=-20.0)
        values.update(overrides)
        return _segment(**values)

    def test_capture_metrics_count_before_merge_without_contents(self):
        callback = Mock()
        pipeline, _, _ = self.pipeline(callback=callback)
        pipeline.on_speech_detected(_segment(reason='达到最长 2.5s'))
        pipeline.on_speech_detected(_segment(reason='private game name'))
        self.assertEqual(callback.call_args_list, [
            unittest.mock.call('asr_segment', 400.0, True, True),
            unittest.mock.call('asr_segment', 400.0, False, True),
        ])
        self.assertNotIn('private game name', str(callback.mock_calls))
        self.assertEqual(pipeline._queue.qsize(), 1)

    def test_runaway_counter_is_subset_of_post_filter(self):
        callback = Mock()
        result = TranscriptionResult('', 'en', .95, runaway_guarded=True,
                                     raw_text='private text ' * 40)
        pipeline, stats, seen = self.pipeline(result, callback)
        pipeline._process(SpeechWorkItem(self.strong_segment(), LatencyTrace('', 1, 1)))
        self.assertEqual(stats['filtered_speech'], 1)
        self.assertFalse(seen)
        self.assertEqual(callback.call_args_list, [
            unittest.mock.call('increment', 'asr_runaway_repetition_blocks'),
            unittest.mock.call('increment', 'asr_post_filter_drops'),
        ])
        self.assertNotIn('private text', str(callback.mock_calls))

    def test_normal_repeated_callout_survives_production_pipeline(self):
        for text in ('go go go', 'Go! Go! Go!', 'push push push'):
            with self.subTest(text=text):
                callback = Mock()
                pipeline, stats, seen = self.pipeline(TranscriptionResult(text, 'en', .95), callback)
                pipeline._process(SpeechWorkItem(self.strong_segment(), LatencyTrace('', 1, 1)))
                self.assertEqual(len(seen), 1)
                self.assertEqual(stats['filtered_speech'], 0)
                callback.assert_not_called()

    def test_diagnostics_failure_cannot_break_admission_or_recognition(self):
        callback = Mock(side_effect=OSError('unavailable'))
        pipeline, stats, seen = self.pipeline(TranscriptionResult('behind you', 'en', .95), callback)
        pipeline.on_speech_detected(self.strong_segment())
        pipeline._process(pipeline._queue.get_nowait())
        self.assertEqual(len(seen), 1)
        self.assertEqual(stats['errors'], 0)

    def test_repeated_callout_exemption_preserves_existing_other_guards(self):
        result = TranscriptionResult('Go! Go! Go!', 'en', .95, no_speech_prob=.7)
        self.assertEqual(should_drop_transcription_result(result), '')
        self.assertEqual(should_drop_transcription_result(result, recent_texts=['go go go']),
                         '短时间重复识别文本')
        result.language_probability = .1
        self.assertIn('语言置信度', should_drop_transcription_result(result, expected_language='en'))

    def test_budget_drop_counts_weak_candidate_once(self):
        callback = Mock()
        pipeline, stats, _ = self.pipeline(callback=callback)
        item = SpeechWorkItem(_segment(), LatencyTrace('', 1, 1), short_segment=True)
        with patch.object(pipeline, '_should_drop_weak_for_inference_budget', return_value=True):
            pipeline._enqueue_with_backpressure(item, pipeline._mode_policy(AppConfig()))
        self.assertEqual(stats['dropped_speech'], 1)
        callback.assert_called_once_with('increment', 'asr_weak_candidate_drops')

    def test_empty_asr_counts_post_filter_without_runaway(self):
        callback = Mock()
        pipeline, _, seen = self.pipeline(TranscriptionResult('', 'en', .95), callback)
        pipeline._process(SpeechWorkItem(self.strong_segment(), LatencyTrace('', 1, 1)))
        self.assertFalse(seen)
        callback.assert_called_once_with('increment', 'asr_post_filter_drops')

    def test_segment_daily_transaction_validation_and_rollover(self):
        with tempfile.TemporaryDirectory() as root:
            day = date(2026, 9, 30)
            store = DailySnapshotStore(root, today=lambda: day)
            metrics = DailyMetrics(store, '0.5.2')
            with patch.object(store, 'save', wraps=store.save) as save:
                self.assertTrue(metrics.asr_segment(2500.4, True, False))
                for invalid in (-1, float('nan'), float('inf'), True, 'secret'):
                    self.assertFalse(metrics.asr_segment(invalid))
                save.assert_not_called()
                day += timedelta(days=1)
                metrics.asr_segment(400, False, True)
                metrics.flush()
            first = store.load('2026-09-30')['metrics']
            second = store.load('2026-10-01')['metrics']
            self.assertEqual(first['asr_segments'], 1)
            self.assertEqual(first['asr_segment_duration_sum_ms'], 2500)
            self.assertEqual(first['asr_forced_max_duration_splits'], 1)
            self.assertEqual(second['asr_segment_duration_samples'], 1)
            self.assertEqual(second['asr_short_fragment_segments'], 1)

    def test_local_writer_flushes_numeric_asr_snapshot(self):
        with tempfile.TemporaryDirectory() as root:
            collector = LocalAnalytics(root, '0.5.2')
            collector.asr_segment(3000, True, False)
            collector.increment('asr_post_filter_drops')
            collector.stop()
            collector._thread.join(timeout=3)
            self.assertFalse(collector._thread.is_alive())
            payload = json.loads(next((Path(root) / 'analytics').rglob('*.json')).read_text())
            self.assertEqual(payload['metrics']['asr_segments'], 1)
            self.assertEqual(payload['metrics']['asr_post_filter_drops'], 1)
            self.assertTrue(all(type(value) is int for key, value in payload['metrics'].items()
                                if key in ASR_COUNTERS))

    def test_full_disabled_creates_no_remote_collector_or_upload(self):
        with tempfile.TemporaryDirectory() as root, patch(
            'voxgo.analytics.client.LocalAnalytics'
        ) as local, patch('voxgo.analytics.uploader.RemoteUploader') as uploader:
            analytics = AuthorizedAnalytics(root, '0.5.2', lambda: SimpleNamespace(
                telemetry_consent='denied', telemetry_consent_version=3))
            analytics.asr_segment(400, False, True)
            analytics.increment('asr_post_filter_drops')
            self.assertEqual(local.call_count, 1)
            local.return_value.asr_segment.assert_called_once_with(400, False, True)
            self.assertIsNone(analytics.remote)
            uploader.assert_not_called()
            analytics.stop()

    def test_guard_failure_keeps_normal_model_result(self):
        recognizer = SpeechRecognizer(WhisperConfig())
        recognizer._model = Mock()
        recognizer._model.transcribe.return_value = (iter([SimpleNamespace(text='go go go')]),
                                                     SimpleNamespace(language='en', language_probability=.95))
        with patch('voxgo.asr.whisper_engine.is_runaway_repetition', side_effect=RuntimeError):
            result = recognizer._transcribe_audio_array(np.zeros(16000, dtype=np.float32), 'en', None)
        self.assertEqual(result.text, 'go go go')
        self.assertFalse(result.runaway_guarded)


if __name__ == '__main__':
    unittest.main()
