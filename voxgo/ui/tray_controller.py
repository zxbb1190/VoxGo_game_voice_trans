from pathlib import Path
import sys

from loguru import logger

from voxgo.app_info import APP_NAME, APP_VERSION
from voxgo.i18n import ui_text
from voxgo.config.schema import ui_language_of


class TrayController:
    def __init__(self, owner):
        self._owner = owner
        self.icon = None
        self.menu = None
        self.actions = {}
        self.setup_error = ""

    @staticmethod
    def _resolve_icon(qt_app, app_icon):
        # Null QIcon objects are truthy; explicitly check their image data.
        for candidate in (app_icon, qt_app.windowIcon()):
            if candidate is not None and (not hasattr(candidate, "isNull") or not candidate.isNull()):
                return candidate
        from PyQt5.QtGui import QIcon
        from PyQt5.QtWidgets import QStyle

        roots = [Path(__file__).resolve().parents[2]]
        if getattr(sys, "_MEIPASS", None):
            roots.insert(0, Path(sys._MEIPASS))
        for root in roots:
            candidate = QIcon(str(root / "assets" / "voxgo.ico"))
            if not candidate.isNull():
                return candidate
        candidate = qt_app.style().standardIcon(QStyle.SP_ComputerIcon)
        if candidate.isNull():
            raise RuntimeError("No usable system tray icon could be loaded")
        logger.warning("Using Qt fallback icon for system tray")
        return candidate

    def _discard(self):
        for item in (self.icon, self.menu):
            if item is not None:
                try:
                    if hasattr(item, "hide"):
                        item.hide()
                    if hasattr(item, "deleteLater"):
                        item.deleteLater()
                except Exception:
                    logger.debug("Could not dispose failed tray object")
        self.icon = None
        self.menu = None
        self.actions = {}

    def setup(self, tray_cls, menu_cls, qt_app, app_icon, overlay):
        self.setup_error = ""
        if not qt_app:
            self.setup_error = "Qt application is not available"
            return False
        if not tray_cls.isSystemTrayAvailable():
            self.setup_error = "system tray is not available"
            logger.warning("系统托盘不可用，跳过托盘入口")
            return False

        try:
            if self.icon is not None:
                self.sync_state(overlay)
                self.icon.show()
                if not hasattr(self.icon, "isVisible") or self.icon.isVisible():
                    return True
                self._discard()
            self.icon = tray_cls(self._resolve_icon(qt_app, app_icon), qt_app)
            self.icon.setToolTip(f"{APP_NAME} v{APP_VERSION}")
            self.menu = menu_cls(qt_app.activeWindow())
            ui_language = ui_language_of(self._owner.config)

            self.actions = {
                "toggle_overlay": self.menu.addAction(ui_text(ui_language, "隐藏浮窗", "Hide Overlay")),
                "reset_overlay_position": self.menu.addAction(ui_text(ui_language, "重置浮窗位置", "Reset Overlay Position")),
                "toggle_translation": self.menu.addAction(ui_text(ui_language, "暂停翻译", "Pause Translation")),
                "clear_history": self.menu.addAction(ui_text(ui_language, "清空字幕", "Clear Subtitles")),
                "compact_mode": self.menu.addAction(ui_text(ui_language, "启用紧凑浮窗", "Enable Compact Overlay")),
            }
            self.menu.addSeparator()
            self.actions["settings"] = self.menu.addAction(ui_text(ui_language, "设置", "Settings"))
            self.actions["fullscreen_help"] = self.menu.addAction(ui_text(ui_language, "全屏兼容说明", "Fullscreen Compatibility"))
            self.menu.addSeparator()
            self.actions["quit"] = self.menu.addAction(ui_text(ui_language, "退出", "Quit"))
            if hasattr(self._owner, "_force_shutdown"):
                self.actions["force_quit"] = self.menu.addAction(ui_text(ui_language, "强制退出", "Force Quit"))
                self.actions["force_quit"].triggered.connect(self._owner._force_shutdown)

            self.actions["toggle_overlay"].triggered.connect(self._owner._tray_toggle_overlay)
            self.actions["reset_overlay_position"].triggered.connect(self._owner._tray_reset_overlay_position)
            self.actions["toggle_translation"].triggered.connect(self._owner._toggle_translation)
            self.actions["clear_history"].triggered.connect(self._owner._clear_history)
            self.actions["compact_mode"].triggered.connect(self._owner._tray_toggle_compact_mode)
            self.actions["settings"].triggered.connect(self._owner._tray_open_settings)
            self.actions["fullscreen_help"].triggered.connect(self._owner._tray_show_fullscreen_help)
            self.actions["quit"].triggered.connect(lambda: self._owner._request_shutdown(from_tray=True))
            self.icon.activated.connect(self._owner._handle_tray_activated)
            self.icon.setContextMenu(self.menu)
            self.sync_state(overlay)
            self.icon.show()
            visible = bool(self.icon.isVisible()) if hasattr(self.icon, "isVisible") else True
            logger.info("system tray initialized: visible={}", visible)
            if not visible:
                raise RuntimeError("System tray icon did not become visible")
            return True
        except Exception as exc:
            self.setup_error = str(exc)
            logger.exception("系统托盘初始化失败: {}", exc)
            self._discard()
            return False

    def sync_state(self, overlay):
        if not self.actions:
            return
        shutdown = getattr(self._owner, "_shutdown_state", "idle")
        for name, action in self.actions.items():
            if hasattr(action, "setEnabled"):
                action.setEnabled(shutdown == "idle" or name in {"toggle_overlay", "reset_overlay_position"} or
                                  (shutdown == "failed" and name in {"quit", "force_quit"}))
            if name == "force_quit" and hasattr(action, "setVisible"):
                action.setVisible(shutdown == "failed")
        config = self._owner.config
        ui_language = ui_language_of(config)
        if "toggle_overlay" in self.actions and overlay:
            self.actions["toggle_overlay"].setText(ui_text(
                ui_language,
                "隐藏浮窗" if overlay.isVisible() else "显示浮窗",
                "Hide Overlay" if overlay.isVisible() else "Show Overlay",
            ))
        if "toggle_translation" in self.actions:
            paused = bool(getattr(self._owner, "_paused", False))
            self.actions["toggle_translation"].setText(ui_text(
                ui_language,
                "恢复翻译" if paused else "暂停翻译",
                "Resume Translation" if paused else "Pause Translation",
            ))
        if "compact_mode" in self.actions:
            compact = bool(getattr(config.overlay, "compact_mode", False))
            self.actions["compact_mode"].setText(ui_text(
                ui_language,
                "退出紧凑浮窗" if compact else "启用紧凑浮窗",
                "Exit Compact Overlay" if compact else "Enable Compact Overlay",
            ))
        static_labels = {
            "clear_history": ("清空字幕", "Clear Subtitles"),
            "reset_overlay_position": ("重置浮窗位置", "Reset Overlay Position"),
            "settings": ("设置", "Settings"),
            "fullscreen_help": ("全屏兼容说明", "Fullscreen Compatibility"),
            "quit": ("退出", "Quit"),
        }
        for key, (zh, en) in static_labels.items():
            if key in self.actions:
                self.actions[key].setText(ui_text(ui_language, zh, en))
        if shutdown in {"stopping", "failed"}:
            self.actions["quit"].setText(ui_text(
                ui_language,
                "正在退出…" if shutdown == "stopping" else "再次退出",
                "Exiting…" if shutdown == "stopping" else "Retry Exit",
            ))
        if self.icon:
            paused = bool(getattr(self._owner, "_paused", False))
            state = ui_text(
                ui_language,
                "暂停" if paused else "运行中",
                "Paused" if paused else "Running",
            )
            if shutdown in {"stopping", "failed"}:
                state = ui_text(ui_language, "正在退出" if shutdown == "stopping" else "退出失败 · 翻译已停止",
                                "Exiting" if shutdown == "stopping" else "Exit failed · Translation stopped")
            self.icon.setToolTip(f"{APP_NAME} v{APP_VERSION} - {state}")

    def hide(self):
        if self.icon:
            self.icon.hide()

    def show_restore_hint(self):
        if not self.icon:
            return
        ui_language = ui_language_of(self._owner.config)
        hotkey = str(getattr(self._owner.config.hotkeys, "toggle_overlay", "") or "").strip()
        message = ui_text(
            ui_language,
            f"VoxGo 仍在运行。点击托盘图标或按 {hotkey} 恢复浮窗。",
            f"VoxGo is still running. Click the tray icon or press {hotkey} to restore the overlay.",
        )
        mobile = getattr(self._owner, "_mobile", None)
        if (mobile and getattr(mobile, "server", None) and
                getattr(mobile, "loop", None) and mobile.loop.is_running() and
                not getattr(mobile, "start_error", None)):
            message += ui_text(ui_language, " 可通过浮窗的手机二维码，用手机查看翻译结果。",
                               " Use the overlay’s Mobile QR Code to view translations on your phone.")
        try:
            self.icon.showMessage(APP_NAME, message)
        except Exception as exc:
            logger.debug("system tray restore hint failed: {}", exc)
