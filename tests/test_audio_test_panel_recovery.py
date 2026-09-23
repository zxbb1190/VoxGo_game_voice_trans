import os
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt5.QtWidgets import QApplication
from voxgo.audio.capture import AudioConfig
from voxgo.ui.widgets import AudioTestPanel


class AudioTestPanelRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt_app = QApplication.instance() or QApplication([])

    def test_stop_failure_retains_monitor_and_prevents_new_stream(self):
        panel = AudioTestPanel(AudioConfig, ui_language='en-US')
        monitor = Mock()
        monitor.stop.side_effect = RuntimeError('reader still running')
        panel._monitor = monitor
        try:
            self.assertFalse(panel.stop_test())
            self.assertIs(panel._monitor, monitor)
            self.assertTrue(panel.stop_button.isEnabled())
            self.assertFalse(panel.start_button.isEnabled())
            with patch('voxgo.ui.widgets.AudioLevelMonitor') as constructor:
                panel.start_test()
                constructor.assert_not_called()
            monitor.stop.side_effect = None
            self.assertTrue(panel.stop_test())
            self.assertIsNone(panel._monitor)
        finally:
            monitor.stop.side_effect = None
            panel.close()

    def test_recovery_signal_only_resets_matching_monitor(self):
        for language, expected in (('zh-CN', '音频测试已因设备恢复停止。'),
                                   ('en-US', 'Audio test stopped while the device was recovering.')):
            panel = AudioTestPanel(AudioConfig, ui_language=language)
            monitor = Mock()
            panel._monitor = monitor
            try:
                panel._handle_level_update({'recovery': True, 'monitor_token': id(monitor) + 1})
                self.assertIs(panel._monitor, monitor)
                panel._handle_level_update({'recovery': True, 'monitor_token': id(monitor)})
                self.assertIsNone(panel._monitor)
                self.assertEqual(panel.status_label.text(), expected)
                self.assertTrue(panel.start_button.isEnabled())
                self.assertFalse(panel.stop_button.isEnabled())
            finally:
                panel.close()
