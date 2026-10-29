"""Model switching feedback: real Qt delivery, fixture downloads, no network/model."""
import io
import os
import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication

from voxgo.app import VoxGoApp
from voxgo.asr.model_download_notice import ModelDownloadNoticeFormatter
from voxgo.asr.whisper_engine import ModelDownloadProgress, SpeechRecognizer, WhisperConfig
from voxgo.config.loader import default_app_config, migrate_runtime_defaults
from voxgo.i18n import UI_LANGUAGE_OPTIONS
from voxgo.ui.config_models import OverlayConfig
from voxgo.ui.model_preparation_status import ModelPreparationStatus
from voxgo.ui.overlay_window import GameOverlay


def progress(status, model='small', done=0, total=0):
    return ModelDownloadProgress(status, model, f'Systran/faster-whisper-{model}',
                                 'ModelScope 国内源', done, total, done / total * 100 if total else 0)


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class ModelProgressFormattingTests(unittest.TestCase):
    def setUp(self):
        self.config = default_app_config()
        self.clock = Clock()
        self.formatter = ModelDownloadNoticeFormatter(lambda: self.config, self.clock)

    def test_eta_uses_newly_transferred_bytes_not_preexisting_cache(self):
        self.formatter.record_progress(progress('checking'))
        self.formatter.record_progress(progress('downloading', done=600, total=1000))
        self.clock.now = 4
        item = progress('downloading', done=800, total=1000)
        self.formatter.record_progress(item)
        text = self.formatter.format_compact(item)
        self.assertIn('50 B/s', text)
        self.assertIn('预计剩余约 4s', text)
        self.assertIn('已用 4s', text)

    def test_stalled_progress_keeps_elapsed_and_removes_stale_eta(self):
        self.formatter.record_progress(progress('downloading', total=1000))
        self.clock.now = 4
        item = progress('downloading', done=500, total=1000)
        self.formatter.record_progress(item)
        self.assertIn('预计剩余', self.formatter.format_compact(item))
        self.clock.now = 9
        text = self.formatter.format_compact(item)
        self.assertIn('已用 9s', text)
        self.assertIn('正在估算剩余时间', text)
        self.assertNotIn('预计剩余约', text)

    def test_unknown_total_or_initial_progress_has_no_fabricated_eta(self):
        for total in (0, 1000):
            item = progress('downloading', done=50, total=total)
            formatter = ModelDownloadNoticeFormatter(lambda: self.config, self.clock)
            formatter.record_progress(item)
            self.assertNotIn('预计剩余约', formatter.format_compact(item))
        self.clock.now = 3
        item = progress('downloading', done=100)
        formatter.record_progress(item)
        self.assertNotIn('预计剩余约', formatter.format_compact(item))

    def test_model_and_retry_cycles_reset_bytes_and_ready_stops_elapsed(self):
        self.formatter.record_progress(progress('downloading', done=500, total=1000))
        self.clock.now = 5
        self.formatter.record_progress(progress('ready'))
        self.clock.now = 20
        self.assertIn('已用 5s', self.formatter.format_compact(progress('ready')))
        item = progress('checking', 'base')
        self.formatter.record_progress(item)
        self.assertEqual(self.formatter.last_download_bytes, (0, 0, 0.0))
        self.assertNotIn('500', self.formatter.format(item))
        self.formatter.record_progress(progress('error', 'base'))
        self.clock.now = 25
        self.formatter.record_progress(progress('checking', 'base'))
        self.assertIn('已用 0s', self.formatter.format_compact(progress('checking', 'base')))

    def test_per_file_progress_is_not_presented_as_whole_model_eta(self):
        self.formatter.record_progress(replace(progress('downloading', total=1000), progress_scope='file'))
        self.clock.now = 4
        item = replace(progress('downloading', done=500, total=1000), progress_scope='file')
        self.formatter.record_progress(item)
        text = self.formatter.format_compact(item)
        self.assertIn('当前文件已下载', text)
        self.assertIn('总剩余时间暂无法估算', text)
        self.assertNotIn('预计剩余约', text)

    def test_all_status_messages_follow_all_five_ui_languages(self):
        for language, _ in UI_LANGUAGE_OPTIONS:
            self.config.app.language = language
            for status in ('pending', 'checking', 'downloading', 'complete', 'loading', 'ready', 'error'):
                with self.subTest(language=language, status=status):
                    item = progress(status, done=100, total=1000)
                    self.formatter.record_progress(item)
                    text = self.formatter.format_compact(item)
                    self.assertIn('small', text)
                    if language != 'en-US':
                        for english in ('speech model', 'Elapsed', 'Estimating', 'recognition engine', 'You can'):
                            self.assertNotIn(english, text)


class ModelStatusQtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def tearDown(self):
        self.qt.processEvents()

    def overlay(self):
        overlay = GameOverlay(config=OverlayConfig(max_lines=3))
        self.addCleanup(overlay.close)
        return overlay

    def test_status_survives_subtitle_eviction_clear_and_second_model_download(self):
        overlay = self.overlay()
        overlay.set_model_preparation_progress(progress('checking', 'base'))
        for i in range(5):
            overlay.add_translation_with_id(str(i), 'fixture', 'fixture')
        overlay.clear_history()
        overlay.set_model_preparation_progress(progress('downloading', done=20, total=100))
        self.qt.processEvents()
        self.assertEqual(len(overlay._translations), 0)
        label = overlay._model_preparation_status
        self.assertFalse(label.isHidden())
        self.assertIn('正在下载识别模型：small', label.text())
        self.assertIn('20.0%', label.text())

    def test_normal_missing_subtitle_update_stays_missing(self):
        overlay = self.overlay()
        overlay.update_translation('old-language-item', 'obsolete text', copyable=True)
        self.qt.processEvents()
        self.assertEqual(len(overlay._translations), 0)
        self.assertTrue(all(button.isHidden() for button in overlay._copy_buttons))

    def test_worker_callback_is_delivered_on_gui_thread(self):
        overlay = self.overlay()
        threads = []
        formatter = overlay._model_preparation_status._formatter
        record = formatter.record_progress

        def recording(item):
            threads.append(QThread.currentThread())
            record(item)

        with patch.object(formatter, 'record_progress', side_effect=recording):
            worker = threading.Thread(target=overlay.set_model_preparation_progress, args=(progress('checking'),))
            worker.start()
            worker.join(timeout=2)
            self.assertFalse(worker.is_alive())
            self.assertEqual(threads, [])
            self.qt.processEvents()
        self.assertEqual(threads, [self.qt.thread()])
        self.assertFalse(overlay._model_preparation_status.isHidden())

    def test_elapsed_refresh_without_bytes_and_language_change_preserves_clock(self):
        config = default_app_config()
        clock = Clock()
        label = ModelPreparationStatus(lambda: config, clock=clock)
        self.addCleanup(label.stop)
        self.addCleanup(label.close)
        label.set_progress(progress('downloading', total=1000))
        clock.now = 12
        label._refresh_timer.timeout.emit()
        self.assertIn('已用 12s', label.text())
        config.app.language = 'en-US'
        label.refresh()
        self.assertIn('Elapsed 12s', label.text())

    def test_cache_ready_is_not_engine_ready_and_error_remains_visible(self):
        overlay = self.overlay()
        label = overlay._model_preparation_status
        for status in ('complete', 'loading'):
            overlay.set_model_preparation_progress(progress(status))
            self.qt.processEvents()
            self.assertIn('正在加载识别引擎', label.text())
            self.assertFalse(label._dismiss_timer.isActive())
        overlay.set_model_preparation_progress(progress('ready'))
        self.qt.processEvents()
        self.assertIn('识别模型已就绪', label.text())
        label._dismiss_timer.start(0)
        self.qt.processEvents()
        self.assertTrue(label.isHidden())
        overlay.set_model_preparation_progress(progress('error'))
        self.qt.processEvents()
        self.assertFalse(label.isHidden())
        self.assertFalse(label._dismiss_timer.isActive())

    def test_pending_does_not_replace_same_download_and_shutdown_ignores_queued_updates(self):
        overlay = self.overlay()
        label = overlay._model_preparation_status
        overlay.set_model_preparation_progress(progress('downloading', done=50, total=100))
        overlay.set_model_preparation_progress(progress('pending'))
        self.qt.processEvents()
        self.assertIn('正在下载', label.text())
        worker = threading.Thread(target=overlay.set_model_preparation_progress,
                                  args=(progress('checking', 'base'),))
        worker.start()
        worker.join(timeout=2)
        self.assertFalse(worker.is_alive())
        overlay.prepare_shutdown()
        self.qt.processEvents()
        self.assertIn('small', label.text())
        self.assertFalse(label._refresh_timer.isActive())

    def test_switching_to_uncached_model_notifies_before_next_audio(self):
        owner = VoxGoApp.__new__(VoxGoApp)
        owner.config = default_app_config()
        owner.config.translation.source_lang = 'ko'
        owner.config.audio.latency_mode = 'balanced'
        migrate_runtime_defaults(owner.config, preserve_existing_audio_tuning=False)
        owner._overlay = self.overlay()
        owner._stopping = False
        recognizer = SpeechRecognizer(WhisperConfig(active_model_size='base'))
        recognizer._loaded_model_size = 'base'
        owner._speech_recognizer = recognizer
        owner._speech_pipeline = Mock()
        owner._queue_recognizer_config()
        self.qt.processEvents()
        self.assertIn('正在切换识别模型：small', owner._overlay._model_preparation_status.text())
        self.assertEqual(recognizer._pending_config.model_size, 'small')
        self.assertFalse(recognizer._initialized)
        owner._speech_pipeline.request_model_preparation.assert_called_once_with()

    def test_old_model_completion_does_not_claim_new_selection_is_ready(self):
        overlay = self.overlay()
        label = overlay._model_preparation_status
        overlay.set_model_preparation_progress(progress('downloading', 'small', 50, 100))
        overlay.set_model_preparation_progress(progress('pending', 'base'))
        overlay.set_model_preparation_progress(progress('ready', 'small'))
        self.qt.processEvents()
        self.assertIn('正在切换识别模型：base', label.text())
        self.assertNotIn('可以继续播放语音', label.text())
        overlay.set_model_preparation_progress(progress('checking', 'base'))
        overlay.set_model_preparation_progress(progress('ready', 'base'))
        self.qt.processEvents()
        self.assertIn('识别模型已就绪：base', label.text())


