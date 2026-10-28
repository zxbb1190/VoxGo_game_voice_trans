"""Exercise the real startup continuation and Qt timer without audio/models/API."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PyQt5.QtCore import QEventLoop, QTimer
from PyQt5.QtWidgets import QApplication
from voxgo.app import VoxGoApp
from voxgo.config.loader import default_app_config
from voxgo.i18n import UI_LANGUAGE_OPTIONS, language_label
from voxgo.languages import ONLINE_DIRECTIONS


class BackendStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt=QApplication.instance() or QApplication([])

    def owner(self,source='en',target='zh',language='zh-CN'):
        owner=VoxGoApp.__new__(VoxGoApp)
        owner.config=default_app_config()
        owner.config.translation.source_lang=source;owner.config.translation.target_lang=target
        owner.config.app.language=language
        owner._stopping=False;owner._running=False;owner._paused=False;owner._audio_timer=None
        owner._setup_hotkeys=Mock();owner._start_speech_worker=Mock()
        owner._start_audio_capture=Mock();owner._notify_user=Mock()
        owner._sync_analytics_activity=Mock()
        owner._audio=SimpleNamespace(process_tick=Mock())
        owner._mobile=SimpleNamespace(get_mobile_url=lambda:'http://127.0.0.1:19662/mobile')
        self.addCleanup(self.stop_timer,owner)
        return owner

    def stop_timer(self,owner):
        if owner._audio_timer:
            owner._audio_timer.stop();owner._audio_timer.deleteLater()
        self.qt.processEvents()

    def start(self,owner):
        with patch('voxgo.app.signal.signal'),patch('sys.stdout',None):
            owner._finish_backend_startup()

    def tick(self,owner):
        loop=QEventLoop();owner._audio_timer.timeout.connect(loop.quit)
        QTimer.singleShot(500,loop.quit);loop.exec_()
        owner._audio.process_tick.assert_called_with(True,False)

    def test_windowed_startup_all_ui_languages_and_twenty_directions(self):
        for language,_ in UI_LANGUAGE_OPTIONS:
            for source,target in sorted(ONLINE_DIRECTIONS):
                with self.subTest(ui=language,source=source,target=target):
                    owner=self.owner(source,target,language);self.start(owner)
                    self.assertTrue(owner._running)
                    owner._start_audio_capture.assert_called_once()
                    owner._start_speech_worker.assert_called_once()
                    self.assertTrue(owner._audio_timer.isActive())
                    notice=owner._notify_user.call_args.args[1]
                    self.assertIn(language_label(source,language),notice)
                    self.assertIn(language_label(target,language),notice)
                    self.stop_timer(owner);owner._audio_timer=None

    def test_real_timer_reaches_audio_consumer_after_startup(self):
        owner=self.owner();self.start(owner);self.tick(owner)

    def test_startup_notice_failure_cannot_disable_audio_consumption(self):
        owner=self.owner();owner._notify_user.side_effect=RuntimeError('fixture presentation failure')
        self.start(owner);self.assertTrue(owner._audio_timer.isActive());self.tick(owner)

    def test_console_banner_failure_cannot_disable_audio_consumption(self):
        owner=self.owner();owner._print_banner=Mock(side_effect=OSError('fixture closed console'))
        self.start(owner);self.assertTrue(owner._audio_timer.isActive());self.tick(owner)
