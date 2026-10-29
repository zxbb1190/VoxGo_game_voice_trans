"""Idle/busy/paused model preparation without audio, network or native models."""
import copy
import os
from dataclasses import replace
from pathlib import Path
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt5.QtWidgets import QApplication
from voxgo.asr.pipeline import SpeechPipeline
from voxgo.asr.whisper_engine import SpeechRecognizer, WhisperConfig
from voxgo.audio.capture import SpeechSegment
from voxgo.config.loader import default_app_config
from voxgo.i18n import UI_LANGUAGE_OPTIONS
from voxgo.languages import ONLINE_DIRECTIONS, LOCAL_DIRECTIONS
from voxgo.runtime.events import EventBus
from voxgo.runtime.work_items import SpeechWorkItem, LatencyTrace
from voxgo.translation import TranslationConfig
from voxgo.ui.config_models import _translation_language_notice
from voxgo.ui.overlay_window import GameOverlay


class EagerModelPreparationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = default_app_config()
        self.stats = {'speech_detected': 0, 'filtered_speech': 0, 'dropped_speech': 0, 'errors': 0}
        self.notify = Mock()

    def recognizer(self, callback=None):
        return SpeechRecognizer(WhisperConfig(model_size='base', active_model_size='base',
            model_dir=self.tmp.name, local_files_only=True), callback)

    def pipeline(self, recognizer, paused=False, revision=0):
        pipeline = SpeechPipeline(lambda: self.config, lambda: recognizer, EventBus(), self.stats,
            lambda: True, lambda: paused, lambda: 'fixture', {}, self.notify,
            language_revision_getter=lambda: revision)
        self.addCleanup(pipeline.stop)
        return pipeline

    @staticmethod
    def native():
        return SimpleNamespace(model=SimpleNamespace(is_multilingual=True), transcribe=Mock())

    def test_idle_and_paused_worker_load_without_any_audio(self):
        for paused in (False, True):
            with self.subTest(paused=paused):
                ready = threading.Event()
                threads = []
                r = self.recognizer(lambda p: ready.set() if p.status == 'ready' else None)
                p = self.pipeline(r, paused=paused)
                r.request_config(replace(r.config, active_model_size='small'))
                p.request_model_preparation()
                self.assertEqual(p._queue.qsize(), 0)

                def load(*args, **kwargs):
                    threads.append(threading.current_thread().name)
                    return self.native()

                with patch('voxgo.asr.whisper_engine.WhisperModel', side_effect=load) as native:
                    p.start()
                    self.assertTrue(ready.wait(3))
                    self.assertTrue(p.stop())
                self.assertEqual(threads, ['speech-worker'])
                self.assertEqual(r._loaded_model_size, 'small')
                self.assertEqual(self.stats['speech_detected'], 0)
                self.assertEqual(self.stats['errors'], 0)
                native.assert_called_once()

    def test_prepare_waits_for_active_inference_and_never_unloads_on_gui_thread(self):
        entered, release, ready = threading.Event(), threading.Event(), threading.Event()
        r = self.recognizer(lambda item: ready.set() if item.status == 'ready' else None)
        r._initialized = True
        r._loaded_model_size = 'base'
        p = self.pipeline(r)
        order = []

        def inference(_):
            with p._processing_lock:
                order.append('inference-start')
                entered.set()
                if not release.wait(3):
                    raise RuntimeError('fixture inference not released')
                order.append('inference-end')

        def load(*args, **kwargs):
            self.assertEqual(order[-1], 'inference-end')
            self.assertEqual(threading.current_thread().name, 'speech-worker')
            order.append('load-small')
            return self.native()

        with patch.object(p, '_process', side_effect=inference), \
                patch.object(r, 'cleanup', wraps=r.cleanup) as cleanup, \
                patch('voxgo.asr.whisper_engine.WhisperModel', side_effect=load):
            try:
                p.start()
                p._queue.put(object())  # Occupy the worker in the controlled inference fixture.
                self.assertTrue(entered.wait(3))
                r.request_config(replace(r.config, active_model_size='small'))
                p.request_model_preparation()
                cleanup.assert_not_called()
                self.assertFalse(ready.is_set())
                release.set()
                self.assertTrue(ready.wait(3))
            finally:
                release.set()
                p.stop()
        self.assertEqual(order, ['inference-start', 'inference-end', 'load-small'])

    def test_multiple_waiting_requests_coalesce_to_latest_model(self):
        ready = threading.Event()
        r = self.recognizer(lambda item: ready.set() if item.status == 'ready' else None)
        p = self.pipeline(r)
        for model in ('small', 'base', 'small', 'base'):
            r.request_config(replace(r.config, active_model_size=model))
            p.request_model_preparation()
        with patch('voxgo.asr.whisper_engine.WhisperModel', return_value=self.native()) as load:
            p.start()
            self.assertTrue(ready.wait(3))
            self.assertTrue(p.stop())
        self.assertEqual(load.call_count, 1)
        self.assertEqual(load.call_args.args[0], 'base')

    def test_request_arriving_during_load_is_applied_next_without_parallel_loading(self):
        entered, release, ready = threading.Event(), threading.Event(), threading.Event()
        calls = []
        r = self.recognizer(lambda item: ready.set() if item.status == 'ready' and item.model_name == 'base' else None)
        p = self.pipeline(r)

        def load(model, **kwargs):
            calls.append(model)
            if model == 'small':
                entered.set()
                if not release.wait(3):
                    raise RuntimeError('fixture loader not released')
            return self.native()

        with patch('voxgo.asr.whisper_engine.WhisperModel', side_effect=load):
            try:
                r.request_config(replace(r.config, active_model_size='small'))
                p.request_model_preparation()
                p.start()
                self.assertTrue(entered.wait(3))
                r.request_config(replace(r.config, active_model_size='base'))
                p.request_model_preparation()
                release.set()
                self.assertTrue(ready.wait(3))
            finally:
                release.set()
                p.stop()
        self.assertEqual(calls, ['small', 'base'])
        self.assertEqual(r._loaded_model_size, 'base')

    def test_failure_does_not_kill_worker_or_retry_without_another_request(self):
        failed, ready = threading.Event(), threading.Event()
        r = self.recognizer()
        p = self.pipeline(r)
        self.notify.side_effect = lambda *args: failed.set()
        calls = []

        def load():
            calls.append(r._effective_model_size())
            if len(calls) == 1:
                raise RuntimeError('fixture load failure')
            ready.set()

        with patch.object(r, 'initialize', side_effect=load):
            r.request_config(replace(r.config, active_model_size='small'))
            p.request_model_preparation()
            p.start()
            self.assertTrue(failed.wait(3))
            self.assertTrue(p._worker_thread.is_alive())
            self.assertEqual(calls, ['small'])
            r.request_config(replace(r.config, active_model_size='base'))
            p.request_model_preparation()
            self.assertTrue(ready.wait(3))
            self.assertTrue(p.stop())
        self.assertEqual(calls, ['small', 'base'])
        self.assertEqual(self.stats['errors'], 1)

    def test_stop_prevents_queued_model_switch_after_current_load(self):
        entered, release = threading.Event(), threading.Event()
        r = self.recognizer()
        p = self.pipeline(r)
        calls, stopped = [], []

        def load(model, **kwargs):
            calls.append(model)
            entered.set()
            if not release.wait(3):
                raise RuntimeError('fixture loader not released')
            return self.native()

        with patch('voxgo.asr.whisper_engine.WhisperModel', side_effect=load):
            try:
                r.request_config(replace(r.config, active_model_size='small'))
                p.request_model_preparation()
                p.start()
                self.assertTrue(entered.wait(3))
                r.request_config(replace(r.config, active_model_size='base'))
                p.request_model_preparation()
                stopper = threading.Thread(target=lambda: stopped.append(p.stop()))
                stopper.start()
                self.assertTrue(p._stop_requested.wait(1))
                release.set()
                stopper.join(3)
                self.assertFalse(stopper.is_alive())
            finally:
                release.set()
                p.stop()
        self.assertEqual(calls, ['small'])
        self.assertEqual(stopped, [True])

    def test_unchanged_native_settings_do_not_reload_model(self):
        applied = threading.Event()
        r = self.recognizer()
        r._initialized = True
        r._loaded_model_size = 'base'
        r._model = self.native()
        p = self.pipeline(r)
        original = r.prepare_pending_config

        def prepare():
            result = original()
            applied.set()
            return result

        with patch.object(r, 'prepare_pending_config', side_effect=prepare), \
                patch('voxgo.asr.whisper_engine.WhisperModel') as native:
            r.request_config(replace(r.config, source_language='ko', beam_size=3))
            p.request_model_preparation()
            p.start()
            self.assertTrue(applied.wait(3))
            self.assertTrue(p.stop())
        native.assert_not_called()
        self.assertEqual(r.config.source_language, 'ko')

    def test_stop_then_restart_does_not_leave_an_old_stop_marker(self):
        ready = threading.Event()
        r = self.recognizer(lambda item: ready.set() if item.status == 'ready' else None)
        p = self.pipeline(r)
        with patch('voxgo.asr.whisper_engine.WhisperModel', return_value=self.native()) as load:
            for model in ('small', 'base'):
                ready.clear()
                r.request_config(replace(r.config, active_model_size=model))
                p.request_model_preparation()
                p.start()
                self.assertTrue(ready.wait(3))
                self.assertTrue(p.stop())
                self.assertTrue(p._queue.empty())
        self.assertEqual([call.args[0] for call in load.call_args_list], ['small', 'base'])

    def test_old_snapshot_does_not_consume_new_pending_settings(self):
        r = self.recognizer()
        before = copy.deepcopy(r.config)
        r.request_config(replace(before, active_model_size='small'))
        r._apply_pending_config(before)
        self.assertEqual(r._effective_model_size(), 'base')
        with patch.object(r, 'initialize'):
            self.assertTrue(r.prepare_pending_config())
        self.assertEqual(r._effective_model_size(), 'small')

    def test_failed_old_model_path_is_cleared_before_new_offline_load(self):
        r = self.recognizer()
        r._model_path = str(Path(self.tmp.name) / 'old-model')
        r.request_config(replace(r.config, active_model_size='small'))
        with patch.object(r, 'initialize'):
            r.prepare_pending_config()
        self.assertIsNone(r._model_path)

    def test_stale_queued_audio_cannot_reload_previous_model(self):
        r = Mock()
        p = self.pipeline(r, revision=2)
        segment = SpeechSegment(b'\0\0' * 16000, 16000, 1.0, 1.0, 5, 5, -10.0, -45.0, -60.0, 'fixture')
        p._process(SpeechWorkItem(segment, LatencyTrace('fixture', 1, 1),
            source_lang='en', target_lang='zh', whisper_language='auto', language_revision=1))
        r.transcribe_audio_bytes_with_language.assert_not_called()
        self.assertEqual(self.stats['dropped_speech'], 1)


class ApiLanguageNoticeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def test_online_providers_hide_api_requirement_for_all_supported_directions(self):
        for provider in ('google', 'openai_compatible'):
            for source, target in ONLINE_DIRECTIONS:
                for language, _ in UI_LANGUAGE_OPTIONS:
                    with self.subTest(provider=provider, source=source, target=target, locale=language):
                        config = TranslationConfig(provider=provider, source_lang=source, target_lang=target)
                        self.assertEqual(_translation_language_notice(config, language), '')

    def test_offline_unsupported_directions_keep_notice_and_never_change_provider(self):
        for source, target in ONLINE_DIRECTIONS:
            config = TranslationConfig(provider='local', source_lang=source, target_lang=target)
            notice = _translation_language_notice(config, 'en-US')
            self.assertEqual(bool(notice), (source, target) not in LOCAL_DIRECTIONS)
            self.assertEqual(config.provider, 'local')

    def test_switching_provider_hides_and_restores_banner(self):
        config = TranslationConfig(provider='local', source_lang='ko', target_lang='zh')
        overlay = GameOverlay(translation_config=config)
        try:
            self.assertFalse(overlay._language_notice.isHidden())
            config.provider = 'openai_compatible'
            overlay.refresh_translation_mode()
            self.assertTrue(overlay._language_notice.isHidden())
            config.provider = 'local'
            overlay.refresh_translation_mode()
            self.assertFalse(overlay._language_notice.isHidden())
            self.assertIn('API Key', overlay._language_notice.text())
        finally:
            overlay.close()


if __name__ == '__main__':
    unittest.main()
