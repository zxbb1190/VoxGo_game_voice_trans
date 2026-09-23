"""Reusable UI widgets and lightweight test runners."""

import asyncio
import threading
import time
from typing import Callable, Optional

from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QColorDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from voxgo.audio.capture import AudioConfig, AudioLevelMonitor, AudioRecoveryInProgress
from voxgo.i18n import UI_LANGUAGE_ZH, is_english_ui, normalize_ui_language
from voxgo.translation import GameTranslator, TranslationConfig
from voxgo.ui.config_models import _copy_audio_config, _copy_translation_config, _tr


class TranslationTestSignals(QObject):
    finished = pyqtSignal(bool, str)


class TranslationTestRunner:
    def __init__(self, config: TranslationConfig, callback: Callable[[bool, str], None]):
        self.signals = TranslationTestSignals()
        self.signals.finished.connect(callback)
        self._config = _copy_translation_config(config)
        self._cancelled = threading.Event()
        self._loop = None
        self._task = None
        if self._config.provider == "local":
            self._config.enable_local_phrase_cache = False

    def start(self):
        threading.Thread(target=self._run, name="translation-test", daemon=True).start()

    def cancel(self):
        self._cancelled.set()
        loop, task = self._loop, self._task
        if loop and task and not loop.is_closed():
            try:
                loop.call_soon_threadsafe(task.cancel)
            except RuntimeError:
                pass

    def _run(self):
        if self._cancelled.is_set():
            return
        started_at = time.time()
        translator = GameTranslator(self._config)
        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        try:
            source = "zh" if self._config.provider == "local" and self._config.source_lang == "zh" else "en"
            text = "请在桥边等我。" if source == "zh" else "Hello, can you hear me?"
            if self._cancelled.is_set():
                return
            self._task = loop.create_task(translator.translate(text, source))
            if self._cancelled.is_set():
                self._task.cancel()
            translated = loop.run_until_complete(self._task)
            if self._cancelled.is_set():
                return
            elapsed_ms = int(round((time.time() - started_at) * 1000))
            translated = (translated or "").strip()
            if not translated:
                self.signals.finished.emit(False, "翻译接口返回空结果")
            elif translated.startswith("[翻译") or translated.startswith("[未翻译]"):
                self.signals.finished.emit(False, translated)
            else:
                self.signals.finished.emit(True, f"测试成功：{translated}\n耗时：{elapsed_ms} ms")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.signals.finished.emit(False, f"测试失败：{str(e)[:220]}")
        finally:
            try:
                loop.run_until_complete(translator.close())
            except Exception:
                pass
            loop.close()


class AudioTestSignals(QObject):
    level = pyqtSignal(dict)


class AudioTestPanel(QWidget):
    def __init__(
        self,
        get_audio_config: Callable[[], AudioConfig],
        parent=None,
        ui_language: str = UI_LANGUAGE_ZH,
    ):
        super().__init__(parent)
        self._get_audio_config = get_audio_config
        self._ui_language = normalize_ui_language(ui_language)
        self._monitor: Optional[AudioLevelMonitor] = None
        self._signals = AudioTestSignals()
        self._signals.level.connect(self._handle_level_update)
        self._init_ui()

    def set_ui_language(self, ui_language: str):
        self._ui_language = normalize_ui_language(ui_language)
        self.start_button.setText(_tr(self._ui_language, "测试音频", "Test Audio"))
        self.stop_button.setText(_tr(self._ui_language, "停止", "Stop"))
        if not self._monitor:
            self.device_label.setText(_tr(self._ui_language, "当前设备：未测试", "Current device: not tested"))
            self.status_label.setText(_tr(
                self._ui_language,
                "播放游戏、Discord 或视频声音后，音量条应该跳动。",
                "Play game, Discord, or video audio; the level meter should move.",
            ))

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        button_row = QHBoxLayout()
        self.start_button = QPushButton(_tr(self._ui_language, "测试音频", "Test Audio"))
        self.stop_button = QPushButton(_tr(self._ui_language, "停止", "Stop"))
        self.stop_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_test)
        self.stop_button.clicked.connect(self.stop_test)
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.stop_button)
        button_row.addStretch()

        self.device_label = QLabel(_tr(self._ui_language, "当前设备：未测试", "Current device: not tested"))
        self.level_bar = QProgressBar()
        self.level_bar.setRange(0, 100)
        self.level_bar.setValue(0)
        self.status_label = QLabel(_tr(
            self._ui_language,
            "播放游戏、Discord 或视频声音后，音量条应该跳动。",
            "Play game, Discord, or video audio; the level meter should move.",
        ))
        self.status_label.setWordWrap(True)

        layout.addLayout(button_row)
        layout.addWidget(self.device_label)
        layout.addWidget(self.level_bar)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    def start_test(self):
        if not self.stop_test():
            return
        self.level_bar.setValue(0)
        self.status_label.setText(_tr(self._ui_language, "正在打开音频设备...", "Opening audio device..."))
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        try:
            config = _copy_audio_config(self._get_audio_config())
            self._monitor = AudioLevelMonitor(config, self._signals.level.emit)
            self._monitor.start()
            self.status_label.setText(_tr(
                self._ui_language,
                "正在监听声音，播放游戏/视频/Discord 后观察音量条。",
                "Listening. Play game, video, or Discord audio and watch the meter.",
            ))
        except Exception as e:
            if self._monitor and not self.stop_test():
                return
            if isinstance(e, AudioRecoveryInProgress):
                self.status_label.setText(_tr(
                    self._ui_language,
                    "音频设备正在恢复，请稍后再测试。",
                    "Audio device is recovering. Please test again shortly.",
                ))
            else:
                self.status_label.setText(_tr(
                    self._ui_language,
                    f"音频测试失败：{str(e)[:220]}",
                    f"Audio test failed: {str(e)[:220]}",
                ))

    def stop_test(self):
        if self._monitor:
            try:
                self._monitor.stop()
            except Exception:
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.status_label.setText(_tr(
                    self._ui_language,
                    "音频测试尚未停止，请重试。",
                    "Audio test has not stopped. Please try again.",
                ))
                return False
            self._monitor = None
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        return True

    def _handle_level_update(self, payload: dict):
        if payload.get("recovery"):
            if self._monitor is None or id(self._monitor) != payload.get("monitor_token"):
                return
            self._monitor = None
            self.level_bar.setValue(0)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText(_tr(
                self._ui_language,
                "音频测试已因设备恢复停止。",
                "Audio test stopped while the device was recovering.",
            ))
            return
        if payload.get("error"):
            self.status_label.setText(_tr(
                self._ui_language,
                f"音频读取失败：{payload.get('error')}",
                f"Audio read failed: {payload.get('error')}",
            ))
            self.stop_test()
            return
        rms = float(payload.get("rms_dbfs", -120.0))
        peak = float(payload.get("peak_dbfs", -120.0))
        detected = bool(payload.get("detected"))
        value = int(max(0, min(100, (rms + 70.0) / 70.0 * 100.0)))
        self.level_bar.setValue(value)
        device = payload.get("device") or {}
        if device:
            self.device_label.setText(
                _tr(self._ui_language, "当前设备：", "Current device: ")
                + f"{device.get('type', 'Audio')} [{device.get('index')}] "
                + f"{device.get('name', '')} ({device.get('sample_rate')}Hz/{device.get('channels')}ch)"
            )
        if is_english_ui(self._ui_language):
            state = "Sound detected" if detected else "No clear sound yet"
            self.status_label.setText(f"{state}. Current {rms:.1f} dBFS, peak {peak:.1f} dBFS.")
        else:
            state = "检测到声音" if detected else "暂未检测到明显声音"
            self.status_label.setText(f"{state}。当前 {rms:.1f} dBFS，峰值 {peak:.1f} dBFS。")

    def close(self):
        self.stop_test()
        super().close()

