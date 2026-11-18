"""Cinema pointer regions, delayed hiding, and the separate clickable unlock window."""
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5.QtCore import Qt, QEvent, QPoint
from PyQt5.QtTest import QTest
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QApplication

from voxgo.config.models import OverlayConfig
from voxgo.ui.overlay_window import GameOverlay


class CinemaHoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])
        for filename in ("msyh.ttc", "msyhbd.ttc"):
            font = Path("C:/Windows/Fonts") / filename
            if font.exists():
                QFontDatabase.addApplicationFont(str(font))

    def setUp(self):
        self.now = 100.0
        self.cursor = QPoint(-10000, -10000)
        for mocked in (patch("voxgo.ui.overlay_presentation.QCursor.pos", side_effect=lambda: QPoint(self.cursor)),
                       patch("voxgo.ui.overlay_presentation.time", SimpleNamespace(monotonic=lambda: self.now))):
            mocked.start()
            self.addCleanup(mocked.stop)
        self.overlay = GameOverlay(config=OverlayConfig(display_mode="cinema"))
        self.overlay._cinema_view.timeline.clock = lambda: self.now
        self.overlay.show()
        self.overlay.add_translation_with_id('seed', 'Cover me.', '...')
        self.overlay.update_translation('seed', '掩护我。', True)
        self.pump()

    def tearDown(self):
        self.overlay.close()
        self.overlay.deleteLater()
        self.pump()

    def pump(self):
        for _ in range(4):
            self.qt.processEvents()

    def point_at(self, widget):
        if widget is self.overlay and not self.overlay._cinema_hovered:
            view = self.overlay._cinema_view
            self.cursor = view.mapToGlobal(view.visible_text_rects()[0].center())
        else:
            self.cursor = widget.mapToGlobal(widget.rect().center())
        self.overlay._poll_cinema_hover()
        self.pump()

    def leave(self):
        self.cursor = QPoint(-10000, -10000)
        self.overlay._poll_cinema_hover()

    def elapse(self, seconds):
        self.now += seconds
        self.overlay._poll_cinema_hover()
        self.pump()

    def test_child_buttons_and_separate_lock_window_never_count_as_leaving(self):
        self.point_at(self.overlay)
        for button in (self.overlay._pause_button, self.overlay._settings_button,
                       self.overlay._qr_button, self.overlay._lock_button):
            self.point_at(button)
            QApplication.sendEvent(self.overlay, QEvent(QEvent.Leave))
            self.elapse(3)
            self.assertTrue(self.overlay._toolbar.isVisible())
            self.assertTrue(button.isVisible())

    def test_leaving_has_grace_period_and_return_cancels_pending_hide(self):
        self.point_at(self.overlay)
        self.leave()
        self.elapse(.4)
        self.assertTrue(self.overlay._toolbar.isVisible())
        self.point_at(self.overlay._settings_button)
        self.elapse(2)
        self.assertTrue(self.overlay._toolbar.isVisible())
        self.leave()
        self.elapse(.71)
        self.assertFalse(self.overlay._toolbar.isVisible())
        self.assertFalse(self.overlay._lock_button.isVisible())

    def test_language_popup_outside_overlay_keeps_toolbar_visible(self):
        self.point_at(self.overlay)
        combo = self.overlay._source_lang_combo
        combo.showPopup()
        self.pump()
        self.assertIsNotNone(QApplication.activePopupWidget())
        self.leave()
        self.elapse(3)
        self.assertTrue(self.overlay._toolbar.isVisible())
        combo.hidePopup()
        self.leave()
        self.elapse(.71)
        self.assertFalse(self.overlay._toolbar.isVisible())

    def test_qr_popup_and_small_gaps_are_part_of_interaction_region(self):
        self.point_at(self.overlay)
        self.overlay._show_qr_popup()
        self.point_at(self.overlay._qr_popup)
        self.elapse(3)
        self.assertTrue(self.overlay._toolbar.isVisible())
        self.overlay._qr_popup.hide()
        self.cursor = self.overlay.frameGeometry().topLeft() + QPoint(-5, 10)
        self.overlay._poll_cinema_hover()
        self.elapse(3)
        self.assertTrue(self.overlay._toolbar.isVisible())

    def test_cue_expiry_does_not_shrink_window_or_move_toolbar_under_pointer(self):
        self.overlay.resize(450, self.overlay.height())
        self.overlay.add_translation_with_id("a", "Please cover me. " * 6, "准备穿过街道，请在右侧掩护我。" * 5)
        self.overlay.update_translation("a", "准备穿过街道，请在右侧掩护我。" * 5, copyable=True)
        self.pump()
        self.assertIsNotNone(self.overlay._cinema_view.timeline.cue)
        self.point_at(self.overlay)
        self.point_at(self.overlay._settings_button)
        top = self.overlay._toolbar.mapToGlobal(QPoint(0, 0))
        height = self.overlay.height()
        self.overlay.clear_history()
        self.pump()
        self.elapse(3)
        self.assertEqual(self.overlay._toolbar.mapToGlobal(QPoint(0, 0)), top)
        self.assertEqual(self.overlay.height(), height)
        self.assertTrue(self.overlay._settings_button.isVisible())
        self.leave()
        self.elapse(.71)
        self.assertLess(self.overlay.height(), height)

    def test_locked_overlay_reveals_clickable_unlock_without_enter_events(self):
        self.overlay._toggle_lock()
        self.pump()
        self.assertTrue(self.overlay.testAttribute(Qt.WA_TransparentForMouseEvents))
        self.assertFalse(self.overlay._lock_button.isVisible())
        # Locked windows do not receive Enter events; the cursor poll must suffice.
        view = self.overlay._cinema_view
        self.cursor = view.mapToGlobal(view.visible_text_rects()[0].center())
        QTest.qWait(170)
        self.assertTrue(self.overlay._lock_button.isVisible())
        self.assertFalse(self.overlay._toolbar.isVisible())
        self.assertFalse(hasattr(self.overlay, "_live_check_button"))
        self.assertTrue(self.overlay.testAttribute(Qt.WA_TransparentForMouseEvents))
        self.assertTrue(self.overlay._lock_button.isWindow())
        self.assertFalse(self.overlay._lock_button.testAttribute(Qt.WA_TransparentForMouseEvents))
        if QApplication.platformName() == "windows":
            import ctypes
            user32 = ctypes.windll.user32
            getter = user32.GetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8 else user32.GetWindowLongW
            getter.argtypes = [ctypes.c_void_p, ctypes.c_int]
            getter.restype = ctypes.c_ssize_t
            self.assertTrue(getter(int(self.overlay.winId()), -20) & 0x20)
            self.assertFalse(getter(int(self.overlay._lock_button.winId()), -20) & 0x20)
        self.point_at(self.overlay._lock_button)
        self.elapse(3)
        QTest.mouseClick(self.overlay._lock_button, Qt.LeftButton)
        self.assertFalse(self.overlay.config.locked)
        self.assertFalse(self.overlay.testAttribute(Qt.WA_TransparentForMouseEvents))
        self.assertTrue(self.overlay._toolbar.isVisible())

    def test_lock_layout_transition_keeps_path_to_unlock_visible(self):
        self.point_at(self.overlay)
        self.point_at(self.overlay._lock_button)
        old_pointer = QPoint(self.cursor)
        self.overlay._lock_button.click()
        self.pump()
        self.assertTrue(self.overlay.config.locked)
        self.cursor = old_pointer
        self.elapse(3)
        self.assertTrue(self.overlay._lock_button.isVisible())
        self.point_at(self.overlay._lock_button)
        self.elapse(3)
        self.assertTrue(self.overlay._lock_button.isVisible())
        self.leave()
        self.elapse(.71)
        self.assertFalse(self.overlay._lock_button.isVisible())

    def test_drag_and_resize_hold_controls_until_operation_finishes(self):
        self.point_at(self.overlay)
        self.overlay._dragging = True
        self.leave()
        self.elapse(3)
        self.assertTrue(self.overlay._toolbar.isVisible())
        self.overlay._dragging = False
        self.overlay._resizing = True
        self.elapse(3)
        self.assertTrue(self.overlay._toolbar.isVisible())
        self.overlay._resizing = False
        self.leave()
        self.elapse(.71)
        self.assertFalse(self.overlay._toolbar.isVisible())

    def test_mode_hide_and_shutdown_stop_poll_and_auxiliary_unlock(self):
        self.assertTrue(self.overlay._cinema_hover_timer.isActive())
        self.point_at(self.overlay)
        self.overlay.set_display_mode("classic")
        self.assertFalse(self.overlay._cinema_hover_timer.isActive())
        self.assertTrue(self.overlay._toolbar.isVisible())
        self.overlay.set_display_mode("cinema")
        self.point_at(self.overlay)
        self.overlay.hide()
        self.assertFalse(self.overlay._cinema_hover_timer.isActive())
        self.assertFalse(self.overlay._lock_button.isVisible())
        self.overlay.show()
        self.assertTrue(self.overlay._cinema_hover_timer.isActive())
        self.overlay.prepare_shutdown()
        self.assertFalse(self.overlay._cinema_hover_timer.isActive())
