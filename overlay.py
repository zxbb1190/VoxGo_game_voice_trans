"""
游戏浮窗叠加层
使用 PyQt5 创建透明置顶窗口，显示翻译结果
"""

import ctypes
import socket
import sys
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, List, Optional

from PyQt5.QtCore import (
    Qt, QEvent, QPoint, QRect, QTimer, pyqtSignal, QObject
)
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush, QIcon, QPixmap, QTextDocument,
)
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QApplication, QPushButton, QFrame, QDialog, QFormLayout,
    QSlider, QCheckBox, QLineEdit, QColorDialog, QToolButton, QComboBox,
    QSpinBox, QSizePolicy, QScrollArea
)

from app_info import APP_NAME
from qr_widget import QrCodeWidget
from translator import TranslationConfig, TRANSLATION_PROVIDERS, normalize_translation_provider


LANGUAGE_OPTIONS = (("en", "英语"), ("zh", "中文"))
LANGUAGE_LABELS = dict(LANGUAGE_OPTIONS)
OPPOSITE_LANGUAGE = {"en": "zh", "zh": "en"}
WHISPER_DEVICE_OPTIONS = (
    ("cpu", "CPU（推荐）"),
    ("auto", "自动检测"),
    ("cuda", "NVIDIA GPU / CUDA"),
)
WHISPER_DEVICE_LABELS = dict(WHISPER_DEVICE_OPTIONS)
WHISPER_DOWNLOAD_SOURCE_OPTIONS = (
    ("modelscope", "ModelScope 国内源（推荐）"),
    ("huggingface", "官方 Hugging Face"),
    ("custom_hf_endpoint", "自定义 Hugging Face Endpoint"),
)


def _normalize_language_code(value: str, default: str = "en") -> str:
    value = (value or "").strip().lower()
    aliases = {
        "english": "en",
        "eng": "en",
        "英语": "en",
        "chinese": "zh",
        "zh-cn": "zh",
        "zh-tw": "zh",
        "cmn": "zh",
        "中文": "zh",
    }
    value = aliases.get(value, value)
    return value if value in LANGUAGE_LABELS else default


def _normalize_whisper_device(value: str) -> str:
    value = (value or "").strip().lower()
    aliases = {
        "gpu": "cuda",
        "nvidia": "cuda",
        "nvidia gpu": "cuda",
        "自动": "auto",
        "自动检测": "auto",
    }
    value = aliases.get(value, value)
    return value if value in WHISPER_DEVICE_LABELS else "cpu"


def _normalize_model_download_endpoint(value: str) -> str:
    endpoint = (value or "").strip()
    if endpoint.lower() in ("official", "huggingface", "huggingface.co", "default", "none"):
        return ""
    if not endpoint:
        return ""
    aliases = {
        "hf-mirror": "https://hf-mirror.com",
        "hf-mirror.com": "https://hf-mirror.com",
        "mirror": "https://hf-mirror.com",
        "china": "https://hf-mirror.com",
        "cn": "https://hf-mirror.com",
    }
    endpoint = aliases.get(endpoint.lower(), endpoint)
    endpoint = endpoint.rstrip("/")
    if endpoint in ("https://huggingface.co", "http://huggingface.co"):
        return ""
    if not endpoint.startswith(("http://", "https://")):
        endpoint = "https://" + endpoint
    return endpoint.rstrip("/")


def _normalize_model_download_source(value: str, endpoint: str = "") -> str:
    source = (value or "").strip().lower().replace("-", "_")
    normalized_endpoint = _normalize_model_download_endpoint(endpoint)
    if not source and normalized_endpoint:
        return "custom_hf_endpoint"
    aliases = {
        "": "modelscope",
        "default": "modelscope",
        "china": "modelscope",
        "cn": "modelscope",
        "domestic": "modelscope",
        "modelscope": "modelscope",
        "model_scope": "modelscope",
        "ms": "modelscope",
        "official": "huggingface",
        "huggingface": "huggingface",
        "hugging_face": "huggingface",
        "hf": "huggingface",
        "custom": "custom_hf_endpoint",
        "custom_hf": "custom_hf_endpoint",
        "custom_huggingface": "custom_hf_endpoint",
        "custom_hugging_face": "custom_hf_endpoint",
        "custom_hf_endpoint": "custom_hf_endpoint",
    }
    normalized = aliases.get(source, source)
    if normalized not in {"modelscope", "huggingface", "custom_hf_endpoint"}:
        normalized = "custom_hf_endpoint" if normalized_endpoint else "modelscope"
    if normalized == "huggingface" and normalized_endpoint:
        return "custom_hf_endpoint"
    if normalized == "custom_hf_endpoint" and not normalized_endpoint:
        return "huggingface"
    return normalized


@dataclass
class OverlayConfig:
    font_size: int = 16
    font_family: str = "Microsoft YaHei"
    text_color: str = "#00FF00"
    bg_color: str = "#20242A"
    bg_opacity: float = 0.82
    position: str = "bottom"
    max_lines: int = 5
    fade_duration: int = 5
    window_width: int = 500
    window_height: int = 200
    opacity: float = 0.85
    original_text_color: str = "#B7C4D8"
    show_original: bool = True
    draggable: bool = True
    locked: bool = False
    mobile_url: str = ""


@dataclass
class HotkeyConfig:
    toggle_overlay: str = "ctrl+shift+t"
    toggle_translation: str = "ctrl+alt+s"
    clear_history: str = "ctrl+alt+c"


@dataclass
class AudioDeviceConfig:
    input_device_index: Optional[int] = None
    input_device_name: str = ""
    input_device_id: str = ""
    max_speech_seconds: float = 8.0


@dataclass
class WhisperDeviceConfig:
    device: str = "cpu"
    model_download_source: str = "modelscope"
    model_download_endpoint: str = ""


class TranslationItem:
    """单条翻译记录"""

    def __init__(
        self,
        original: str,
        translated: str,
        fade_duration: int,
        timestamp: float = None,
        item_id: str = "",
    ):
        self.item_id = item_id
        self.original = original
        self.translated = translated
        self.fade_duration = max(1, fade_duration)
        self.timestamp = timestamp or time.time()
        self.fade_start = None

    def start_fade(self):
        self.fade_start = time.time()

    @property
    def opacity(self) -> float:
        if self.fade_start is None:
            return 1.0
        elapsed = time.time() - self.fade_start
        return max(0.0, 1.0 - elapsed / self.fade_duration)


class OverlaySignals(QObject):
    """信号类，用于线程安全更新"""
    new_translation = pyqtSignal(str, str)
    new_translation_with_id = pyqtSignal(str, str, str)
    update_translation = pyqtSignal(str, str)
    clear_history = pyqtSignal()
    toggle_visibility = pyqtSignal()
    settings_changed = pyqtSignal(object, object, object, object, object)
    refresh_audio_devices = pyqtSignal()


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