class ColorButton(QPushButton):
    """Small color picker button."""

    color_changed = pyqtSignal(str)

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedWidth(80)
        self.clicked.connect(self._pick_color)
        self._refresh()

    def color(self) -> str:
        return self._color

    def set_color(self, color: str):
        self._color = color
        self._refresh()

    def _refresh(self):
        self.setText(self._color)
        self.setStyleSheet(f"""
            QPushButton {{
                color: #FFFFFF;
                background: {self._color};
                border: 1px solid #7D8794;
                border-radius: 4px;
                padding: 4px 6px;
            }}
        """)

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._color), self, "选择颜色")
        if color.isValid():
            self.set_color(color.name().upper())
            self.color_changed.emit(self._color)


class HotkeyCaptureEdit(QLineEdit):
    """Line edit that records the next pressed key combination."""

    hotkey_changed = pyqtSignal(str)

    MODIFIER_NAMES = [
        (Qt.ControlModifier, "ctrl"),
        (Qt.AltModifier, "alt"),
        (Qt.ShiftModifier, "shift"),
        (Qt.MetaModifier, "windows"),
    ]

    KEY_NAMES = {
        Qt.Key_Escape: "esc",
        Qt.Key_Space: "space",
        Qt.Key_Tab: "tab",
        Qt.Key_Backspace: "backspace",
        Qt.Key_Delete: "delete",
        Qt.Key_Return: "enter",
        Qt.Key_Enter: "enter",
    }

    def __init__(self, value: str, parent=None):
        super().__init__(value, parent)
        self.setReadOnly(True)
        self.setPlaceholderText("点击后按快捷键")
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        self.setText("请按快捷键...")
        self.selectAll()
        self.setFocus(Qt.MouseFocusReason)
        event.accept()

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Escape, Qt.Key_Backspace, Qt.Key_Delete):
            self.clear()
            self.hotkey_changed.emit("")
            return
        if key in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta):
            return
        hotkey = self._event_to_hotkey(event)
        if hotkey:
            self.setText(hotkey)
            self.hotkey_changed.emit(hotkey)

    def _event_to_hotkey(self, event) -> str:
        parts = []
        modifiers = event.modifiers()
        for modifier, name in self.MODIFIER_NAMES:
            if modifiers & modifier:
                parts.append(name)
        key_name = self.KEY_NAMES.get(event.key())
        if not key_name:
            text = event.text().lower()
            if text and text.isprintable():
                key_name = text
            elif Qt.Key_F1 <= event.key() <= Qt.Key_F35:
                key_name = f"f{event.key() - Qt.Key_F1 + 1}"
            else:
                key_name = event.keyCombination().key().name.lower()
        if not key_name:
            return ""
        parts.append(key_name)
        return "+".join(parts)

class OverlayLockButton(QToolButton):
    """Separate top-level button so the overlay can be mouse-transparent while locked."""

    def __init__(self, owner):
        super().__init__(None)
        self._owner = owner
        flags = Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
        if hasattr(Qt, "WindowDoesNotAcceptFocus"):
            flags |= Qt.WindowDoesNotAcceptFocus
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setObjectName("floatingLockButton")
        self.setFixedSize(28, 24)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.clicked.connect(owner._toggle_lock)

    def closeEvent(self, event):
        event.accept()
