import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt5.QtCore import Qt, QPoint, QEvent, QPointF
from PyQt5.QtGui import QFontDatabase, QMouseEvent
from PyQt5.QtWidgets import QApplication

from voxgo.config.models import OverlayConfig, normalize_overlay_display
from voxgo.config.loader import default_app_config, load_user_settings, save_user_settings
from voxgo.ui.cinema_subtitles import CinemaTimeline
from voxgo.ui.overlay_window import GameOverlay


class CinemaTimelineTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.timeline = CinemaTimeline(lambda: self.now)

    def test_late_translation_never_rewinds_the_current_pair(self):
        self.timeline.offer(2, 'new', 'new original', '新译文')
        self.assertFalse(self.timeline.offer(1, 'old', 'old original', '旧译文'))
        self.assertEqual(self.timeline.cue.original, 'new original')
        self.assertEqual(self.timeline.cue.translated, '新译文')

    def test_expiry_fades_and_repeated_result_does_not_extend_it(self):
        self.timeline.offer(1, 'a', 'Cover me.', '掩护我。')
        deadline = self.timeline.cue.expires_at
        self.now = deadline - .175
        self.assertAlmostEqual(self.timeline.opacity, .5)
        self.assertFalse(self.timeline.offer(1, 'a', 'Cover me.', '掩护我。'))
        self.now = deadline + 1
        self.assertEqual(self.timeline.opacity, 0)

    def test_reading_time_is_bounded_and_monotonic(self):
        self.timeline.offer(1, 'short', '', '短句')
        self.assertEqual(self.timeline.cue.expires_at, 104)
        self.timeline.offer(2, 'long', '', '长句' * 100)
        self.assertEqual(self.timeline.cue.expires_at, 108)

    def test_clear_remove_and_empty_results_cannot_resurrect_an_older_cue(self):
        self.timeline.offer(2, 'b', '', '有效')
        self.timeline.remove('b')
        self.assertIsNone(self.timeline.cue)
        self.assertFalse(self.timeline.offer(1, 'a', '', '迟到'))
        self.assertFalse(self.timeline.offer(3, 'c', '', '  '))
        self.timeline.offer(4, 'd', '', '新句')
        self.timeline.clear()
        self.assertEqual(self.timeline.opacity, 0)
        self.assertFalse(self.timeline.offer(3, 'c', '', '迟到'))


class CinemaPersistenceTests(unittest.TestCase):
    def test_old_settings_keep_classic_mode_and_geometry(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'user_settings.json').write_text(json.dumps({
                'overlay': {'font_size': 22, 'window_x': 99, 'window_y': 120}}), encoding='utf-8')
            config = default_app_config()
            load_user_settings(config, Path(directory))
            self.assertEqual(config.overlay.display_mode, 'classic')
            self.assertEqual((config.overlay.font_size, config.overlay.window_x), (22, 99))
            self.assertEqual(config.overlay.cinema_font_size, 32)

    def test_profiles_round_trip_without_persisting_process_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            config = default_app_config()
            config.overlay = OverlayConfig(display_mode='cinema', font_size=23, window_x=71,
                cinema_font_size=48, cinema_original_font_size=26, cinema_show_original=False,
                cinema_x=-1700, cinema_bottom=800, cinema_width=1100, cinema_bg_opacity=.4,
                cinema_text_color='#FFEEAA')
            save_user_settings(config, Path(directory))
            restored = default_app_config()
            load_user_settings(restored, Path(directory))
            self.assertEqual(restored.overlay, config.overlay)

    def test_invalid_presentation_values_are_normalized(self):
        config = OverlayConfig(display_mode='unknown', cinema_font_size='bad', cinema_width=float('inf'),
            cinema_bg_opacity=-3, cinema_original_font_size=500, cinema_x='bad', cinema_bottom=float('nan'),
            cinema_text_color='<unsafe>')
        normalize_overlay_display(config)
        self.assertEqual(config.display_mode, 'classic')
        self.assertEqual(config.cinema_font_size, 32)
        self.assertEqual(config.cinema_width, 900)
        self.assertEqual(config.cinema_original_font_size, 40)
        self.assertEqual(config.cinema_bg_opacity, 0)
        self.assertIsNone(config.cinema_x)
        self.assertIsNone(config.cinema_bottom)
        self.assertEqual(config.cinema_text_color, '#FFFFFF')


class CinemaWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])
        # Qt's Windows offscreen platform starts without system fonts.
        for filename in ('msyh.ttc', 'msyhbd.ttc'):
            font = Path('C:/Windows/Fonts') / filename
            if font.exists():
                QFontDatabase.addApplicationFont(str(font))

    def setUp(self):
        self.pipeline_callback = Mock()
        self.overlay = GameOverlay(config=OverlayConfig(), on_settings_changed=self.pipeline_callback)
        self.now = 100.0
        self.overlay._cinema_view.timeline.clock = lambda: self.now
        self.presented = []
        self.overlay.subtitle_presented.connect(self.presented.append)
        self.overlay.show()
        self.pump()

    def tearDown(self):
        self.overlay.close()
        self.overlay.deleteLater()
        self.pump()

    def pump(self):
        for _ in range(4):
            self.qt.processEvents()

    def add(self, name='a', text='掩护我，我要穿过这条街。', original='Cover me. I am crossing the street.'):
        self.overlay.add_translation_with_id(name, original, '...translating')
        self.overlay.update_translation(name, text, copyable=True)
        self.pump()

    def test_switching_and_settings_do_not_call_the_pipeline(self):
        self.add()
        self.overlay.set_display_mode('cinema')
        self.overlay.show_settings()
        dialog = self.overlay._settings_dialog
        dialog.cinema_settings.translation_size.setValue(44)
        self.pump()
        self.assertEqual(self.overlay.config.cinema_font_size, 44)
        self.assertEqual(self.overlay.config.font_size, 16)
        dialog.display_mode_combo.setCurrentIndex(0)
        self.pump()
        self.assertFalse(self.overlay.is_cinema())
        self.assertEqual(len(self.overlay._translations), 1)
        self.pipeline_callback.assert_not_called()

    def test_each_mode_keeps_its_own_geometry(self):
        self.overlay.move(70, 90)
        self.overlay.resize(480, 230)
        self.pump()
        classic = self.overlay.geometry()
        self.overlay.set_display_mode('cinema')
        self.overlay.move(35, 180)
        self.overlay.resize(650, self.overlay.height())
        self.pump()
        cinema = (self.overlay.x(), self.overlay.y() + self.overlay.height(), self.overlay.width())
        self.overlay.set_display_mode('classic')
        self.pump()
        self.assertEqual(self.overlay.geometry(), classic)
        self.overlay.set_display_mode('cinema')
        self.pump()
        self.assertEqual((self.overlay.x(), self.overlay.y() + self.overlay.height(), self.overlay.width()), cinema)

    def test_complete_pairs_only_and_no_false_presentation_for_late_results(self):
        self.overlay.set_display_mode('cinema')
        self.overlay.add_translation_with_id('old', 'old original', 'pending')
        self.overlay.add_translation_with_id('new', 'new original', 'pending')
        self.pump()
        self.assertIsNone(self.overlay._cinema_view.timeline.cue)
        self.overlay.update_translation('new', '新译文', True)
        self.pump()
        self.overlay.update_translation('old', '旧译文', True)
        self.pump()
        self.assertEqual(self.overlay._cinema_view.timeline.cue.item_id, 'new')
        self.assertIn('new', self.presented)
        self.assertNotIn('old', self.presented)

    def test_hidden_or_expired_cues_do_not_count_as_presented(self):
        self.overlay.set_display_mode('cinema')
        self.overlay.hide()
        self.add()
        self.assertEqual(self.presented, [])
        self.now += 20
        self.overlay.show()
        self.pump()
        self.assertEqual(self.presented, [])
        self.add('fresh')
        self.assertIn('fresh', self.presented)

    def test_clear_and_remove_do_not_reveal_previous_caption(self):
        self.overlay.set_display_mode('cinema')
        self.add('a')
        self.add('b')
        self.overlay.remove_translation('b')
        self.pump()
        self.assertIsNone(self.overlay._cinema_view.timeline.cue)
        self.overlay.clear_history()
        self.pump()
        self.assertFalse(self.overlay._visible_items)

    def test_long_cue_grows_upward_and_wraps_unicode_without_losing_text(self):
        self.overlay.set_display_mode('cinema')
        self.overlay.move(40, 400)
        self.overlay.resize(480, self.overlay.height())
        self.pump()
        bottom = self.overlay.y() + self.overlay.height()
        original = 'Cover me. Прикрой меня. こちらです。 여기입니다. 🛡️ ' * 3
        self.add(text='掩护我，请从右边绕过去。' * 4, original=original)
        view = self.overlay._cinema_view
        self.assertEqual(view._lines[1][0].text(), ' '.join(original.split()))
        self.assertGreater(view._lines[0][0].lineCount(), 1)
        self.assertEqual(self.overlay.y() + self.overlay.height(), bottom)
        self.assertEqual(view.height(), view.minimumHeight())
        self.assertGreater(view.height(), 100)

    def test_locked_movie_keeps_only_hovered_unlock_and_is_mouse_transparent(self):
        self.overlay.set_display_mode('cinema')
        self.overlay._cinema_hovered = True
        self.overlay._refresh_display_controls()
        self.assertFalse(self.overlay._toolbar.isHidden())
        self.overlay._toggle_lock()
        self.assertTrue(self.overlay.testAttribute(Qt.WA_TransparentForMouseEvents))
        self.assertTrue(self.overlay._toolbar.isHidden())
        self.assertTrue(self.overlay._lock_button.isVisible())
        self.overlay._lock_button.click()
        self.assertFalse(self.overlay.testAttribute(Qt.WA_TransparentForMouseEvents))

    def test_drag_changes_cinema_anchor_without_changing_classic_position(self):
        classic = (self.overlay.config.window_x, self.overlay.config.window_y)
        self.overlay.set_display_mode('cinema')
        self.add()
        self.overlay._cinema_hovered = True
        self.overlay._refresh_display_controls()
        start = self.overlay.pos()
        point = QPoint(30, 50)
        global_point = self.overlay.mapToGlobal(point)
        QApplication.sendEvent(self.overlay, QMouseEvent(QEvent.MouseButtonPress,
            QPointF(point), QPointF(global_point), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
        QApplication.sendEvent(self.overlay, QMouseEvent(QEvent.MouseMove,
            QPointF(point + QPoint(20, -25)), QPointF(global_point + QPoint(20, -25)),
            Qt.NoButton, Qt.LeftButton, Qt.NoModifier))
        QApplication.sendEvent(self.overlay, QMouseEvent(QEvent.MouseButtonRelease,
            QPointF(point), QPointF(global_point + QPoint(20, -25)), Qt.LeftButton, Qt.NoButton, Qt.NoModifier))
        self.assertEqual(self.overlay.pos(), start + QPoint(20, -25))
        self.assertEqual((self.overlay.config.window_x, self.overlay.config.window_y), classic)

    def test_pause_capture_error_and_model_progress_stay_outside_the_cue(self):
        self.overlay.set_display_mode('cinema')
        self.add()
        self.overlay.set_paused(True)
        self.overlay.set_source_status('Target exited', attention=True)
        self.assertFalse(self.overlay._cinema_notice.isHidden())
        self.assertTrue(self.overlay._source_status.isHidden())
        self.assertEqual(self.overlay._cinema_view.timeline.cue.item_id, 'a')
        self.overlay.update_translation('a', '[Translation failed] offline', False)
        self.pump()
        self.assertIsNone(self.overlay._cinema_view.timeline.cue)
        self.overlay.set_paused(False)
        self.assertIn('offline', self.overlay._cinema_notice.text())

    def test_cinema_ignores_compact_toggle_and_refreshes_open_settings(self):
        self.overlay.show_settings()
        self.overlay.set_display_mode('cinema')
        dialog = self.overlay._settings_dialog
        self.assertEqual(dialog.display_mode_combo.currentData(), 'cinema')
        self.assertFalse(dialog.cinema_settings.isHidden())
        self.overlay.toggle_compact_mode()
        self.assertFalse(self.overlay.config.compact_mode)
        dialog.cinema_settings.show_original.setChecked(False)
        self.add()
        self.assertEqual(len(self.overlay._cinema_view._lines), 1)

    def test_empty_locked_cinema_can_recover_via_mode_shortcut_without_tray(self):
        self.overlay.set_display_mode('cinema')
        self.overlay._tray_available = False
        self.overlay._toggle_lock()
        self.assertFalse(self.overlay._lock_button.isVisible())
        self.overlay._signals.toggle_display_mode.emit()
        self.pump()
        self.assertFalse(self.overlay.is_cinema())
        self.assertTrue(self.overlay._lock_button.isVisible())
        self.overlay._lock_button.click()
        self.assertFalse(self.overlay.config.locked)

    def test_locking_with_settings_open_cannot_be_undone_by_the_dialog_copy(self):
        self.overlay.set_display_mode('cinema')
        self.overlay.show_settings()
        self.pump()
        self.overlay._toggle_lock()
        self.pump()
        self.assertTrue(self.overlay.config.locked)
        self.assertTrue(self.overlay.testAttribute(Qt.WA_TransparentForMouseEvents))
        self.assertFalse(self.overlay._settings_dialog.isVisible())

    def test_narrow_large_text_pages_inside_screen_without_truncation(self):
        self.overlay.config.cinema_font_size = 64
        self.overlay.config.cinema_original_font_size = 40
        self.overlay.set_display_mode('cinema')
        self.overlay.resize(320, self.overlay.height())
        translated = '请绕过前方的仓库，从右侧靠近。' * 7
        original = 'Please move around the warehouse and approach from the right. ' * 5
        self.add(text=translated, original=original)
        view = self.overlay._cinema_view
        self.assertGreater(len(view._pages), 1)
        self.assertLessEqual(self.overlay.height(), self.overlay.screen().availableGeometry().height())
        for layout, main in view._lines:
            expected = {layout.lineAt(i).textStart() for i in range(layout.lineCount())}
            shown = {line.textStart() for page in view._pages for line, is_main, _ in page if is_main == main}
            self.assertEqual(shown, expected)
        self.now += view._seconds_per_page
        view.tick()
        self.pump()
        self.assertGreater(view.timeline.opacity, 0)

    def test_worker_thread_results_are_queued_and_painted_on_gui_thread(self):
        self.overlay.set_display_mode('cinema')
        def deliver():
            self.overlay.add_translation_with_id('old', 'old original', 'pending')
            self.overlay.add_translation_with_id('new', 'new original', 'pending')
            self.overlay.update_translation('new', '新译文', True)
            self.overlay.update_translation('old', '旧译文', True)
        worker = threading.Thread(target=deliver)
        worker.start()
        worker.join(timeout=2)
        self.assertFalse(worker.is_alive())
        self.assertIsNone(self.overlay._cinema_view.timeline.cue)
        self.pump()
        self.assertEqual(self.overlay._cinema_view.timeline.cue.item_id, 'new')
        self.assertEqual(self.presented, ['new'])


if __name__ == '__main__':
    unittest.main()