def _make_icon(kind: str, color: str) -> QIcon:
    pixmap = QPixmap(28, 28)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color), 2)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    if kind == "qr":
        for rect in (QRect(5, 5, 6, 6), QRect(17, 5, 6, 6), QRect(5, 17, 6, 6)):
            painter.drawRect(rect)
            painter.fillRect(rect.adjusted(2, 2, -2, -2), QColor(color))
        painter.fillRect(QRect(17, 17, 3, 3), QColor(color))
        painter.fillRect(QRect(21, 21, 3, 3), QColor(color))
        painter.fillRect(QRect(17, 23, 7, 2), QColor(color))
    elif kind == "settings":
        painter.drawEllipse(QPoint(14, 14), 4, 4)
        for angle in range(0, 360, 45):
            painter.save()
            painter.translate(14, 14)
            painter.rotate(angle)
            painter.drawLine(0, -11, 0, -8)
            painter.restore()
        painter.drawEllipse(QPoint(14, 14), 10, 10)
    elif kind in ("lock", "unlock"):
        painter.drawRoundedRect(QRect(7, 12, 16, 11), 2, 2)
        if kind == "lock":
            painter.drawArc(QRect(9, 4, 12, 15), 0, 180 * 16)
        else:
            painter.drawArc(QRect(13, 4, 12, 15), 35 * 16, 185 * 16)
            painter.drawLine(10, 12, 10, 10)
        painter.drawLine(14, 16, 14, 19)
    elif kind == "swap":
        painter.drawLine(7, 10, 20, 10)
        painter.drawLine(17, 7, 20, 10)
        painter.drawLine(17, 13, 20, 10)
        painter.drawLine(21, 18, 8, 18)
        painter.drawLine(11, 15, 8, 18)
        painter.drawLine(11, 21, 8, 18)
    else:
        painter.drawLine(8, 8, 20, 20)
        painter.drawLine(20, 8, 8, 20)

    painter.end()
    return QIcon(pixmap)


