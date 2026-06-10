"""
游戏浮窗叠加层
使用 PyQt5 创建透明置顶窗口，显示翻译结果
"""

import ctypes
import socket
import sys
import time
from collections import deque
from typing import Callable, List, Optional

from loguru import logger
from PyQt5.QtCore import Qt, QEvent, QPoint, QRect, QTimer, QObject, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QTextDocument, QCursor
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from voxgo.app_info import APP_NAME, APP_VERSION
from voxgo.i18n import UI_LANGUAGE_ZH, normalize_ui_language
from voxgo.translation import TranslationConfig
from voxgo.update.checker import UpdateCheckResult, UpdateInfo, UpdateSettings
from voxgo.ui.config_models import (
    AudioDeviceConfig,
    DebugConfig,
    HotkeyConfig,
    OverlayConfig,
    OPPOSITE_LANGUAGE,
    RuntimeConfig,
    WhisperDeviceConfig,
    _normalize_language_code,
    _speech_language_options,
    _tr,
)
from voxgo.ui.dialogs import (
    FeedbackDialog,
    FirstRunWizard,
    FullscreenHelpDialog,
    UpdatePromptDialog,
    _build_help_text,
)
from voxgo.ui.icons import _make_icon
from voxgo.ui.qr_widget import QrCodeWidget
from voxgo.ui.settings_dialog import SettingsDialog
from voxgo.ui.widgets import (
    AudioTestPanel,
    AudioTestSignals,
    ColorButton,
    HotkeyCaptureEdit,
    OverlayLockButton,
    TranslationTestRunner,
    TranslationTestSignals,
)


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
    remove_translation = pyqtSignal(str)
    clear_history = pyqtSignal()
    toggle_visibility = pyqtSignal()
    toggle_lock = pyqtSignal()
    toggle_compact = pyqtSignal()
    settings_changed = pyqtSignal(object, object, object, object, object, object, object)
    refresh_audio_devices = pyqtSignal()
    update_checking = pyqtSignal(bool)
    update_check_result = pyqtSignal(object, bool)
    pause_state_changed = pyqtSignal(bool)

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
        app_config: RuntimeConfig = None,
        debug_config: DebugConfig = None,
        update_config: UpdateSettings = None,
        app_version: str = "",
        runtime_dir: str = "",
        get_last_latency_summary: Optional[Callable[[], dict]] = None,
        on_settings_changed: Optional[
            Callable[
                [OverlayConfig, HotkeyConfig, AudioDeviceConfig, TranslationConfig, object, RuntimeConfig, UpdateSettings],
                None,
            ]
        ] = None,
        on_audio_devices_refresh: Optional[Callable[[], List[dict]]] = None,
        on_update_check_requested: Optional[Callable[[bool], None]] = None,
        on_update_version_ignored: Optional[Callable[[str], None]] = None,
        on_shutdown_requested: Optional[Callable[[], None]] = None,
        on_overlay_updated: Optional[Callable[[str], None]] = None,
    ):
        super().__init__()
        self.config = config or OverlayConfig()
        self.hotkeys = hotkeys or HotkeyConfig()
        self.audio_config = audio_config or AudioDeviceConfig()
        self.translation_config = translation_config or TranslationConfig()
        self.audio_devices = audio_devices or []
        self.whisper_config = whisper_config or WhisperDeviceConfig()
        self.app_config = app_config or RuntimeConfig()
        self.app_config.language = normalize_ui_language(getattr(self.app_config, "language", UI_LANGUAGE_ZH))
        self.debug_config = debug_config or DebugConfig()
        self.update_config = update_config or UpdateSettings()
        self.app_version = app_version or APP_VERSION
        self.runtime_dir = runtime_dir
        self._get_last_latency_summary = get_last_latency_summary
        self._on_settings_changed = on_settings_changed
        self._on_audio_devices_refresh = on_audio_devices_refresh
        self._on_update_check_requested = on_update_check_requested
        self._on_update_version_ignored = on_update_version_ignored
        self._on_shutdown_requested = on_shutdown_requested
        self._on_overlay_updated = on_overlay_updated
        self._translations: deque = deque(maxlen=self.config.max_lines)
        self._signals = OverlaySignals()
        self._dragging = False
        self._drag_pos = None
        self._resizing = False
        self._resize_start_pos = None
        self._resize_start_size = None
        self._initializing_geometry = True
        self._syncing_language_controls = False
        self._settings_dialog = None
        self._first_run_wizard = None
        self._fullscreen_help_dialog = None
        self._paused = False
        self._pending_update: Optional[UpdateInfo] = None
        self._update_prompt_dialog = None
        self._update_notice_shown_version = ""
        self._fade_timer = QTimer()
        self._fade_timer.timeout.connect(self._update_fade)
        self._fade_timer.start(100)

        self._init_ui()
        self._connect_signals()

    def _ui_language(self) -> str:
        return normalize_ui_language(getattr(self.app_config or RuntimeConfig(), "language", UI_LANGUAGE_ZH))

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
        compact = bool(getattr(self.config, "compact_mode", False))
        self.setMinimumSize(260 if compact else 360, 92 if compact else 150)
        self.setMaximumSize(980, 520)

        self._restore_window_geometry()

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

        ui_language = self._ui_language()
        self._source_lang_combo = self._create_language_combo(_tr(ui_language, "识别语言", "Recognition Language"))
        self._source_lang_combo.setObjectName("languageCombo")
        toolbar_layout.addWidget(self._source_lang_combo)

        self._swap_lang_button = QToolButton()
        self._swap_lang_button.setObjectName("languageSwapButton")
        self._swap_lang_button.setIcon(_make_icon("swap", self.config.original_text_color))
        self._swap_lang_button.setToolTip(_tr(ui_language, "交换识别语言和翻译目标语言", "Swap recognition and target languages"))
        self._swap_lang_button.setFixedSize(28, 24)
        self._swap_lang_button.setCursor(Qt.PointingHandCursor)
        self._swap_lang_button.clicked.connect(self._swap_language_flow)
        toolbar_layout.addWidget(self._swap_lang_button)

        self._target_lang_combo = self._create_language_combo(_tr(ui_language, "翻译目标语言", "Target Language"))
        self._target_lang_combo.setObjectName("languageCombo")
        toolbar_layout.addWidget(self._target_lang_combo)
        self._sync_language_controls()
        self._source_lang_combo.currentIndexChanged.connect(self._language_combo_changed)
        self._target_lang_combo.currentIndexChanged.connect(self._language_combo_changed)

        toolbar_layout.addStretch()

        self._compact_button = QToolButton()
        self._compact_button.setObjectName("compactButton")
        self._compact_button.setFixedSize(28, 24)
        self._compact_button.setCursor(Qt.PointingHandCursor)
        self._compact_button.clicked.connect(self.toggle_compact_mode)
        toolbar_layout.addWidget(self._compact_button)

        self._qr_button = QToolButton()
        self._qr_button.setObjectName("qrButton")
        self._qr_button.setIcon(_make_icon("qr", self.config.text_color))
        self._qr_button.setToolTip(_tr(ui_language, "手机二维码", "Mobile QR Code"))
        self._qr_button.setFixedSize(28, 24)
        self._qr_button.setCursor(Qt.PointingHandCursor)
        self._qr_button.installEventFilter(self)
        toolbar_layout.addWidget(self._qr_button)

        self._settings_button = QToolButton()
        self._settings_button.setObjectName("settingsButton")
        self._settings_button.setIcon(_make_icon("settings", self.config.text_color))
        self._settings_button.setToolTip(_tr(ui_language, "浮窗设置", "Overlay Settings"))
        self._settings_button.setFixedSize(28, 24)
        self._settings_button.setCursor(Qt.PointingHandCursor)
        self._settings_button.clicked.connect(self._open_settings)
        toolbar_layout.addWidget(self._settings_button)
        self._settings_badge = QLabel(self._settings_button)
        self._settings_badge.setObjectName("settingsBadge")
        self._settings_badge.setFixedSize(9, 9)
        self._settings_badge.setStyleSheet(
            "background: #F04438; border: 1px solid #FFFFFF; border-radius: 4px;"
        )
        self._settings_badge.hide()

        self._quit_button = QToolButton()
        self._quit_button.setObjectName("quitButton")
        self._quit_button.setIcon(_make_icon("close", self.config.text_color))
        self._quit_button.setToolTip(_tr(ui_language, "退出程序", "Quit"))
        self._quit_button.setFixedSize(28, 24)
        self._quit_button.setCursor(Qt.PointingHandCursor)
        self._quit_button.clicked.connect(self._request_shutdown)
        toolbar_layout.addWidget(self._quit_button)

        self._lock_slot = QWidget()
        self._lock_slot.setFixedSize(28, 24)
        toolbar_layout.addWidget(self._lock_slot)
        self._layout.addWidget(self._toolbar)

        self._lock_button = OverlayLockButton(self)

        self._qr_popup = QFrame(None)
        self._qr_popup.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self._qr_popup.setAttribute(Qt.WA_ShowWithoutActivating)
        self._qr_popup.setObjectName("qrPopup")
        self._qr_popup.installEventFilter(self)
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

        # 设置窗口透明度
        self.setWindowOpacity(self.config.opacity)
        self._apply_styles()
        self._refresh_control_state()
        self._refresh_compact_mode()
        self._refresh_lock_state()
        self._initializing_geometry = False
        QTimer.singleShot(0, self._position_lock_button)

    def _restore_window_geometry(self):
        primary = QApplication.primaryScreen().geometry()
        screen = primary
        for item in QApplication.screens():
            screen = screen.united(item.geometry())
        width = max(260, min(980, int(getattr(self.config, "window_width", 500) or 500)))
        height = max(92, min(520, int(getattr(self.config, "window_height", 200) or 200)))
        self.resize(width, height)
        x = getattr(self.config, "window_x", None)
        y = getattr(self.config, "window_y", None)
        if x is None or y is None:
            x, y = self._default_position_for_size(primary, width, height)
        x = max(screen.left(), min(int(x), screen.right() - width + 1))
        y = max(screen.top(), min(int(y), screen.bottom() - height + 1))
        self.move(x, y)
        self._remember_window_geometry()

    def _default_position_for_size(self, screen: QRect, width: int, height: int):
        if self.config.position == "top":
            return (screen.width() - width) // 2, 50
        if self.config.position == "right":
            return screen.width() - width - 20, (screen.height() - height) // 2
        if self.config.position == "left":
            return 20, (screen.height() - height) // 2
        return (screen.width() - width) // 2, screen.height() - height - 50

    def _remember_window_geometry(self):
        if not hasattr(self, "config"):
            return
        self.config.window_width = int(self.width())
        self.config.window_height = int(self.height())
        self.config.window_x = int(self.x())
        self.config.window_y = int(self.y())

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
            QToolButton#compactButton, QToolButton#qrButton, QToolButton#settingsButton, QToolButton#quitButton {{
                background: rgba(18, 24, 33, 150);
                border: 1px solid {self.config.text_color};
                border-radius: 4px;
            }}
            QToolButton#compactButton:hover, QToolButton#qrButton:hover,
            QToolButton#settingsButton:hover, QToolButton#quitButton:hover {{
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
        if hasattr(self, "_settings_badge"):
            self._position_settings_badge()

    def _create_language_combo(self, tooltip: str) -> QComboBox:
        combo = QComboBox()
        combo.setToolTip(tooltip)
        combo.setCursor(Qt.PointingHandCursor)
        for code, label in _speech_language_options(self._ui_language()):
            combo.addItem(label, code)
        self._fit_language_combo_width(combo)
        return combo

    def _refresh_language_combo_items(self, combo: QComboBox, current: str):
        combo.blockSignals(True)
        combo.clear()
        for code, label in _speech_language_options(self._ui_language()):
            combo.addItem(label, code)
        self._set_combo_language(combo, current)
        self._fit_language_combo_width(combo)
        combo.blockSignals(False)

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
            self._refresh_language_combo_items(self._source_lang_combo, source)
            self._refresh_language_combo_items(self._target_lang_combo, target)
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
                self.app_config,
                self.update_config,
            )

    def _setup_qr_code(self):
        url = self.config.mobile_url or self._guess_mobile_url()
        self._qr_widget.set_text(url)
        self._qr_url_label.setText(url)
        self._qr_popup.setToolTip(url)
        self._qr_popup.adjustSize()

    def _refresh_control_state(self):
        ui_language = self._ui_language()
        if hasattr(self, "_compact_button"):
            compact = bool(getattr(self.config, "compact_mode", False))
            self._compact_button.setIcon(_make_icon("expand" if compact else "compact", self.config.text_color))
            self._compact_button.setToolTip(_tr(
                ui_language,
                "退出紧凑浮窗" if compact else "紧凑浮窗",
                "Exit compact overlay" if compact else "Compact overlay",
            ))
        if hasattr(self, "_qr_button"):
            self._qr_button.setToolTip(_tr(ui_language, "手机二维码", "Mobile QR Code"))
        if hasattr(self, "_settings_button"):
            self._settings_button.setToolTip(_tr(ui_language, "浮窗设置", "Overlay Settings"))
        if hasattr(self, "_swap_lang_button"):
            self._swap_lang_button.setToolTip(_tr(ui_language, "交换识别语言和翻译目标语言", "Swap recognition and target languages"))
        if hasattr(self, "_source_lang_combo"):
            self._source_lang_combo.setToolTip(_tr(ui_language, "识别语言", "Recognition Language"))
        if hasattr(self, "_target_lang_combo"):
            self._target_lang_combo.setToolTip(_tr(ui_language, "翻译目标语言", "Target Language"))
        if hasattr(self, "_quit_button"):
            self._quit_button.setToolTip(_tr(ui_language, "退出程序", "Quit"))

    def set_paused(self, paused: bool):
        self._paused = bool(paused)
        self._refresh_control_state()
        self._signals.pause_state_changed.emit(self._paused)

    def is_paused(self) -> bool:
        return bool(self._paused)

    def clear_history(self):
        self._clear_history()

    def show_settings(self):
        self._open_settings()

    def toggle_compact_mode(self, *args):
        self.set_compact_mode(not bool(getattr(self.config, "compact_mode", False)))

    def set_compact_mode(self, compact: bool):
        compact = bool(compact)
        if bool(getattr(self.config, "compact_mode", False)) == compact:
            self._refresh_compact_mode()
            return
        self.config.compact_mode = compact
        self._refresh_compact_mode()
        self._notify_settings_changed()

    def _refresh_compact_mode(self):
        if not hasattr(self, "_toolbar"):
            return
        compact = bool(getattr(self.config, "compact_mode", False))
        for widget in (
            getattr(self, "_source_lang_combo", None),
            getattr(self, "_swap_lang_button", None),
            getattr(self, "_target_lang_combo", None),
        ):
            if widget:
                widget.setVisible(not compact)
        self._layout.setContentsMargins(7 if compact else 10, 5 if compact else 8, 7 if compact else 10, 7 if compact else 10)
        self._layout.setSpacing(3 if compact else 6)
        self._content_layout.setSpacing(2 if compact else 4)
        self.setMinimumSize(260 if compact else 360, 92 if compact else 150)
        self._remember_window_geometry()
        self._refresh_control_state()
        self._refresh_labels()
        self.update()

    def show_fullscreen_help(self):
        if self._fullscreen_help_dialog and self._fullscreen_help_dialog.isVisible():
            self._fullscreen_help_dialog.raise_()
            self._fullscreen_help_dialog.activateWindow()
            return
        self._fullscreen_help_dialog = FullscreenHelpDialog(self.hotkeys, self._ui_language(), self)
        self._fullscreen_help_dialog.show()
        self._fullscreen_help_dialog.raise_()
        self._fullscreen_help_dialog.activateWindow()

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
                QTimer.singleShot(140, self._hide_qr_popup_if_unhovered)
        elif watched is self._qr_popup:
            if event.type() == QEvent.Leave:
                QTimer.singleShot(140, self._hide_qr_popup_if_unhovered)
        return super().eventFilter(watched, event)

    def _show_qr_popup(self):
        if self._is_locked():
            self._qr_popup.hide()
            return
        self._qr_popup.adjustSize()
        button_rect = self._qr_button.rect()
        button_top_left = self._qr_button.mapToGlobal(button_rect.topLeft())
        screen = QApplication.screenAt(button_top_left) or QApplication.primaryScreen()
        available = screen.availableGeometry()
        x = button_top_left.x() + self._qr_button.width() - self._qr_popup.width()
        y = button_top_left.y() + self._qr_button.height() + 6
        if y + self._qr_popup.height() > available.bottom():
            y = button_top_left.y() - self._qr_popup.height() - 6
        x = max(available.left() + 8, min(x, available.right() - self._qr_popup.width() - 8))
        y = max(available.top() + 8, min(y, available.bottom() - self._qr_popup.height() - 8))
        self._qr_popup.move(x, y)
        self._qr_popup.show()
        self._qr_popup.raise_()

    def _hide_qr_popup_if_unhovered(self):
        if not hasattr(self, "_qr_popup") or not self._qr_popup.isVisible():
            return
        cursor_pos = QCursor.pos()
        if self._qr_button.rect().contains(self._qr_button.mapFromGlobal(cursor_pos)):
            return
        if self._qr_popup.rect().contains(self._qr_popup.mapFromGlobal(cursor_pos)):
            return
        self._qr_popup.hide()

    def _open_settings(self):
        if self._is_locked():
            return
        if self._settings_dialog and self._settings_dialog.isVisible():
            self._settings_dialog.raise_()
            self._settings_dialog.activateWindow()
            return
        try:
            self._settings_dialog = SettingsDialog(
                self.config,
                self.hotkeys,
                self.audio_config,
                self.translation_config,
                self.audio_devices,
                self.whisper_config,
                self.app_config,
                self.debug_config,
                self.update_config,
                self.app_version,
                self.runtime_dir,
                self._current_latency_summary(),
                self,
            )
            self._settings_dialog.settings_changed.connect(self._apply_settings)
            if self._pending_update:
                self._settings_dialog.show_pending_update(self._pending_update)
            self._set_update_badge_visible(False)
            self._settings_dialog.show()
            self._settings_dialog.raise_()
            self._settings_dialog.activateWindow()
        except Exception:
            logger.exception("打开设置窗口失败")

    def show_first_run_wizard(self, on_completed: Optional[Callable[[], None]] = None):
        if self._first_run_wizard and self._first_run_wizard.isVisible():
            self._first_run_wizard.raise_()
            self._first_run_wizard.activateWindow()
            return
        self._first_run_wizard = FirstRunWizard(
            self.audio_config,
            self.translation_config,
            self.audio_devices,
            self.whisper_config,
            self.app_config,
            self.debug_config,
            self.app_version,
            self.runtime_dir,
            self._current_latency_summary,
            self._on_audio_devices_refresh,
            self,
        )
        self._first_run_wizard.setup_completed.connect(
            lambda: self._handle_first_run_completed(on_completed)
        )
        self._first_run_wizard.show()
        self._first_run_wizard.raise_()
        self._first_run_wizard.activateWindow()

    def _handle_first_run_completed(self, on_completed: Optional[Callable[[], None]] = None):
        self._sync_language_controls()
        if on_completed:
            on_completed()

    def refresh_language(self):
        self._sync_language_controls()
        self._refresh_control_state()
        self._refresh_lock_state()
        if self._fullscreen_help_dialog and self._fullscreen_help_dialog.isVisible():
            self._fullscreen_help_dialog.close()
            self._fullscreen_help_dialog = None
        if self._settings_dialog and self._settings_dialog.isVisible():
            old_dialog = self._settings_dialog
            tab_index = 0
            tabs = old_dialog.findChild(QTabWidget)
            if tabs:
                tab_index = tabs.currentIndex()
            old_dialog.close()
            self._settings_dialog = None
            QTimer.singleShot(0, lambda index=tab_index: self._reopen_settings_at(index))

    def _reopen_settings_at(self, tab_index: int):
        self._open_settings()
        if self._settings_dialog:
            tabs = self._settings_dialog.findChild(QTabWidget)
            if tabs:
                tabs.setCurrentIndex(max(0, min(int(tab_index or 0), tabs.count() - 1)))

    def _current_latency_summary(self) -> dict:
        if self._get_last_latency_summary:
            try:
                return self._get_last_latency_summary() or {}
            except Exception:
                return {}
        return {}

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
            self._compact_button,
            self._qr_button,
            self._settings_button,
            self._quit_button,
        ):
            widget.setEnabled(not locked)

        self._lock_button.setChecked(locked)
        self._lock_button.setIcon(_make_icon("unlock" if locked else "lock", self.config.text_color))
        self._lock_button.setToolTip(_tr(
            self._ui_language(),
            "解锁浮窗" if locked else "锁定浮窗",
            "Unlock overlay" if locked else "Lock overlay",
        ))
        self._style_lock_button()
        self._set_overlay_mouse_passthrough(locked)
        self._position_lock_button()
        self._set_update_badge_visible(bool(self._pending_update))
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

    def _position_settings_badge(self):
        if not hasattr(self, "_settings_badge") or not hasattr(self, "_settings_button"):
            return
        self._settings_badge.move(
            max(0, self._settings_button.width() - self._settings_badge.width() - 1),
            1,
        )
        self._settings_badge.raise_()

    def _set_update_badge_visible(self, visible: bool):
        if hasattr(self, "_settings_badge"):
            self._settings_badge.setVisible(bool(visible) and not self._is_locked())
            self._position_settings_badge()

    def request_update_check(self, manual: bool = False):
        if self._on_update_check_requested:
            self.set_update_checking(True)
            self._on_update_check_requested(bool(manual))
            return
        self.set_update_checking(False)

    def set_update_checking(self, checking: bool):
        self._signals.update_checking.emit(bool(checking))

    def handle_update_check_result(self, result: UpdateCheckResult, manual: bool = False):
        self._signals.update_check_result.emit(result, bool(manual))

    def _handle_update_checking(self, checking: bool):
        if self._settings_dialog and self._settings_dialog.isVisible():
            self._settings_dialog.set_update_checking(checking)

    def _handle_update_check_result(self, result: UpdateCheckResult, manual: bool = False):
        self._handle_update_checking(False)
        if self._settings_dialog and self._settings_dialog.isVisible():
            self._settings_dialog.set_update_check_result(result)

        update = getattr(result, "update", None)
        if getattr(result, "status", "") == "available" and update:
            self._pending_update = update
            self._set_update_badge_visible(True)
            self._show_update_prompt(update, manual)
            return

        if manual:
            self._pending_update = None
            self._set_update_badge_visible(False)

    def _show_update_prompt(self, update: UpdateInfo, manual: bool = False):
        if not update:
            return
        version = str(getattr(update, "latest", "") or "").strip()
        if not manual and version == self._update_notice_shown_version:
            return
        self._update_notice_shown_version = version
        if self._update_prompt_dialog and self._update_prompt_dialog.isVisible():
            self._update_prompt_dialog.raise_()
            self._update_prompt_dialog.activateWindow()
            return
        self._update_prompt_dialog = UpdatePromptDialog(
            update,
            self.app_version,
            self._ignore_update_version,
            self._ui_language(),
            self,
        )
        self._update_prompt_dialog.show()
        self._update_prompt_dialog.raise_()
        self._update_prompt_dialog.activateWindow()

    def _ignore_update_version(self, version: str):
        self.update_config.ignored_version = str(version or "").strip().lstrip("v")
        self._pending_update = None
        self._set_update_badge_visible(False)
        if self._settings_dialog and self._settings_dialog.isVisible():
            self._settings_dialog.set_update_check_result(
                UpdateCheckResult("ignored", message=f"已忽略 v{self.update_config.ignored_version}")
            )
        if self._on_update_version_ignored:
            self._on_update_version_ignored(self.update_config.ignored_version)

    def _notify_settings_changed(self):
        if self._on_settings_changed:
            self._on_settings_changed(
                self.config,
                self.hotkeys,
                self.audio_config,
                self.translation_config,
                self.whisper_config,
                self.app_config,
                self.update_config,
            )

    def _apply_settings(
        self,
        overlay_config: OverlayConfig,
        hotkey_config: HotkeyConfig,
        audio_config: AudioDeviceConfig,
        translation_config: TranslationConfig,
        whisper_config,
        app_config: RuntimeConfig,
        update_config,
    ):
        self._remember_window_geometry()
        overlay_config.window_x = self.config.window_x
        overlay_config.window_y = self.config.window_y
        overlay_config.window_width = self.config.window_width
        overlay_config.window_height = self.config.window_height
        self.config = overlay_config
        self.hotkeys = hotkey_config
        self.audio_config = audio_config
        self.translation_config = translation_config
        self.whisper_config = whisper_config
        self.app_config = app_config or self.app_config or RuntimeConfig()
        self.app_config.language = normalize_ui_language(getattr(self.app_config, "language", UI_LANGUAGE_ZH))
        self.update_config = update_config or self.update_config
        self.setWindowOpacity(self.config.opacity)
        self._apply_styles()
        self._qr_button.setIcon(_make_icon("qr", self.config.text_color))
        self._swap_lang_button.setIcon(_make_icon("swap", self.config.original_text_color))
        self._settings_button.setIcon(_make_icon("settings", self.config.text_color))
        self._quit_button.setIcon(_make_icon("close", self.config.text_color))
        self._sync_language_controls()
        self._refresh_control_state()
        self._refresh_compact_mode()
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
                self.app_config,
                self.update_config,
            )

    def request_audio_device_refresh(self):
        if self._on_audio_devices_refresh:
            self.audio_devices = self._on_audio_devices_refresh() or []
        if self._settings_dialog:
            self._settings_dialog.set_audio_devices(self.audio_devices, self.audio_config)
        if self._first_run_wizard and self._first_run_wizard.isVisible():
            self._first_run_wizard.audio_devices = self.audio_devices
            self._first_run_wizard._fill_wizard_audio_devices()

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
        self._signals.remove_translation.connect(self._remove_translation)
        self._signals.clear_history.connect(self._clear_history)
        self._signals.toggle_visibility.connect(self._toggle_visibility)
        self._signals.toggle_lock.connect(self._toggle_lock)
        self._signals.toggle_compact.connect(self.toggle_compact_mode)
        self._signals.update_checking.connect(self._handle_update_checking)
        self._signals.update_check_result.connect(self._handle_update_check_result)

    def add_translation(self, original: str, translated: str):
        """线程安全地添加翻译"""
        self._signals.new_translation.emit(original, translated)

    def add_translation_with_id(self, item_id: str, original: str, translated: str):
        """线程安全地添加可更新的翻译记录。"""
        self._signals.new_translation_with_id.emit(item_id, original, translated)

    def update_translation(self, item_id: str, translated: str):
        """线程安全地更新已有翻译记录。"""
        self._signals.update_translation.emit(item_id, translated)

    def remove_translation(self, item_id: str):
        self._signals.remove_translation.emit(item_id)

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
                if self._on_overlay_updated:
                    self._on_overlay_updated(item_id)
                return

    def _remove_translation(self, item_id: str):
        for item in list(self._translations):
            if item.item_id == item_id:
                self._translations.remove(item)
                self._refresh_labels()
                if self._on_overlay_updated:
                    self._on_overlay_updated(item_id)
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
        if was_resizing or event.button() == Qt.LeftButton:
            self._remember_window_geometry()
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
        self._remember_window_geometry()
        self._refresh_labels()
        self._position_lock_button()

    def moveEvent(self, event):
        super().moveEvent(event)
        self._remember_window_geometry()
        self._position_lock_button()
        if hasattr(self, "_qr_popup") and self._qr_popup.isVisible():
            self._show_qr_popup()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_lock_state()
        self._refresh_labels()
        self._position_lock_button()

    def hideEvent(self, event):
        if hasattr(self, "_lock_button"):
            self._lock_button.hide()
        if hasattr(self, "_qr_popup"):
            self._qr_popup.hide()
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
            self._remember_window_geometry()
            self._notify_settings_changed()

    def closeEvent(self, event):
        """关闭事件"""
        self._fade_timer.stop()
        if hasattr(self, "_lock_button"):
            self._lock_button.close()
        if hasattr(self, "_qr_popup"):
            self._qr_popup.close()
        super().closeEvent(event)