class ModelPreparationLifecycleTests(unittest.TestCase):
    def test_fixture_download_then_load_and_ready_use_existing_recognizer_path(self):
        events = []
        payloads = {'config.json': b'{}', 'model.bin': b'fixture-model', 'tokenizer.json': b'{}'}
        with tempfile.TemporaryDirectory() as tmp:
            recognizer = SpeechRecognizer(WhisperConfig(model_dir=tmp), events.append)
            files = [{'Path': name, 'Size': len(data)} for name, data in payloads.items()]

            def load(*args, **kwargs):
                self.assertEqual(events[-1].status, 'loading')
                self.assertFalse(recognizer._initialized)
                return SimpleNamespace(model=SimpleNamespace(is_multilingual=True))

            def response(request, **kwargs):
                return io.BytesIO(payloads[request.full_url.rsplit('/', 1)[-1]])

            with patch.object(recognizer, '_use_local_huggingface_snapshot', return_value=False), \
                    patch.object(recognizer, '_modelscope_model_files', return_value=files), \
                    patch.object(recognizer, '_model_load_candidates', return_value=[('cpu', 'int8')]), \
                    patch('voxgo.asr.whisper_engine.urlopen', side_effect=response), \
                    patch('voxgo.asr.whisper_engine.WhisperModel', side_effect=load):
                recognizer.initialize()
            statuses = [event.status for event in events]
            self.assertEqual(statuses[0], 'checking')
            self.assertIn('downloading', statuses)
            self.assertEqual(statuses[-3:], ['complete', 'loading', 'ready'])
            self.assertTrue(recognizer._initialized)
            self.assertEqual(events[-3].downloaded_bytes, sum(map(len, payloads.values())))

    def test_cached_offline_model_still_shows_loading_and_load_error_never_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            events = []
            recognizer = SpeechRecognizer(WhisperConfig(model_dir=tmp, local_files_only=True), events.append)
            with patch.object(recognizer, '_model_load_candidates', return_value=[('cpu', 'int8')]), \
                    patch('voxgo.asr.whisper_engine.WhisperModel', side_effect=RuntimeError('fixture load failure')), \
                    patch('voxgo.asr.whisper_engine.urlopen') as network:
                with self.assertRaisesRegex(RuntimeError, 'Whisper 模型加载失败'):
                    recognizer.initialize()
            network.assert_not_called()
            self.assertEqual([event.status for event in events], ['loading', 'error'])
            self.assertFalse(recognizer._initialized)

    def test_broken_status_callback_does_not_fail_loaded_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            callback = Mock(side_effect=RuntimeError('fixture UI failure'))
            recognizer = SpeechRecognizer(WhisperConfig(model_dir=tmp, local_files_only=True), callback)
            with patch.object(recognizer, '_model_load_candidates', return_value=[('cpu', 'int8')]), \
                    patch('voxgo.asr.whisper_engine.WhisperModel', return_value=SimpleNamespace()):
                recognizer.initialize()
            self.assertTrue(recognizer._initialized)
            self.assertEqual([call.args[0].status for call in callback.call_args_list], ['loading', 'ready'])


if __name__ == '__main__':
    unittest.main()
