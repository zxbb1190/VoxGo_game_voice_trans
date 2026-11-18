"""Visible-caption hit testing and mode switching through real Qt events."""
import json
import os
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from voxgo.app import VoxGoApp
from voxgo.config.loader import default_app_config, load_user_settings, save_user_settings
from voxgo.ui.overlay_window import GameOverlay


class CinemaControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])
        for name in ('msyh.ttc', 'msyhbd.ttc'):
            QFontDatabase.addApplicationFont('C:/Windows/Fonts/' + name)

    def setUp(self):
        self.cursor = QPoint(-10000, -10000)
        self.now = 100.0
        self.cursor_patch = patch('voxgo.ui.overlay_presentation.QCursor.pos', side_effect=lambda: self.cursor)
        self.cursor_patch.start()
        self.addCleanup(self.cursor_patch.stop)
        self.config = default_app_config()
        self.config.overlay.display_mode = 'cinema'
        self.pipeline = Mock()
        self.overlay = GameOverlay(config=self.config.overlay, hotkeys=self.config.hotkeys,
                                   on_settings_changed=self.pipeline)
        self.addCleanup(self.close_overlay)
        self.overlay._cinema_view.timeline.clock = lambda: self.now
        self.overlay.show()
        self.pump()

    def close_overlay(self):
        self.overlay.close()
        self.overlay.deleteLater()
        self.pump()

    def pump(self):
        for _ in range(4):
            self.qt.processEvents()

    def add_caption(self):
        self.overlay.add_translation_with_id('a', 'Cover me.', '...')
        self.overlay.update_translation('a', '掩护我。', True)
        self.pump()

    def hover_caption(self):
        view = self.overlay._cinema_view
        self.cursor = view.mapToGlobal(view.visible_text_rects()[0].center())
        self.overlay._poll_cinema_hover()
        self.pump()

    def test_empty_pending_or_failed_translation_cannot_show_toolbar_or_capture_mouse(self):
        self.cursor = self.overlay.frameGeometry().center()
        self.overlay._poll_cinema_hover()
        self.assertTrue(self.overlay._cinema_notice.isHidden())
        self.overlay.add_translation_with_id('a', 'Cover me.', '...')
        for failed in (False, True):
            if failed:
                self.overlay.update_translation('a', '[Translation failed] offline', False)
            self.overlay._poll_cinema_hover()
            self.pump()
            self.assertFalse(self.overlay._toolbar.isVisible())
            self.assertFalse(self.overlay._lock_button.isVisible())
            self.assertTrue(self.overlay.testAttribute(Qt.WA_TransparentForMouseEvents))
            self.assertFalse(self.overlay._can_interact())

    def test_visible_caption_triggers_toolbar_but_empty_sides_do_not(self):
        self.add_caption()
        view = self.overlay._cinema_view
        self.cursor = view.mapToGlobal(QPoint(1, view.height() // 2))
        self.overlay._poll_cinema_hover()
        self.assertFalse(self.overlay._toolbar.isVisible())
        self.assertTrue(self.overlay.testAttribute(Qt.WA_TransparentForMouseEvents))
        self.hover_caption()
        self.assertTrue(self.overlay._toolbar.isVisible())
        self.assertFalse(self.overlay.testAttribute(Qt.WA_TransparentForMouseEvents))

    def test_expired_subtitle_cannot_begin_new_hover(self):
        self.add_caption()
        view = self.overlay._cinema_view
        self.cursor = view.mapToGlobal(view.visible_text_rects()[0].center())
        self.now += 30
        self.overlay._update_fade()
        self.overlay._poll_cinema_hover()
        self.assertEqual(view.visible_text_rects(), [])
        self.assertFalse(self.overlay._toolbar.isVisible())
        self.assertTrue(self.overlay.testAttribute(Qt.WA_TransparentForMouseEvents))

    def test_locked_empty_stays_invisible_but_caption_reveals_only_unlock(self):
        self.overlay._toggle_lock()
        self.cursor = self.overlay.frameGeometry().center()
        self.overlay._poll_cinema_hover()
        self.assertFalse(self.overlay._lock_button.isVisible())
        self.add_caption()
        self.hover_caption()
        self.assertFalse(self.overlay._toolbar.isVisible())
        self.assertTrue(self.overlay._lock_button.isVisible())
        self.overlay._lock_button.click()
        self.assertTrue(self.overlay._toolbar.isVisible())
        self.assertFalse(self.overlay.config.locked)

    def test_source_hidden_lock_aligned_and_outer_border_transparent(self):
        self.overlay.set_source_status('Source: test device', attention=True)
        self.add_caption()
        self.hover_caption()
        self.assertTrue(self.overlay._source_status.isHidden())
        self.assertEqual(self.overlay._lock_button.y(), self.overlay._settings_button.mapToGlobal(QPoint()).y())
        self.assertEqual(self.overlay._lock_button.x(), self.overlay._lock_slot.mapToGlobal(QPoint()).x())
        self.assertEqual(self.overlay._lock_button.size(), self.overlay._settings_button.size())
        frame = self.overlay.grab().toImage()
        for y in range(12, frame.height() - 12):
            self.assertEqual(frame.pixelColor(1, y).alpha(), 0)
        self.overlay.set_display_mode('classic')
        self.assertTrue(self.overlay._source_status.isVisible())

    def test_toolbar_button_switches_both_ways_without_touching_pipeline(self):
        self.add_caption()
        self.hover_caption()
        changed = Mock()
        self.overlay.presentation_changed.connect(changed)
        self.assertIn('ctrl+alt+m', self.overlay._display_mode_button.toolTip())
        self.overlay._display_mode_button.click()
        self.assertFalse(self.overlay.is_cinema())
        self.assertTrue(self.overlay._display_mode_button.isVisible())
        self.overlay._display_mode_button.click()
        self.assertTrue(self.overlay.is_cinema())
        self.assertEqual(self.overlay._cinema_view.timeline.cue.item_id, 'a')
        self.assertEqual(changed.call_count, 2)
        self.pipeline.assert_not_called()

    def test_worker_shortcut_switches_on_ui_thread_and_persists_when_empty_or_locked(self):
        with tempfile.TemporaryDirectory() as directory:
            app = SimpleNamespace(config=self.config, _overlay=self.overlay,
                _save_user_settings=lambda: save_user_settings(self.config, Path(directory)), _sync_tray_state=Mock())
            self.overlay.presentation_changed.connect(lambda: VoxGoApp._save_overlay_presentation(app))
            self.overlay._toggle_lock()
            worker = threading.Thread(target=lambda: VoxGoApp._toggle_display_mode(app))
            worker.start()
            worker.join()
            self.assertTrue(self.overlay.is_cinema())
            self.pump()
            self.assertFalse(self.overlay.is_cinema())
            self.assertTrue(self.overlay.config.locked)
            restored = default_app_config()
            load_user_settings(restored, Path(directory))
            self.assertEqual(restored.overlay.display_mode, 'classic')
            self.assertTrue(restored.overlay.locked)
            self.pipeline.assert_not_called()

    def test_settings_reject_duplicate_hotkey_then_apply_corrected_value(self):
        self.overlay.show_settings()
        dialog = self.overlay._settings_dialog
        changed = Mock()
        dialog.settings_changed.connect(changed)
        dialog.toggle_display_mode_input.setText('Control + Alt + S')
        dialog._hotkeys_changed()
        self.assertFalse(dialog.hotkey_conflict_label.isHidden())
        self.assertEqual(dialog.hotkey_config.toggle_display_mode, 'ctrl+alt+m')
        changed.assert_not_called()
        # Other collection paths must not accidentally persist a duplicate either.
        dialog._collect_values()
        self.assertEqual(dialog.hotkey_config.toggle_display_mode, 'ctrl+alt+m')
        dialog.toggle_display_mode_input.setText('ctrl+alt+n')
        dialog._hotkeys_changed()
        self.assertTrue(dialog.hotkey_conflict_label.isHidden())
        self.assertEqual(dialog.hotkey_config.toggle_display_mode, 'ctrl+alt+n')
        self.assertIn('ctrl+alt+n', self.overlay._display_mode_button.toolTip())
        changed.assert_called_once()

    def test_mode_hotkey_can_be_captured_and_cleared_in_settings(self):
        self.overlay.show_settings()
        dialog = self.overlay._settings_dialog
        field = dialog.toggle_display_mode_input
        QTest.keyClick(field, Qt.Key_N, Qt.ControlModifier | Qt.AltModifier)
        self.assertEqual(dialog.hotkey_config.toggle_display_mode, 'ctrl+alt+n')
        QTest.keyClick(field, Qt.Key_Backspace)
        self.assertEqual(dialog.hotkey_config.toggle_display_mode, '')


class ModeHotkeyPersistenceTests(unittest.TestCase):
    def test_old_config_gets_default_and_custom_or_disabled_binding_roundtrips(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'user_settings.json').write_text(json.dumps({'hotkeys': {'toggle_overlay': 'ctrl+alt+t'}}))
            config = default_app_config()
            load_user_settings(config, root)
            self.assertEqual(config.hotkeys.toggle_display_mode, 'ctrl+alt+m')
            self.assertEqual(config.hotkeys.toggle_overlay, 'ctrl+alt+t')
            for binding in ('ctrl+alt+n', ''):
                config.hotkeys.toggle_display_mode = binding
                save_user_settings(config, root)
                restored = default_app_config()
                load_user_settings(restored, root)
                self.assertEqual(restored.hotkeys.toggle_display_mode, binding)
