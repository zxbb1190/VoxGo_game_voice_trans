import keyboard
from loguru import logger
from voxgo.config.hotkeys import HOTKEY_ACTIONS, hotkey_conflicts


class HotkeyManager:
    def __init__(self, notify_error):
        self._notify_error = notify_error
        self._handles = []

    def setup(self, hotkeys, callbacks):
        self.remove_all()
        conflicts = dict((duplicate, first) for first, duplicate in hotkey_conflicts(hotkeys))
        active_hotkeys = []
        for name, label, _ in HOTKEY_ACTIONS:
            value = str(getattr(hotkeys, name, '') or '').strip()
            if not value or name not in callbacks:
                continue
            if name in conflicts:
                self._notify_error("快捷键冲突", f"{label}: {value} 已被其他功能使用，请在设置中修改。", "错误")
                continue
            try:
                self._handles.append(keyboard.add_hotkey(value, callbacks[name]))
                active_hotkeys.append(f"{label}={value}")
            except Exception as e:
                logger.exception(f"热键注册失败: {e}")
                self._notify_error("热键注册失败", str(e), "错误")
        logger.info("热键已注册: {}", ", ".join(active_hotkeys) or "无")

    def remove_all(self):
        for handle in self._handles:
            try:
                keyboard.remove_hotkey(handle)
            except Exception:
                pass
        self._handles = []
