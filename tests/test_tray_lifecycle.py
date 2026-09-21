import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMenu

from voxgo.config.schema import RuntimeConfig
from voxgo.ui.tray_controller import TrayController


class FakeTray:
    available = True
    fail_show = False

    @classmethod
    def isSystemTrayAvailable(cls):
        return cls.available

    def __init__(self, icon, parent):
        self.asset = icon
        self.activated = SimpleNamespace(connect=Mock())
        self.visible = False

    def setToolTip(self, text):
        self.tooltip = text

    def setContextMenu(self, menu):
        self.menu = menu

    def show(self):
        self.visible = not self.fail_show

    def hide(self):
        self.visible = False

    def isVisible(self):
        return self.visible


class TrayLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        FakeTray.available = True
        FakeTray.fail_show = False
        self.owner = SimpleNamespace(
            config=SimpleNamespace(app=RuntimeConfig(language="en"),
                                   overlay=SimpleNamespace(compact_mode=False)),
            _shutdown_state="idle", _paused=False,
        )
        for method in ("_tray_toggle_overlay", "_toggle_translation", "_clear_history",
                       "_tray_toggle_compact_mode", "_tray_open_settings",
                       "_tray_show_fullscreen_help", "_request_shutdown",
                       "_handle_tray_activated", "_force_shutdown"):
            setattr(self.owner, method, Mock())
        self.controller = TrayController(self.owner)
        self.addCleanup(self.controller._discard)

    def setup_tray(self):
        return self.controller.setup(FakeTray, QMenu, self.app, QIcon(), None)

    def test_null_icon_resolves_to_actual_asset(self):
        self.assertTrue(self.setup_tray())
        self.assertFalse(self.controller.icon.asset.isNull())

    def test_missing_asset_uses_standard_icon(self):
        self.app.setWindowIcon(QIcon())
        with patch("PyQt5.QtGui.QIcon", return_value=QIcon()):
            self.assertFalse(self.controller._resolve_icon(self.app, QIcon()).isNull())

    def test_unavailable_tray_can_retry_and_setup_is_idempotent(self):
        FakeTray.available = False
        self.assertFalse(self.setup_tray())
        FakeTray.available = True
        self.assertTrue(self.setup_tray())
        original = self.controller.icon
        self.controller.hide()
        self.assertTrue(self.setup_tray())
        self.assertIs(original, self.controller.icon)
        self.assertTrue(original.isVisible())

    def test_failed_show_disposes_partial_setup_and_allows_retry(self):
        FakeTray.fail_show = True
        self.assertFalse(self.setup_tray())
        self.assertIsNone(self.controller.icon)
        self.assertEqual(self.controller.actions, {})
        FakeTray.fail_show = False
        self.assertTrue(self.setup_tray())

    def test_phone_hint_only_when_mobile_service_is_running(self):
        self.owner.config.hotkeys = SimpleNamespace(toggle_overlay="ctrl+shift+t")
        self.assertTrue(self.setup_tray())
        self.controller.icon.showMessage = Mock()
        self.controller.show_restore_hint()
        self.assertNotIn("QR", self.controller.icon.showMessage.call_args.args[1])
        self.owner._mobile = SimpleNamespace(server=object(), loop=SimpleNamespace(is_running=lambda: True),
                                             start_error=None)
        self.controller.show_restore_hint()
        self.assertIn("QR", self.controller.icon.showMessage.call_args.args[1])

    def test_failed_shutdown_keeps_restore_and_exit_but_blocks_translation(self):
        self.assertTrue(self.setup_tray())
        self.owner._shutdown_state = "stopping"
        self.controller.sync_state(None)
        actions = self.controller.actions
        self.assertFalse(actions["toggle_translation"].isEnabled())
        self.assertFalse(actions["quit"].isEnabled())
        self.assertTrue(actions["toggle_overlay"].isEnabled())
        self.owner._shutdown_state = "failed"
        self.controller.sync_state(None)
        self.assertTrue(actions["quit"].isEnabled())
        self.assertTrue(actions["force_quit"].isVisible())
        self.assertFalse(actions["toggle_translation"].isEnabled())
        actions["quit"].trigger()
        self.owner._request_shutdown.assert_called_once_with(from_tray=True)
        actions["force_quit"].trigger()
        self.owner._force_shutdown.assert_called_once()
        self.assertTrue(self.controller.icon.isVisible())


if __name__ == "__main__":
    unittest.main()