class SettingsDialog(QDialog):
    """Graphical settings for overlay and hotkeys."""

    settings_changed = pyqtSignal(object, object, object, object, object)

    def __init__(
        self,
        overlay_config: OverlayConfig,
        hotkey_config: HotkeyConfig,
        audio_config: AudioDeviceConfig = None,
        translation_config: TranslationConfig = None,
        audio_devices: Optional[List[dict]] = None,
        whisper_config=None,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("浮窗设置")
        self.setWindowFlags(self.windowFlags() | Qt.Tool)
        self.overlay_config = overlay_config
        self.hotkey_config = hotkey_config
        self.audio_config = audio_config or AudioDeviceConfig()
        self.translation_config = translation_config or TranslationConfig()
        self.audio_devices = audio_devices or []
        self.whisper_config = whisper_config or WhisperDeviceConfig()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setValue(int(self.overlay_config.opacity * 100))
        self.opacity_label = QLabel(f"{self.opacity_slider.value()}%")
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(self.opacity_slider)
        opacity_row.addWidget(self.opacity_label)
        self.opacity_slider.valueChanged.connect(lambda value: self.opacity_label.setText(f"{value}%"))
        self.opacity_slider.valueChanged.connect(self._preview)
        form.addRow("整体透明度", opacity_row)

        self.bg_opacity_slider = QSlider(Qt.Horizontal)
        self.bg_opacity_slider.setRange(20, 100)
        self.bg_opacity_slider.setValue(int(float(getattr(self.overlay_config, "bg_opacity", 0.82)) * 100))
        self.bg_opacity_label = QLabel(f"{self.bg_opacity_slider.value()}%")
        bg_opacity_row = QHBoxLayout()
        bg_opacity_row.addWidget(self.bg_opacity_slider)
        bg_opacity_row.addWidget(self.bg_opacity_label)
        self.bg_opacity_slider.valueChanged.connect(lambda value: self.bg_opacity_label.setText(f"{value}%"))
        self.bg_opacity_slider.valueChanged.connect(self._preview)
        form.addRow("背景透明度", bg_opacity_row)

        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setRange(12, 30)
        self.font_slider.setValue(self.overlay_config.font_size)
        self.font_label = QLabel(f"{self.font_slider.value()}px")
        font_row = QHBoxLayout()
        font_row.addWidget(self.font_slider)
        font_row.addWidget(self.font_label)
        self.font_slider.valueChanged.connect(lambda value: self.font_label.setText(f"{value}px"))
        self.font_slider.valueChanged.connect(self._preview)
        form.addRow("字号", font_row)

        self.text_color_btn = ColorButton(self.overlay_config.text_color)
        self.text_color_btn.color_changed.connect(self._preview)
        form.addRow("译文颜色", self.text_color_btn)

        self.original_color_btn = ColorButton(self.overlay_config.original_text_color)
        self.original_color_btn.color_changed.connect(self._preview)
        form.addRow("原文颜色", self.original_color_btn)

        self.show_original_check = QCheckBox("显示英文原文")
        self.show_original_check.setChecked(self.overlay_config.show_original)
        self.show_original_check.stateChanged.connect(self._preview)
        form.addRow("中英对照", self.show_original_check)

        self.provider_combo = QComboBox()
        self.provider_combo.setToolTip("OpenAI 兼容适合硅基流动、DeepSeek、Qwen、GLM 和本地模型；Google 使用 Cloud Translation Basic v2")
        self._fill_translation_providers()
        self.provider_combo.currentIndexChanged.connect(self._provider_changed)
        form.addRow("翻译服务", self.provider_combo)

        self.api_key_input = QLineEdit(self.translation_config.api_key)
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("OpenAI 兼容 API Key")
        self.api_key_input.setToolTip("硅基流动、DeepSeek、Qwen、GLM 或本地兼容服务的 API Key；本地服务不需要时可留空")
        self.api_key_input.editingFinished.connect(self._preview)
        form.addRow("API Key", self.api_key_input)

        self.model_input = QLineEdit(self.translation_config.model)
        self.model_input.setPlaceholderText("tencent/Hunyuan-MT-7B")
        self.model_input.setToolTip("填写服务商要求的模型名，例如 tencent/Hunyuan-MT-7B、deepseek-chat、qwen-plus、glm-4-flash")
        self.model_input.editingFinished.connect(self._preview)
        form.addRow("模型名", self.model_input)

        self.endpoint_input = QLineEdit(self.translation_config.endpoint)
        self.endpoint_input.setPlaceholderText("https://api.siliconflow.cn/v1/chat/completions")
        self.endpoint_input.setToolTip("填写 OpenAI 兼容地址；可填完整 /chat/completions URL，也可填以 /v1 结尾的 base_url")
        self.endpoint_input.editingFinished.connect(self._preview)
        form.addRow("兼容地址", self.endpoint_input)
        self._refresh_translation_provider_ui()

        self.whisper_device_combo = QComboBox()
        self.whisper_device_combo.setToolTip("普通用户选 CPU；自动/GPU 需要本机有可用 NVIDIA CUDA 运行环境")
        self._fill_whisper_devices()
        self.whisper_device_combo.currentIndexChanged.connect(self._preview)
        form.addRow("识别设备", self.whisper_device_combo)

        self.model_download_source_combo = QComboBox()
        self.model_download_source_combo.setToolTip("lite 包首次运行会下载 Whisper 模型；大陆网络推荐 ModelScope 国内源")
        self.model_download_endpoint_input = QLineEdit(
            _normalize_model_download_endpoint(getattr(self.whisper_config, "model_download_endpoint", ""))
        )
        self.model_download_endpoint_input.setPlaceholderText("https://your-hf-endpoint.example.com")
        self.model_download_endpoint_input.setToolTip("仅自定义 Hugging Face Endpoint 使用；ModelScope 不是 Hugging Face endpoint")
        self.model_download_endpoint_input.editingFinished.connect(self._preview)
        self._fill_model_download_sources()
        self.model_download_source_combo.currentIndexChanged.connect(self._download_source_changed)
        download_source_row = QHBoxLayout()
        download_source_row.addWidget(self.model_download_source_combo)
        download_source_row.addWidget(self.model_download_endpoint_input)
        form.addRow("模型下载源", download_source_row)

        self.audio_device_combo = QComboBox()
        self.audio_device_combo.setToolTip("优先选择 [系统声音] 或 Loopback；普通麦克风通常录不到游戏声音")
        self.refresh_audio_button = QPushButton("刷新")
        self._fill_audio_devices()
        audio_row = QHBoxLayout()
        audio_row.addWidget(self.audio_device_combo)
        audio_row.addWidget(self.refresh_audio_button)
        self.audio_device_combo.currentIndexChanged.connect(self._preview)
        self.refresh_audio_button.clicked.connect(self._request_audio_refresh)
        form.addRow("音频设备", audio_row)

        self.max_speech_seconds_spin = QSpinBox()
        self.max_speech_seconds_spin.setRange(3, 30)
        self.max_speech_seconds_spin.setSuffix(" 秒")
        self.max_speech_seconds_spin.setValue(
            int(round(float(getattr(self.audio_config, "max_speech_seconds", 8) or 8)))
        )
        self.max_speech_seconds_spin.setToolTip("连续有声超过这个时长会强制切成一段，推荐 6-10 秒")
        self.max_speech_seconds_spin.valueChanged.connect(self._preview)
        form.addRow("最长捕获", self.max_speech_seconds_spin)

        self.toggle_overlay_input = HotkeyCaptureEdit(self.hotkey_config.toggle_overlay)
        self.toggle_translation_input = HotkeyCaptureEdit(self.hotkey_config.toggle_translation)
        self.clear_history_input = HotkeyCaptureEdit(self.hotkey_config.clear_history)
        self.toggle_overlay_input.hotkey_changed.connect(self._preview)
        self.toggle_translation_input.hotkey_changed.connect(self._preview)
        self.clear_history_input.hotkey_changed.connect(self._preview)
        form.addRow("显示/隐藏", self.toggle_overlay_input)
        form.addRow("暂停/恢复", self.toggle_translation_input)
        form.addRow("清空历史", self.clear_history_input)

        layout.addLayout(form)

        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        self.setLayout(layout)
        self.resize(700, 540)

    def closeEvent(self, event):
        self._preview()
        super().closeEvent(event)

    def _fill_audio_devices(self):
        self.audio_device_combo.blockSignals(True)
        self.audio_device_combo.clear()
        self.audio_device_combo.addItem("自动选择", None)
        selected_row = 0
        selected_index = self.audio_config.input_device_index
        selected_name = (self.audio_config.input_device_name or "").strip()
        selected_device_id = (getattr(self.audio_config, "input_device_id", "") or "").strip()
        for row, device in enumerate(self.audio_devices, start=1):
            index = device.get("index")
            name = device.get("name", "")
            device_id = (device.get("device_id") or "").strip()
            sample_rate = device.get("sample_rate") or 0
            channels = device.get("channels") or 0
            device_type = "系统声音" if device.get("is_loopback") else "输入设备"
            label = f"[{device_type}] [{index}] {name} ({sample_rate}Hz/{channels}ch)"
            self.audio_device_combo.addItem(label, device)
            if selected_device_id and selected_device_id == device_id:
                selected_row = row
            elif selected_row == 0 and selected_name and selected_name == name:
                selected_row = row
            elif selected_row == 0 and not selected_name and selected_index is not None and int(selected_index) == int(index):
                selected_row = row
        self.audio_device_combo.setCurrentIndex(selected_row)
        self.audio_device_combo.blockSignals(False)

    def _fill_whisper_devices(self):
        self.whisper_device_combo.blockSignals(True)
        self.whisper_device_combo.clear()
        selected_device = _normalize_whisper_device(getattr(self.whisper_config, "device", "cpu"))
        selected_row = 0
        for row, (device, label) in enumerate(WHISPER_DEVICE_OPTIONS):
            self.whisper_device_combo.addItem(label, device)
            if device == selected_device:
                selected_row = row
        self.whisper_device_combo.setCurrentIndex(selected_row)
        self.whisper_device_combo.blockSignals(False)

    def _fill_model_download_sources(self):
        self.model_download_source_combo.blockSignals(True)
        self.model_download_source_combo.clear()
        selected_source = _normalize_model_download_source(
            getattr(self.whisper_config, "model_download_source", "modelscope"),
            getattr(self.whisper_config, "model_download_endpoint", ""),
        )
        selected_endpoint = _normalize_model_download_endpoint(
            getattr(self.whisper_config, "model_download_endpoint", "")
        )
        selected_row = 0
        for row, (source, label) in enumerate(WHISPER_DOWNLOAD_SOURCE_OPTIONS):
            self.model_download_source_combo.addItem(label, source)
            if source == selected_source:
                selected_row = row
        self.model_download_source_combo.setCurrentIndex(selected_row)
        self.model_download_source_combo.blockSignals(False)
        self._refresh_model_download_source_ui()

    def _download_source_changed(self, *args):
        self._refresh_model_download_source_ui()
        self._preview()

    def _refresh_model_download_source_ui(self):
        selected = self.model_download_source_combo.currentData()
        is_custom = selected == "custom_hf_endpoint"
        self.model_download_endpoint_input.setEnabled(is_custom)
        if not is_custom:
            self.model_download_endpoint_input.setText("")

    def _fill_translation_providers(self):
        self.provider_combo.blockSignals(True)
        self.provider_combo.clear()
        selected_provider = normalize_translation_provider(
            getattr(self.translation_config, "provider", "openai_compatible")
        )
        selected_row = 0
        for row, (provider, label) in enumerate(TRANSLATION_PROVIDERS.items()):
            self.provider_combo.addItem(label, provider)
            if provider == selected_provider:
                selected_row = row
        self.provider_combo.setCurrentIndex(selected_row)
        self.provider_combo.blockSignals(False)

    def _provider_changed(self, *args):
        self._refresh_translation_provider_ui()
        self._preview()

    def _refresh_translation_provider_ui(self):
        if not hasattr(self, "provider_combo"):
            return
        provider = normalize_translation_provider(self.provider_combo.currentData())
        is_google = provider == "google"
        if hasattr(self, "api_key_input"):
            self.api_key_input.setPlaceholderText(
                "Google Cloud Translation API Key" if is_google else "OpenAI 兼容 API Key"
            )
            self.api_key_input.setToolTip(
                "Google Cloud 项目中启用 Cloud Translation API 后创建的 API Key"
                if is_google
                else "硅基流动、DeepSeek、Qwen、GLM 或本地兼容服务的 API Key；本地服务不需要时可留空"
            )
        for widget in (getattr(self, "model_input", None), getattr(self, "endpoint_input", None)):
            if widget:
                widget.setEnabled(not is_google)
        if hasattr(self, "model_input"):
            self.model_input.setToolTip(
                "Google Cloud Translation Basic v2 不需要模型名"
                if is_google
                else "填写服务商要求的模型名，例如 tencent/Hunyuan-MT-7B、deepseek-chat、qwen-plus、glm-4-flash"
            )
        if hasattr(self, "endpoint_input"):
            self.endpoint_input.setToolTip(
                "Google Cloud Translation Basic v2 使用固定官方接口，不需要填写兼容地址"
                if is_google
                else "填写 OpenAI 兼容地址；可填完整 /chat/completions URL，也可填以 /v1 结尾的 base_url"
            )

    def set_audio_devices(self, audio_devices: List[dict], audio_config: AudioDeviceConfig):
        self.audio_devices = audio_devices or []
        self.audio_config = audio_config
        self._fill_audio_devices()
        if hasattr(self, "max_speech_seconds_spin"):
            self.max_speech_seconds_spin.blockSignals(True)
            self.max_speech_seconds_spin.setValue(
                int(round(float(getattr(self.audio_config, "max_speech_seconds", 8) or 8)))
            )
            self.max_speech_seconds_spin.blockSignals(False)

    def _request_audio_refresh(self):
        parent = self.parent()
        if parent and hasattr(parent, "request_audio_device_refresh"):
            parent.request_audio_device_refresh()

    def _preview(self, *args):
        self._collect_values()
        self.settings_changed.emit(
            self.overlay_config,
            self.hotkey_config,
            self.audio_config,
            self.translation_config,
            self.whisper_config,
        )

    def _collect_values(self):
        self.overlay_config.opacity = self.opacity_slider.value() / 100
        self.overlay_config.bg_opacity = self.bg_opacity_slider.value() / 100
        self.overlay_config.font_size = self.font_slider.value()
        self.overlay_config.text_color = self.text_color_btn.color()
        self.overlay_config.original_text_color = self.original_color_btn.color()
        self.overlay_config.show_original = self.show_original_check.isChecked()

        self.hotkey_config.toggle_overlay = self.toggle_overlay_input.text().strip() or self.hotkey_config.toggle_overlay
        self.hotkey_config.toggle_translation = self.toggle_translation_input.text().strip() or self.hotkey_config.toggle_translation
        self.hotkey_config.clear_history = self.clear_history_input.text().strip() or self.hotkey_config.clear_history

        self.translation_config.provider = normalize_translation_provider(self.provider_combo.currentData())
        self.translation_config.api_key = self.api_key_input.text().strip()
        self.translation_config.model = self.model_input.text().strip() or self.translation_config.model
        self.translation_config.endpoint = self.endpoint_input.text().strip() or self.translation_config.endpoint
        self.whisper_config.device = _normalize_whisper_device(self.whisper_device_combo.currentData())
        selected_download_source = self.model_download_source_combo.currentData()
        self.whisper_config.model_download_source = _normalize_model_download_source(
            selected_download_source,
            self.model_download_endpoint_input.text(),
        )
        if self.whisper_config.model_download_source == "custom_hf_endpoint":
            self.whisper_config.model_download_endpoint = _normalize_model_download_endpoint(
                self.model_download_endpoint_input.text()
            )
        else:
            self.whisper_config.model_download_endpoint = ""

        device = self.audio_device_combo.currentData()
        if device:
            self.audio_config.input_device_index = int(device.get("index"))
            self.audio_config.input_device_name = device.get("name", "")
            self.audio_config.input_device_id = device.get("device_id", "")
        else:
            self.audio_config.input_device_index = None
            self.audio_config.input_device_name = ""
            self.audio_config.input_device_id = ""
        self.audio_config.max_speech_seconds = float(self.max_speech_seconds_spin.value())


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


class GameOverlay(QWidget):
    """游戏浮窗叠加层"""

    def __init__(
        self,
        config: OverlayConfig = None,
        hotkeys: HotkeyConfig = None,
        audio_config: AudioDeviceConfig = None,
        translation_config: TranslationConfig = None,
        audio_devices: Optional[List[dict]] = None,
        whisper_config=None,
        on_settings_changed: Optional[Callable[[OverlayConfig, HotkeyConfig, AudioDeviceConfig, TranslationConfig, object], None]] = None,
        on_audio_devices_refresh: Optional[Callable[[], List[dict]]] = None,
        on_shutdown_requested: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.config = config or OverlayConfig()
        self.hotkeys = hotkeys or HotkeyConfig()
        self.audio_config = audio_config or AudioDeviceConfig()
        self.translation_config = translation_config or TranslationConfig()
        self.audio_devices = audio_devices or []
        self.whisper_config = whisper_config or WhisperDeviceConfig()
        self._on_settings_changed = on_settings_changed
        self._on_audio_devices_refresh = on_audio_devices_refresh
        self._on_shutdown_requested = on_shutdown_requested
        self._translations: deque = deque(maxlen=self.config.max_lines)
        self._signals = OverlaySignals()
        self._dragging = False
        self._drag_pos = None
        self._resizing = False
        self._resize_start_pos = None
        self._resize_start_size = None
        self._syncing_language_controls = False
        self._settings_dialog = None
        self._fade_timer = QTimer()
        self._fade_timer.timeout.connect(self._update_fade)
        self._fade_timer.start(100)

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """初始化界面"""
        # 窗口属性
        self.setWindowTitle(APP_NAME)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # 窗口大小和位置
        screen = QApplication.primaryScreen().geometry()
        self.resize(self.config.window_width, self.config.window_height)

        if self.config.position == "bottom":
            x = (screen.width() - self.config.window_width) // 2
            y = screen.height() - self.config.window_height - 50
        elif self.config.position == "top":
            x = (screen.width() - self.config.window_width) // 2
            y = 50
        elif self.config.position == "right":
            x = screen.width() - self.config.window_width - 20
            y = (screen.height() - self.config.window_height) // 2
        else:
            x = (screen.width() - self.config.window_width) // 2
            y = screen.height() - self.config.window_height - 50

        self.move(x, y)

        # 主布局
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(10, 8, 10, 10)
        self._layout.setSpacing(6)
        self.setLayout(self._layout)

        # 顶部工具条
        self._toolbar = QFrame()
        self._toolbar.setObjectName("toolbar")
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(2, 0, 2, 0)
        toolbar_layout.setSpacing(6)
        self._toolbar.setLayout(toolbar_layout)

        self._title_label = QLabel("实时翻译")
        self._title_label.setObjectName("title")
        toolbar_layout.addWidget(self._title_label)

        self._source_lang_combo = self._create_language_combo("识别语言")
        self._source_lang_combo.setObjectName("languageCombo")
        toolbar_layout.addWidget(self._source_lang_combo)

        self._swap_lang_button = QToolButton()
        self._swap_lang_button.setObjectName("languageSwapButton")
        self._swap_lang_button.setIcon(_make_icon("swap", self.config.original_text_color))
        self._swap_lang_button.setToolTip("交换识别语言和翻译目标语言")
        self._swap_lang_button.setFixedSize(28, 24)
        self._swap_lang_button.setCursor(Qt.PointingHandCursor)
        self._swap_lang_button.clicked.connect(self._swap_language_flow)
        toolbar_layout.addWidget(self._swap_lang_button)

        self._target_lang_combo = self._create_language_combo("翻译目标语言")
        self._target_lang_combo.setObjectName("languageCombo")
        toolbar_layout.addWidget(self._target_lang_combo)
        self._sync_language_controls()
        self._source_lang_combo.currentIndexChanged.connect(self._language_combo_changed)
        self._target_lang_combo.currentIndexChanged.connect(self._language_combo_changed)

        toolbar_layout.addStretch()

        self._qr_button = QToolButton()
        self._qr_button.setObjectName("qrButton")
        self._qr_button.setIcon(_make_icon("qr", self.config.text_color))
        self._qr_button.setToolTip("手机二维码")
        self._qr_button.setFixedSize(28, 24)
        self._qr_button.setCursor(Qt.PointingHandCursor)
        self._qr_button.installEventFilter(self)
        toolbar_layout.addWidget(self._qr_button)

        self._settings_button = QToolButton()
        self._settings_button.setObjectName("settingsButton")
        self._settings_button.setIcon(_make_icon("settings", self.config.text_color))
        self._settings_button.setToolTip("浮窗设置")
        self._settings_button.setFixedSize(28, 24)
        self._settings_button.setCursor(Qt.PointingHandCursor)
        self._settings_button.clicked.connect(self._open_settings)
        toolbar_layout.addWidget(self._settings_button)

        self._quit_button = QToolButton()
        self._quit_button.setObjectName("quitButton")
        self._quit_button.setIcon(_make_icon("close", self.config.text_color))
        self._quit_button.setToolTip("退出程序")
        self._quit_button.setFixedSize(28, 24)
        self._quit_button.setCursor(Qt.PointingHandCursor)
        self._quit_button.clicked.connect(self._request_shutdown)
        toolbar_layout.addWidget(self._quit_button)

        self._lock_slot = QWidget()
        self._lock_slot.setFixedSize(28, 24)
        toolbar_layout.addWidget(self._lock_slot)
        self._layout.addWidget(self._toolbar)

        self._lock_button = OverlayLockButton(self)

        self._qr_popup = QFrame(self)
        self._qr_popup.setObjectName("qrPopup")
        qr_layout = QVBoxLayout()
        qr_layout.setContentsMargins(8, 8, 8, 8)
        qr_layout.setSpacing(6)
        self._qr_popup.setLayout(qr_layout)
        self._qr_widget = QrCodeWidget(parent=self._qr_popup)
        self._qr_url_label = QLabel()
        self._qr_url_label.setObjectName("qrUrl")
        self._qr_url_label.setAlignment(Qt.AlignCenter)
        self._qr_url_label.setWordWrap(True)
        qr_layout.addWidget(self._qr_widget)
        qr_layout.addWidget(self._qr_url_label)
        self._qr_popup.hide()
        self._setup_qr_code()

        # 翻译内容容器
        self._scroll_area = QScrollArea()
        self._scroll_area.setObjectName("translationScrollArea")
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.NoFrame)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._content_widget = QWidget()
        self._content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._content_layout = QVBoxLayout()
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(4)
        self._content_widget.setLayout(self._content_layout)
        self._scroll_area.setWidget(self._content_widget)
        self._layout.addWidget(self._scroll_area, 1)
        self._content_layout.addStretch(1)

        # 翻译标签池
        self._labels: List[QLabel] = []
        for i in range(self.config.max_lines):
            label = QLabel()
            label.setWordWrap(True)
            label.setTextFormat(Qt.RichText)
            label.setTextInteractionFlags(Qt.NoTextInteraction)
            label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            label.setContentsMargins(0, 0, 0, 0)
            label.setMinimumWidth(0)
            label.hide()
            self._content_layout.addWidget(label)
            self._labels.append(label)

        self.setMinimumSize(360, 150)
        self.setMaximumSize(980, 520)

        # 设置窗口透明度
        self.setWindowOpacity(self.config.opacity)
        self._apply_styles()
        self._refresh_lock_state()
        QTimer.singleShot(0, self._position_lock_button)

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QLabel {{
                font-family: "{self.config.font_family}";
            }}
            QLabel#title {{
                color: {self.config.original_text_color};
                font-size: {max(10, self.config.font_size - 4)}px;
                padding: 0 2px;
            }}
            QComboBox#languageCombo {{
                color: {self.config.original_text_color};
                background: transparent;
                border: 0;
                padding: 1px 9px 1px 1px;
                font-size: {max(10, self.config.font_size - 3)}px;
            }}
            QComboBox#languageCombo:hover {{
                background: rgba(255, 255, 255, 24);
            }}
            QComboBox#languageCombo::drop-down {{
                border: 0;
                width: 10px;
            }}
            QToolButton#languageSwapButton {{
                background: transparent;
                border: 0;
                border-radius: 4px;
            }}
            QToolButton#languageSwapButton:hover {{
                background: rgba(255, 255, 255, 28);
            }}
            QToolButton#qrButton, QToolButton#settingsButton, QToolButton#quitButton {{
                background: rgba(18, 24, 33, 150);
                border: 1px solid {self.config.text_color};
                border-radius: 4px;
            }}
            QToolButton#qrButton:hover, QToolButton#settingsButton:hover, QToolButton#quitButton:hover {{
                background: rgba(40, 60, 48, 210);
            }}
            QFrame#qrPopup {{
                background: rgba(255, 255, 255, 245);
                border: 1px solid #D7DFEA;
                border-radius: 6px;
            }}
            QScrollArea#translationScrollArea {{
                background: transparent;
                border: 0;
            }}
            QScrollArea#translationScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
            QScrollArea#translationScrollArea QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                margin: 0;
            }}
            QScrollArea#translationScrollArea QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 75);
                border-radius: 3px;
                min-height: 18px;
            }}
            QScrollArea#translationScrollArea QScrollBar::add-line:vertical,
            QScrollArea#translationScrollArea QScrollBar::sub-line:vertical {{
                height: 0;
                border: 0;
            }}
            QLabel#qrUrl {{
                color: #1B2430;
                font-size: 10px;
                background: transparent;
            }}
        """)
        if hasattr(self, "_source_lang_combo"):
            self._fit_language_combo_width(self._source_lang_combo)
        if hasattr(self, "_target_lang_combo"):
            self._fit_language_combo_width(self._target_lang_combo)
        if hasattr(self, "_lock_button"):
            self._style_lock_button()

    def _create_language_combo(self, tooltip: str) -> QComboBox:
        combo = QComboBox()
        combo.setToolTip(tooltip)
        combo.setCursor(Qt.PointingHandCursor)
        for code, label in LANGUAGE_OPTIONS:
            combo.addItem(label, code)
        self._fit_language_combo_width(combo)
        return combo

    def _fit_language_combo_width(self, combo: QComboBox):
        combo.ensurePolished()
        metrics = combo.fontMetrics()
        text_width = max(
            metrics.horizontalAdvance(combo.itemText(index))
            for index in range(combo.count())
        )
        combo.setFixedWidth(text_width + 18)

    def _sync_language_controls(self):
        source = _normalize_language_code(self.translation_config.source_lang, "en")
        target = _normalize_language_code(self.translation_config.target_lang, OPPOSITE_LANGUAGE[source])
        if target == source:
            target = OPPOSITE_LANGUAGE[source]

        self.translation_config.source_lang = source
        self.translation_config.target_lang = target
        self._syncing_language_controls = True
        try:
            self._set_combo_language(self._source_lang_combo, source)
            self._set_combo_language(self._target_lang_combo, target)
            self._fit_language_combo_width(self._source_lang_combo)
            self._fit_language_combo_width(self._target_lang_combo)
        finally:
            self._syncing_language_controls = False

    def _set_combo_language(self, combo: QComboBox, language: str):
        for index in range(combo.count()):
            if combo.itemData(index) == language:
                combo.setCurrentIndex(index)
                return

    def _language_combo_changed(self, *args):
        if self._syncing_language_controls:
            return
        source = _normalize_language_code(self._source_lang_combo.currentData(), "en")
        target = _normalize_language_code(self._target_lang_combo.currentData(), "zh")
        sender = self.sender()
        if source == target:
            if sender is self._source_lang_combo:
                target = OPPOSITE_LANGUAGE[source]
            else:
                source = OPPOSITE_LANGUAGE[target]
        self._apply_language_flow(source, target)

    def _swap_language_flow(self):
        source = _normalize_language_code(self.translation_config.source_lang, "en")
        target = _normalize_language_code(self.translation_config.target_lang, OPPOSITE_LANGUAGE[source])
        self._apply_language_flow(target, source)

    def _apply_language_flow(self, source: str, target: str):
        self.translation_config.source_lang = _normalize_language_code(source, "en")
        self.translation_config.target_lang = _normalize_language_code(
            target,
            OPPOSITE_LANGUAGE[self.translation_config.source_lang],
        )
        if self.translation_config.source_lang == self.translation_config.target_lang:
            self.translation_config.target_lang = OPPOSITE_LANGUAGE[self.translation_config.source_lang]
        self._sync_language_controls()
        if self._on_settings_changed:
            self._on_settings_changed(
                self.config,
                self.hotkeys,
                self.audio_config,
                self.translation_config,
                self.whisper_config,
            )

    def _setup_qr_code(self):
        url = self.config.mobile_url or self._guess_mobile_url()
        self._qr_widget.set_text(url)
        self._qr_url_label.setText(url)
        self._qr_popup.setToolTip(url)
        self._qr_popup.adjustSize()

    def _guess_mobile_url(self) -> str:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                host = sock.getsockname()[0]
        except Exception:
            host = "127.0.0.1"
        return f"http://{host}:8765/mobile"

    def eventFilter(self, watched, event):
        if watched is self._qr_button:
            if self._is_locked():
                self._qr_popup.hide()
                return True
            if event.type() == QEvent.Enter:
                self._show_qr_popup()
            elif event.type() == QEvent.Leave:
                self._qr_popup.hide()
        return super().eventFilter(watched, event)

    def _show_qr_popup(self):
        if self._is_locked():
            self._qr_popup.hide()
            return
        x = max(8, self.width() - self._qr_popup.width() - 8)
        y = self._toolbar.height() + 6
        self._qr_popup.move(x, y)
        self._qr_popup.show()
        self._qr_popup.raise_()

    def _open_settings(self):
        if self._is_locked():
            return
        if self._settings_dialog and self._settings_dialog.isVisible():
            self._settings_dialog.raise_()
            self._settings_dialog.activateWindow()
            return
        self._settings_dialog = SettingsDialog(
            self.config,
            self.hotkeys,
            self.audio_config,
            self.translation_config,
            self.audio_devices,
            self.whisper_config,
            self,
        )
        self._settings_dialog.settings_changed.connect(self._apply_settings)
        self._settings_dialog.show()

    def _is_locked(self) -> bool:
        return bool(getattr(self.config, "locked", False))

    def _can_interact(self) -> bool:
        return not self._is_locked() and bool(getattr(self.config, "draggable", True))

    def _toggle_lock(self, checked=None):
        self.config.locked = not self._is_locked()
        self._refresh_lock_state()
        self._notify_settings_changed()

    def _refresh_lock_state(self):
        locked = self._is_locked()
        self.config.locked = locked
        self._dragging = False
        self._resizing = False
        self.setCursor(Qt.ArrowCursor)
        self._qr_popup.hide()
        if locked and self._settings_dialog and self._settings_dialog.isVisible():
            self._settings_dialog.close()

        for widget in (
            self._source_lang_combo,
            self._target_lang_combo,
            self._swap_lang_button,
            self._qr_button,
            self._settings_button,
            self._quit_button,
        ):
            widget.setEnabled(not locked)

        self._lock_button.setChecked(locked)
        self._lock_button.setIcon(_make_icon("unlock" if locked else "lock", self.config.text_color))
        self._lock_button.setToolTip("解锁浮窗" if locked else "锁定浮窗")
        self._style_lock_button()
        self._set_overlay_mouse_passthrough(locked)
        self._position_lock_button()
        self.update()

    def _style_lock_button(self):
        border_color = self.config.text_color
        bg = "rgba(35, 58, 42, 230)" if self._is_locked() else "rgba(18, 24, 33, 150)"
        self._lock_button.setStyleSheet(f"""
            QToolButton#floatingLockButton {{
                background: {bg};
                border: 1px solid {border_color};
                border-radius: 4px;
            }}
            QToolButton#floatingLockButton:hover {{
                background: rgba(40, 60, 48, 230);
            }}
        """)

    def _set_overlay_mouse_passthrough(self, enabled: bool):
        self.setAttribute(Qt.WA_TransparentForMouseEvents, enabled)
        if not sys.platform.startswith("win"):
            return
        try:
            hwnd = int(self.winId())
            user32 = ctypes.windll.user32
            gwl_exstyle = -20
            ws_ex_transparent = 0x00000020
            ws_ex_layered = 0x00080000
            ws_ex_noactivate = 0x08000000
            if ctypes.sizeof(ctypes.c_void_p) == 8:
                get_window_long = user32.GetWindowLongPtrW
                set_window_long = user32.SetWindowLongPtrW
                get_window_long.restype = ctypes.c_longlong
                set_window_long.restype = ctypes.c_longlong
            else:
                get_window_long = user32.GetWindowLongW
                set_window_long = user32.SetWindowLongW
                get_window_long.restype = ctypes.c_long
                set_window_long.restype = ctypes.c_long
            get_window_long.argtypes = [ctypes.c_void_p, ctypes.c_int]
            set_window_long.argtypes = [ctypes.c_void_p, ctypes.c_int, get_window_long.restype]
            style = int(get_window_long(hwnd, gwl_exstyle))
            style |= ws_ex_layered | ws_ex_noactivate
            if enabled:
                style |= ws_ex_transparent
            else:
                style &= ~ws_ex_transparent
            set_window_long(hwnd, gwl_exstyle, style)
        except Exception:
            pass

    def _position_lock_button(self):
        if not hasattr(self, "_lock_button") or not hasattr(self, "_lock_slot"):
            return
        self._lock_button.move(self._lock_slot.mapToGlobal(QPoint(0, 0)))
        if self.isVisible():
            self._lock_button.show()
            self._lock_button.raise_()

    def _notify_settings_changed(self):
        if self._on_settings_changed:
            self._on_settings_changed(
                self.config,
                self.hotkeys,
                self.audio_config,
                self.translation_config,
                self.whisper_config,
            )

    def _apply_settings(
        self,
        overlay_config: OverlayConfig,
        hotkey_config: HotkeyConfig,
        audio_config: AudioDeviceConfig,
        translation_config: TranslationConfig,
        whisper_config,
    ):
        self.config = overlay_config
        self.hotkeys = hotkey_config
        self.audio_config = audio_config
        self.translation_config = translation_config
        self.whisper_config = whisper_config
        self.setWindowOpacity(self.config.opacity)
        self._apply_styles()
        self._qr_button.setIcon(_make_icon("qr", self.config.text_color))
        self._swap_lang_button.setIcon(_make_icon("swap", self.config.original_text_color))
        self._settings_button.setIcon(_make_icon("settings", self.config.text_color))
        self._quit_button.setIcon(_make_icon("close", self.config.text_color))
        self._sync_language_controls()
        self._refresh_labels()
        self._refresh_lock_state()
        self.update()
        if self._on_settings_changed:
            self._on_settings_changed(
                self.config,
                self.hotkeys,
                self.audio_config,
                self.translation_config,
                self.whisper_config,
            )

    def request_audio_device_refresh(self):
        if self._on_audio_devices_refresh:
            self.audio_devices = self._on_audio_devices_refresh() or []
        if self._settings_dialog:
            self._settings_dialog.set_audio_devices(self.audio_devices, self.audio_config)

    def _request_shutdown(self):
        if self._on_shutdown_requested:
            self._on_shutdown_requested()
        else:
            app = QApplication.instance()
            if app:
                app.quit()

    def _connect_signals(self):
        """连接信号"""
        self._signals.new_translation.connect(self._add_translation)
        self._signals.new_translation_with_id.connect(self._add_translation_with_id)
        self._signals.update_translation.connect(self._update_translation)
        self._signals.clear_history.connect(self._clear_history)
        self._signals.toggle_visibility.connect(self._toggle_visibility)

    def add_translation(self, original: str, translated: str):
        """线程安全地添加翻译"""
        self._signals.new_translation.emit(original, translated)

    def add_translation_with_id(self, item_id: str, original: str, translated: str):
        """线程安全地添加可更新的翻译记录。"""
        self._signals.new_translation_with_id.emit(item_id, original, translated)

    def update_translation(self, item_id: str, translated: str):
        """线程安全地更新已有翻译记录。"""
        self._signals.update_translation.emit(item_id, translated)

    def _add_translation(self, original: str, translated: str):
        """添加翻译到浮窗"""
        item = TranslationItem(original, translated, self.config.fade_duration)
        self._append_translation_item(item)

    def _add_translation_with_id(self, item_id: str, original: str, translated: str):
        """添加一条之后可用 item_id 更新的翻译。"""
        item = TranslationItem(original, translated, self.config.fade_duration, item_id=item_id)
        self._append_translation_item(item)

    def _append_translation_item(self, item: TranslationItem):
        self._translations.append(item)

        # 更新标签显示
        items = list(self._translations)
        self._render_items(items)

        # 启动淡出计时器
        if len(self._translations) >= self.config.max_lines:
            oldest = self._translations[0]
            if oldest.fade_start is None:
                oldest.start_fade()

    def _update_translation(self, item_id: str, translated: str):
        """更新已有翻译内容，避免慢翻译显示到下一条上。"""
        for item in self._translations:
            if item.item_id == item_id:
                item.translated = translated
                item.fade_start = None
                item.timestamp = time.time()
                self._refresh_labels()
                return

    def _update_fade(self):
        """更新淡出效果"""
        needs_update = False
        to_remove = []

        for item in self._translations:
            if item.fade_start is not None and item.opacity <= 0:
                to_remove.append(item)
                needs_update = True

        for item in to_remove:
            self._translations.remove(item)

        if needs_update:
            self._refresh_labels()

    def _refresh_labels(self):
        if not hasattr(self, "_labels") or not hasattr(self, "_content_widget"):
            return
        self._render_items(list(self._translations))

    def _render_items(self, items: List[TranslationItem]):
        text_width = self._label_text_width()
        visible_items = []

        for item in items[-self.config.max_lines:]:
            html = self._format_item(item, item.opacity, text_width)
            height = self._measure_html_height(html, text_width)
            visible_items.append((html, height))

        for i, label in enumerate(self._labels):
            if i < len(visible_items):
                html, height = visible_items[i]
                label.setText(html)
                label.setFixedHeight(max(1, height))
                label.show()
                label.updateGeometry()
            else:
                label.clear()
                label.setFixedHeight(0)
                label.hide()
        self._content_layout.activate()
        self._content_widget.updateGeometry()
        if hasattr(self, "_scroll_area"):
            QTimer.singleShot(0, self._scroll_to_latest)

    def _label_text_width(self) -> int:
        if hasattr(self, "_scroll_area"):
            width = self._scroll_area.viewport().contentsRect().width()
        else:
            width = self._content_widget.contentsRect().width()
        if width <= 0:
            margins = self._layout.contentsMargins()
            width = self.width() - margins.left() - margins.right()
        return max(40, int(width) - 2)

    def _measure_html_height(self, html: str, width: int) -> int:
        doc = QTextDocument()
        doc.setDocumentMargin(0)
        doc.setDefaultFont(self.font())
        doc.setHtml(html)
        doc.setTextWidth(max(80, width))
        return max(1, int(doc.size().height()) + 3)

    def _format_item(self, item: TranslationItem, opacity: float, width: int = None) -> str:
        translated = self._escape(self._normalize_display_text(item.translated))
        original = self._escape(self._normalize_display_text(item.original))
        main_color = self._rgba_css(self.config.text_color, opacity)
        original_color = self._rgba_css(self.config.original_text_color, opacity * 0.92)
        family = self._escape(self.config.font_family).replace('"', "&quot;")
        if self.config.show_original:
            return (
                f'<div style="font-family:&quot;{family}&quot;; font-size:{self.config.font_size}px; '
                f'line-height:1.25; margin:0; color:{main_color}; white-space:normal; '
                f'word-wrap:break-word;">'
                f'{translated}</div>'
                f'<div style="font-family:&quot;{family}&quot;; font-size:{max(10, self.config.font_size - 4)}px; '
                f'line-height:1.2; margin:2px 0 0 0; color:{original_color}; '
                f'white-space:normal; word-wrap:break-word;">{original}</div>'
            )
        return (
            f'<div style="font-family:&quot;{family}&quot;; font-size:{self.config.font_size}px; '
            f'line-height:1.25; margin:0; color:{main_color}; white-space:normal; '
            f'word-wrap:break-word;">{translated}</div>'
        )

    def _normalize_display_text(self, text: str) -> str:
        return " ".join((text or "").split())

    def _scroll_to_latest(self):
        if not hasattr(self, "_scroll_area"):
            return
        bar = self._scroll_area.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _escape(self, text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def _rgba_css(self, color: str, opacity: float) -> str:
        qcolor = QColor(color)
        alpha = max(0, min(255, int(opacity * 255)))
        return f"rgba({qcolor.red()}, {qcolor.green()}, {qcolor.blue()}, {alpha})"

    def _clear_history(self):
        """清除翻译历史"""
        self._translations.clear()
        for label in self._labels:
            label.hide()

    def _toggle_visibility(self):
        """切换可见性"""
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def paintEvent(self, event):
        """绘制半透明背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 背景
        bg_color = QColor(self.config.bg_color)
        if not bg_color.isValid():
            bg_color = QColor("#20242A")
        bg_opacity = max(0.0, min(1.0, float(getattr(self.config, "bg_opacity", 0.82))))
        bg_color.setAlpha(int(bg_opacity * 255))
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)

        # 边框
        pen = QPen(QColor(self.config.text_color))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(
            self.rect().adjusted(1, 1, -1, -1), 10, 10
        )

        # 右下角尺寸拖拽手柄
        if not self._can_interact():
            return
        handle_color = QColor(self.config.text_color)
        handle_color.setAlpha(150)
        painter.setPen(QPen(handle_color, 1))
        for offset in (7, 12, 17):
            painter.drawLine(
                self.width() - offset,
                self.height() - 4,
                self.width() - 4,
                self.height() - offset,
            )

    def _resize_hit_test(self, pos) -> bool:
        return self._can_interact() and pos.x() >= self.width() - 24 and pos.y() >= self.height() - 24

    def mousePressEvent(self, event):
        """鼠标按下 - 开始拖拽"""
        if not self._can_interact():
            event.ignore()
            return
        if event.button() == Qt.LeftButton and self._resize_hit_test(event.pos()):
            self._resizing = True
            self._resize_start_pos = event.globalPos()
            self._resize_start_size = self.size()
            event.accept()
        elif event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动 - 拖拽窗口"""
        if not self._can_interact():
            self.setCursor(Qt.ArrowCursor)
            event.ignore()
            return
        if self._resizing and event.buttons() == Qt.LeftButton:
            delta = event.globalPos() - self._resize_start_pos
            width = max(self.minimumWidth(), min(self.maximumWidth(), self._resize_start_size.width() + delta.x()))
            height = max(self.minimumHeight(), min(self.maximumHeight(), self._resize_start_size.height() + delta.y()))
            self.resize(width, height)
            self.config.window_width = width
            self.config.window_height = height
            self._refresh_labels()
            event.accept()
        elif self._dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
        else:
            self.setCursor(Qt.SizeFDiagCursor if self._resize_hit_test(event.pos()) else Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        """鼠标释放 - 结束拖拽"""
        was_resizing = self._resizing
        self._dragging = False
        self._resizing = False
        self.setCursor(Qt.ArrowCursor)
        self._refresh_labels()
        if was_resizing:
            self._notify_settings_changed()
        event.accept()

    def enable_drag(self):
        """启用拖拽（临时关闭鼠标穿透）"""
        self.config.draggable = True
        if not self._is_locked():
            self._set_overlay_mouse_passthrough(False)
        self.update()

    def disable_drag(self):
        """禁用拖拽（恢复鼠标穿透）"""
        self.config.draggable = False
        self._set_overlay_mouse_passthrough(True)
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.config.window_width = self.width()
        self.config.window_height = self.height()
        self._refresh_labels()
        self._position_lock_button()

    def moveEvent(self, event):
        super().moveEvent(event)
        self._position_lock_button()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_lock_state()
        self._refresh_labels()
        self._position_lock_button()

    def hideEvent(self, event):
        if hasattr(self, "_lock_button"):
            self._lock_button.hide()
        super().hideEvent(event)

    def set_position(self, position: str):
        """设置浮窗位置"""
        screen = QApplication.primaryScreen().geometry()
        positions = {
            "top": (screen.width() // 2 - self.width() // 2, 50),
            "bottom": (screen.width() // 2 - self.width() // 2,
                       screen.height() - self.height() - 50),
            "left": (20, screen.height() // 2 - self.height() // 2),
            "right": (screen.width() - self.width() - 20,
                      screen.height() // 2 - self.height() // 2),
        }
        if position in positions:
            self.move(*positions[position])
            self.config.position = position

    def closeEvent(self, event):
        """关闭事件"""
        self._fade_timer.stop()
        if hasattr(self, "_lock_button"):
            self._lock_button.close()
        super().closeEvent(event)
