import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QPoint, QRect, Qt
from PyQt5.QtWidgets import QApplication

from voxgo.i18n import UI_LANGUAGE_EN, UI_LANGUAGE_ZH
from voxgo.translation import TranslationConfig
from voxgo.ui.config_models import OverlayConfig, RuntimeConfig
from voxgo.ui.overlay_window import GameOverlay


class OverlayExperience051Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt_app = QApplication.instance() or QApplication([])

    def test_saved_offscreen_position_and_manual_reset(self):
        config = OverlayConfig(window_x=100000, window_y=100000)
        overlay = GameOverlay(config=config)
        try:
            self.assertTrue(overlay._geometry_reasonably_visible(overlay.geometry()))
            overlay.move(100000, 100000)
            overlay._ensure_visible_geometry()
            self.assertTrue(overlay._geometry_reasonably_visible(overlay.geometry()))
            overlay.hide()
            overlay.reset_overlay_position()
            self.assertTrue(overlay.isVisible())
            self.assertTrue(overlay._geometry_reasonably_visible(overlay.geometry()))
            self.assertTrue(overlay.windowFlags() & Qt.Tool)
            self.assertTrue(overlay.testAttribute(Qt.WA_ShowWithoutActivating))
        finally:
            overlay.close()

    def test_screen_gap_is_invisible_but_negative_secondary_screen_is_valid(self):
        overlay = GameOverlay(config=OverlayConfig())
        try:
            primary = SimpleNamespace(availableGeometry=lambda: QRect(0, 0, 800, 600))
            secondary = SimpleNamespace(availableGeometry=lambda: QRect(1600, 0, 800, 600))
            fake_app = SimpleNamespace(primaryScreen=lambda: primary, screens=lambda: [primary, secondary])
            with patch("voxgo.ui.overlay_window.QApplication", fake_app):
                self.assertFalse(overlay._geometry_reasonably_visible(QRect(1000, 100, 300, 150)))
                overlay.config.window_x = 1000
                overlay.config.window_y = 100
                overlay._restore_window_geometry()
                self.assertTrue(overlay._geometry_reasonably_visible(overlay.geometry()))
                self.assertLess(overlay.x(), 800)

            negative = SimpleNamespace(availableGeometry=lambda: QRect(-1920, 0, 1920, 1080))
            fake_app = SimpleNamespace(primaryScreen=lambda: primary, screens=lambda: [primary, negative])
            with patch("voxgo.ui.overlay_window.QApplication", fake_app):
                overlay.config.window_x = -1800
                overlay.config.window_y = 120
                overlay._restore_window_geometry()
                self.assertEqual((overlay.x(), overlay.y()), (-1800, 120))
        finally:
            overlay.close()

    def test_default_position_uses_primary_screen_nonzero_origin(self):
        overlay = GameOverlay(config=OverlayConfig(position="top"))
        try:
            area = QRect(1920, -200, 1000, 700)
            self.assertEqual(overlay._default_position_for_size(area, 500, 200), (2170, -150))
        finally:
            overlay.close()

    def test_provider_label_refreshes_for_provider_and_language(self):
        config = TranslationConfig()
        overlay = GameOverlay(translation_config=config, app_config=RuntimeConfig(language=UI_LANGUAGE_ZH))
        try:
            self.assertEqual(overlay._provider_label.text(), "API")
            config.provider = "google"
            overlay.refresh_translation_mode()
            self.assertEqual(overlay._provider_label.text(), "Google")
            config.provider = "local"
            overlay.refresh_translation_mode()
            self.assertEqual(overlay._provider_label.text(), "本地")
            overlay.app_config.language = UI_LANGUAGE_EN
            overlay.refresh_language()
            self.assertEqual(overlay._provider_label.text(), "Local")
            overlay.set_compact_mode(True)
            self.assertFalse(overlay._provider_label.isHidden())
        finally:
            overlay.close()

    def test_copy_only_final_translation_not_status_or_placeholder(self):
        overlay = GameOverlay(app_config=RuntimeConfig(language=UI_LANGUAGE_EN))
        try:
            overlay.add_translation("[Status] Download", "Please wait")
            overlay.add_translation_with_id("result", "hello", "...translating")
            overlay._set_copy_button_hover(0, True)
            overlay._set_copy_button_hover(1, True)
            self.assertTrue(overlay._copy_buttons[0].isHidden())
            self.assertTrue(overlay._copy_buttons[1].isHidden())

            overlay.update_translation("result", "你好", copyable=True)
            overlay._set_copy_button_hover(1, True)
            self.assertFalse(overlay._copy_buttons[1].isHidden())
            self.assertEqual(overlay._copy_buttons[1].toolTip(), "Copy translation")
            overlay._copy_buttons[1].click()
            self.assertEqual(QApplication.clipboard().text(), "你好")
            with patch("voxgo.ui.overlay_window.QCursor", SimpleNamespace(pos=lambda: QPoint(100000, 100000))):
                overlay._hide_copy_button_if_unhovered(1)
            self.assertTrue(overlay._copy_buttons[1].isHidden())

            overlay.update_translation("result", "[Translation failed] unavailable")
            overlay._set_copy_button_hover(1, True)
            self.assertTrue(overlay._copy_buttons[1].isHidden())
            overlay._clear_history()
            self.assertFalse(overlay._visible_items)
        finally:
            overlay.close()


if __name__ == "__main__":
    unittest.main()
