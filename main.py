"""
主程序 - 游戏语音实时翻译器
整合音频捕获、语音识别、翻译和浮窗展示
"""

import asyncio
import os
import json
import queue
import signal
import sys
import threading
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import keyboard
from loguru import logger

from audio_capture import SystemAudioCapture, AudioConfig, list_input_devices
from speech_recognition import (
    SpeechRecognizer,
    WhisperConfig,
    DEFAULT_VAD_PARAMS,
    is_likely_asr_hallucination,
    sanitize_vad_parameters,
)
from translator import GameTranslator, TranslationConfig
from mobile_server import MobileWebSocketManager, WebSocketConfig


LANGUAGE_ALIASES = {
    "en": "en",
    "eng": "en",
    "english": "en",
    "英语": "en",
    "zh": "zh",
    "zh-cn": "zh",
    "zh-tw": "zh",
    "cmn": "zh",
    "yue": "zh",
    "chinese": "zh",
    "中文": "zh",
}
LANGUAGE_NAMES = {"en": "英语", "zh": "中文"}
OPPOSITE_LANGUAGE = {"en": "zh", "zh": "en"}
WHISPER_DEVICE_NAMES = {
    "cpu": "CPU（推荐）",
    "auto": "自动检测",
    "cuda": "NVIDIA GPU / CUDA",
}


def _normalize_language_code(value: str, default: str = "en") -> str:
    value = (value or "").strip().lower()
    normalized = LANGUAGE_ALIASES.get(value, value)
    return normalized if normalized in LANGUAGE_NAMES else default


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
    return value if value in WHISPER_DEVICE_NAMES else "cpu"


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
    mobile_url: str = ""


@dataclass
class HotkeyConfig:
    toggle_overlay: str = "ctrl+shift+t"
    toggle_translation: str = "ctrl+alt+s"
    clear_history: str = "ctrl+alt+c"


@dataclass
class AppConfig:
    audio: AudioConfig = None
    whisper: WhisperConfig = None
    translation: TranslationConfig = None
    overlay: OverlayConfig = None
    websocket: WebSocketConfig = None
    hotkeys: HotkeyConfig = None


class GameVoiceTranslator:

    def __init__(self, config_path: str = None):
        self._setup_logging()
        self.config = self._load_config(config_path)
        self._audio_capture: Optional[SystemAudioCapture] = None
        self._speech_recognizer: Optional[SpeechRecognizer] = None
        self._translator: Optional[GameTranslator] = None
        self._overlay = None
        self._mobile_server: Optional[MobileWebSocketManager] = None
        self._qt_app = None
        self._audio_timer = None
        self._mobile_loop: Optional[asyncio.AbstractEventLoop] = None
        self._mobile_thread: Optional[threading.Thread] = None
        self._mobile_start_error: Optional[BaseException] = None
        self._translation_loop: Optional[asyncio.AbstractEventLoop] = None
        self._translation_thread: Optional[threading.Thread] = None
        self._startup_thread: Optional[threading.Thread] = None
        self._startup_signals = None
        self._backend_ready = False
        self._running = False
        self._paused = False
        self._stopping = False
        self._processing_lock = threading.Lock()
        self._speech_queue = queue.Queue(maxsize=2)
        self._speech_stop_token = object()
        self._speech_worker_thread: Optional[threading.Thread] = None
        self._translation_item_seq = 0
        self._hotkey_handles = []
        self._pending_notices = []
        self._last_audio_device = (
            self.config.audio.input_device_id,
            self.config.audio.input_device_index,
            self.config.audio.input_device_name,
            self.config.audio.max_speech_seconds,
        )
        self._last_translation_settings = (
            self.config.translation.api_key,
            self.config.translation.model,
            self.config.translation.endpoint,
        )
        self._last_language_flow = (
            self.config.translation.source_lang,
            self.config.translation.target_lang,
        )
        self._last_whisper_device = _normalize_whisper_device(self.config.whisper.device)
        self._stats = {
            "audio_chunks": 0, "speech_detected": 0,
            "transcriptions": 0, "translations": 0, "errors": 0,
            "dropped_speech": 0
        }

    def _load_config(self, config_path: str = None) -> AppConfig:
        default_config = AppConfig(
            audio=AudioConfig(), whisper=WhisperConfig(),
            translation=TranslationConfig(), overlay=OverlayConfig(),
            websocket=WebSocketConfig(), hotkeys=HotkeyConfig()
        )
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for section in ["audio", "whisper", "translation", "overlay", "websocket", "hotkeys"]:
                    if section in data:
                        target = getattr(default_config, section)
                        for k, v in data[section].items():
                            if hasattr(target, k):
                                setattr(target, k, v)
                logger.info(f"已加载配置: {config_path}")
            except Exception as e:
                logger.error(f"配置加载失败: {e}")
        self._load_user_settings(default_config)
        self._sync_language_flow(default_config)
        self._sync_whisper_vad_limit(default_config)
        return default_config

    def _load_user_settings(self, config: AppConfig):
        settings_path = self._runtime_dir() / "user_settings.json"
        if not settings_path.exists():
            return
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for section in ["audio", "overlay", "hotkeys", "translation", "whisper"]:
                if section in data:
                    target = getattr(config, section)
                    for key, value in data[section].items():
                        if hasattr(target, key):
                            setattr(target, key, value)
            logger.info("已加载用户设置: {}", settings_path)
        except Exception as e:
            logger.warning("用户设置加载失败: {}", e)

    def _save_user_settings(self):
        settings_path = self._runtime_dir() / "user_settings.json"
        data = {
            "audio": {
                "input_device_id": self.config.audio.input_device_id,
                "input_device_index": self.config.audio.input_device_index,
                "input_device_name": self.config.audio.input_device_name,
                "max_speech_seconds": self.config.audio.max_speech_seconds,
            },
            "overlay": {
                "font_size": self.config.overlay.font_size,
                "text_color": self.config.overlay.text_color,
                "original_text_color": self.config.overlay.original_text_color,
                "bg_color": self.config.overlay.bg_color,
                "bg_opacity": self.config.overlay.bg_opacity,
                "window_width": self.config.overlay.window_width,
                "window_height": self.config.overlay.window_height,
                "opacity": self.config.overlay.opacity,
                "show_original": self.config.overlay.show_original,
            },
            "hotkeys": {
                "toggle_overlay": self.config.hotkeys.toggle_overlay,
                "toggle_translation": self.config.hotkeys.toggle_translation,
                "clear_history": self.config.hotkeys.clear_history,
            },
            "whisper": {
                "device": _normalize_whisper_device(self.config.whisper.device),
            },
            "translation": {
                "api_key": self.config.translation.api_key,
                "model": self.config.translation.model,
                "endpoint": self.config.translation.endpoint,
                "max_tokens": self.config.translation.max_tokens,
                "temperature": self.config.translation.temperature,
                "source_lang": self.config.translation.source_lang,
                "target_lang": self.config.translation.target_lang,
                "context_messages": self.config.translation.context_messages,
                "timeout_seconds": self.config.translation.timeout_seconds,
            },
        }
        try:
            settings_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("用户设置保存失败: {}", e)

    def _sync_language_flow(self, config: AppConfig = None):
        config = config or self.config
        source = _normalize_language_code(config.translation.source_lang, "en")
        target = _normalize_language_code(config.translation.target_lang, OPPOSITE_LANGUAGE[source])
        if target == source:
            target = OPPOSITE_LANGUAGE[source]
        config.translation.source_lang = source
        config.translation.target_lang = target
        config.whisper.language = source
        return source, target

    def _sync_whisper_vad_limit(self, config: AppConfig = None):
        config = config or self.config
        vad_parameters = dict(config.whisper.vad_parameters or DEFAULT_VAD_PARAMS)
        vad_parameters["max_speech_duration_s"] = float(config.audio.max_speech_seconds or 8)
        config.whisper.vad_parameters = sanitize_vad_parameters(vad_parameters)

    def _setup_logging(self):
        logger.remove()
        log_target = sys.stderr if sys.stderr is not None else open(os.devnull, "w", encoding="utf-8")
        log_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
        logger.add(
            log_target,
            level="INFO",
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        )
        logger.add(
            log_dir / "app.log",
            level="INFO",
            rotation="2 MB",
            retention=3,
            encoding="utf-8",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        )

    def _runtime_dir(self) -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent
        return Path(__file__).parent

    def _write_crash_report(self, title: str, exc: Exception, detail: str = ""):
        report_path = self._runtime_dir() / "crash_report.txt"
        content = [
            title,
            time.strftime("%Y-%m-%d %H:%M:%S"),
            detail,
            "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        ]
        try:
            report_path.write_text("\n\n".join(part for part in content if part), encoding="utf-8")
        except Exception:
            pass

    def _show_error_dialog(self, title: str, message: str):
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)
        except Exception:
            pass

    def _notify_user(self, title: str, message: str, level: str = "状态"):
        title = (title or "").strip()
        message = (message or "").strip()
        if not title and not message:
            return
        original = f"[{level}] {title}" if title else f"[{level}]"
        if self._overlay:
            self._overlay.add_translation(original, message)
        else:
            self._pending_notices.append((original, message))

    def _flush_pending_notices(self):
        if not self._overlay:
            return
        for original, message in self._pending_notices:
            self._overlay.add_translation(original, message)
        self._pending_notices.clear()

    def _describe_selected_audio_device(self) -> str:
        if not self._audio_capture or not self._audio_capture.selected_device:
            if self.config.audio.input_device_index is not None:
                return f"[{self.config.audio.input_device_index}] {self.config.audio.input_device_name}"
            return "自动选择"
        device = self._audio_capture.selected_device
        return (
            f"{device['type']} [{device['index']}]: {device['name']} "
            f"({device['sample_rate']}Hz/{device['channels']}ch)"
        )

    def _on_speech_detected(self, audio_data: bytes):
        if self._paused or not self._running:
            return
        self._stats["speech_detected"] += 1
        try:
            self._speech_queue.put_nowait(audio_data)
        except queue.Full:
            try:
                self._speech_queue.get_nowait()
                self._stats["dropped_speech"] += 1
                logger.warning("语音处理队列已满，丢弃最旧片段以保持实时性")
            except queue.Empty:
                pass
            try:
                self._speech_queue.put_nowait(audio_data)
            except queue.Full:
                self._stats["dropped_speech"] += 1
                logger.warning("语音处理队列仍然已满，丢弃当前片段")

    def _start_speech_worker(self):
        if self._speech_worker_thread and self._speech_worker_thread.is_alive():
            return
        self._speech_worker_thread = threading.Thread(
            target=self._speech_worker,
            name="speech-worker",
            daemon=True,
        )
        self._speech_worker_thread.start()
        logger.info("语音处理队列已启动")

    def _speech_worker(self):
        while True:
            audio_data = self._speech_queue.get()
            if audio_data is self._speech_stop_token:
                return
            self._process_speech(audio_data)

    def _stop_speech_worker(self):
        while True:
            try:
                self._speech_queue.get_nowait()
            except queue.Empty:
                break
        try:
            self._speech_queue.put_nowait(self._speech_stop_token)
        except queue.Full:
            pass
        if self._speech_worker_thread and self._speech_worker_thread.is_alive():
            self._speech_worker_thread.join(timeout=8)
        if self._speech_worker_thread and self._speech_worker_thread.is_alive():
            logger.warning("语音处理线程仍在结束中，跳过模型清理以避免资源释放冲突")
            return False
        self._speech_worker_thread = None
        return True

    def _process_speech(self, audio_data: bytes):
        try:
            if self._paused or not self._running:
                return
            t0 = time.time()
            with self._processing_lock:
                result = self._speech_recognizer.transcribe_audio_bytes_with_language(
                    audio_data,
                    sample_rate=self.config.audio.sample_rate
                )
            text = result.text
            if not text or len(text.strip()) < 2:
                return
            if is_likely_asr_hallucination(text):
                logger.warning("丢弃疑似 ASR 幻觉文本: {}", text[:120])
                return
            self._stats["transcriptions"] += 1
            logger.info(
                "[识别] {} (lang={}, prob={:.2f}, {:.1f}s)",
                text[:80],
                result.language or "unknown",
                result.language_probability,
                time.time()-t0
            )

            item_id = self._next_translation_item_id()
            if self._overlay:
                self._overlay.add_translation_with_id(item_id, text, "...正在翻译")
            self._start_async_translation(item_id, text, result.language)
        except Exception as e:
            self._stats["errors"] += 1
            logger.exception(f"处理失败: {e}")
            self._notify_user("处理失败", str(e), "错误")

    def _setup_hotkeys(self):
        try:
            self._remove_hotkeys()
            hotkeys = self.config.hotkeys
            self._hotkey_handles = [
                keyboard.add_hotkey(hotkeys.toggle_overlay, self._toggle_overlay),
                keyboard.add_hotkey(hotkeys.clear_history, self._clear_history),
                keyboard.add_hotkey(hotkeys.toggle_translation, self._toggle_translation),
            ]
            logger.info(
                "热键已注册: {}/{}/{}",
                hotkeys.toggle_overlay,
                hotkeys.clear_history,
                hotkeys.toggle_translation,
            )
        except Exception as e:
            logger.exception(f"热键注册失败: {e}")
            self._notify_user("热键注册失败", str(e), "错误")

    def _remove_hotkeys(self):
        for handle in self._hotkey_handles:
            try:
                keyboard.remove_hotkey(handle)
            except Exception:
                pass
        self._hotkey_handles = []

    def _toggle_overlay(self):
        if self._overlay:
            logger.info("触发热键: 切换浮窗")
            self._overlay._signals.toggle_visibility.emit()
            self._notify_user("热键", f"已触发: {self.config.hotkeys.toggle_overlay}", "状态")

    def _clear_history(self):
        if self._overlay:
            logger.info("触发热键: 清空历史")
            self._overlay._signals.clear_history.emit()
            self._notify_user("翻译历史", "已清空", "状态")

    def _toggle_translation(self):
        self._paused = not self._paused
        logger.info(f"翻译{'暂停' if self._paused else '恢复'}")
        self._notify_user("翻译状态", "翻译暂停" if self._paused else "翻译恢复", "状态")

    def _start_qt(self):
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, Qt, QTimer
        from overlay import GameOverlay

        class StartupSignals(QObject):
            backend_ready = pyqtSignal()
            backend_failed = pyqtSignal(str)

            def __init__(self, owner):
                super().__init__()
                self._owner = owner

            @pyqtSlot()
            def finish_backend_startup(self):
                self._owner._finish_backend_startup()

            @pyqtSlot(str)
            def handle_backend_startup_failure(self, message: str):
                self._owner._handle_backend_startup_failure(message)

        self._qt_app = QApplication.instance() or QApplication(sys.argv)
        self._startup_signals = StartupSignals(self)
        self._startup_signals.backend_ready.connect(
            self._startup_signals.finish_backend_startup,
            Qt.QueuedConnection,
        )
        self._startup_signals.backend_failed.connect(
            self._startup_signals.handle_backend_startup_failure,
            Qt.QueuedConnection,
        )
        if self._mobile_server:
            self.config.overlay.mobile_url = self._mobile_server.get_mobile_url()
        self._overlay = GameOverlay(
            self.config.overlay,
            self.config.hotkeys,
            self.config.audio,
            self.config.translation,
            [],
            self.config.whisper,
            self._apply_overlay_settings,
            self._list_audio_devices,
            self._request_shutdown,
        )
        self._overlay.show()
        self._flush_pending_notices()
        QTimer.singleShot(300, self._refresh_overlay_audio_devices)
        logger.info("浮窗已启动")

    def _request_shutdown(self):
        logger.info("收到退出按钮请求")
        if self._qt_app:
            self._qt_app.quit()

    def _apply_overlay_settings(
        self,
        overlay_config: OverlayConfig,
        hotkey_config: HotkeyConfig,
        audio_config: AudioConfig,
        translation_config: TranslationConfig,
        whisper_config: WhisperConfig,
    ):
        previous_device = self._last_audio_device
        previous_translation = self._last_translation_settings
        previous_whisper_device = self._last_whisper_device
        self.config.overlay = overlay_config
        self.config.hotkeys = hotkey_config
        self.config.translation = translation_config
        self.config.whisper.device = _normalize_whisper_device(
            getattr(whisper_config, "device", self.config.whisper.device)
        )
        self.config.audio.input_device_id = getattr(audio_config, "input_device_id", "")
        self.config.audio.input_device_index = audio_config.input_device_index
        self.config.audio.input_device_name = audio_config.input_device_name
        self.config.audio.max_speech_seconds = audio_config.max_speech_seconds
        previous_language_flow = self._last_language_flow
        current_language_flow = self._sync_language_flow()
        self._sync_whisper_vad_limit()
        if self._translator:
            self._translator.config = self.config.translation
        self._setup_hotkeys()
        self._save_user_settings()
        current_device = (
            self.config.audio.input_device_id,
            self.config.audio.input_device_index,
            self.config.audio.input_device_name,
            self.config.audio.max_speech_seconds,
        )
        current_translation = (
            self.config.translation.api_key,
            self.config.translation.model,
            self.config.translation.endpoint,
        )
        current_whisper_device = _normalize_whisper_device(self.config.whisper.device)
        if self._running and current_device != previous_device:
            self._restart_audio_capture()
        if current_language_flow != previous_language_flow:
            if self._translator:
                self._translator.clear_context()
            self._notify_user(
                "语言方向已更新",
                f"{LANGUAGE_NAMES[current_language_flow[0]]} → {LANGUAGE_NAMES[current_language_flow[1]]}",
                "状态",
            )
        if current_translation != previous_translation:
            self._notify_user(
                "翻译接口已更新",
                f"模型: {self.config.translation.model}\n兼容地址: {self.config.translation.endpoint}",
                "状态",
            )
        if current_whisper_device != previous_whisper_device:
            self._notify_user(
                "识别设备已更新",
                f"当前选择: {WHISPER_DEVICE_NAMES[current_whisper_device]}\n重启程序后生效",
                "状态",
            )
        self._last_audio_device = current_device
        self._last_translation_settings = current_translation
        self._last_language_flow = current_language_flow
        self._last_whisper_device = current_whisper_device
        logger.info(
            "浮窗设置已应用: opacity={:.2f}, bg_opacity={:.2f}, text_color={}, show_original={}, audio_device={} {}, max_speech={}s, language={}→{}, whisper_device={}, model={}, endpoint={}, hotkeys={}/{}/{}",
            overlay_config.opacity,
            overlay_config.bg_opacity,
            overlay_config.text_color,
            overlay_config.show_original,
            self.config.audio.input_device_index,
            self.config.audio.input_device_name,
            self.config.audio.max_speech_seconds,
            current_language_flow[0],
            current_language_flow[1],
            current_whisper_device,
            self.config.translation.model,
            self.config.translation.endpoint,
            hotkey_config.toggle_overlay,
            hotkey_config.clear_history,
            hotkey_config.toggle_translation,
        )

    def _start_mobile(self):
        self._mobile_server = MobileWebSocketManager(self.config.websocket)
        self._mobile_start_error = None

        def _run():
            loop = asyncio.new_event_loop()
            self._mobile_loop = loop
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._mobile_server.start_server())
            except BaseException as e:
                self._mobile_start_error = e
                if not self._stopping:
                    self._write_crash_report("手机端服务启动失败", e)
                    logger.exception("手机端服务启动失败: {}", e)
            finally:
                try:
                    loop.close()
                except Exception:
                    pass

        self._mobile_thread = threading.Thread(target=_run, name="mobile-server", daemon=True)
        self._mobile_thread.start()
        if self._mobile_server.wait_until_ready(5):
            logger.info(f"手机端: {self._mobile_server.get_mobile_url()}")
            return

        if self._mobile_start_error:
            message = str(self._mobile_start_error)
        elif self._mobile_thread.is_alive():
            message = f"手机端服务启动超时，请检查 {self.config.websocket.port} 端口或防火墙"
        else:
            message = "手机端服务启动失败，未能监听端口"
        logger.warning(message)
        self._notify_user("手机端未启动", message, "错误")

    def _start_translation_loop(self):
        def _run():
            self._translation_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._translation_loop)
            self._translation_loop.run_forever()

        self._translation_thread = threading.Thread(target=_run, daemon=True)
        self._translation_thread.start()
        while not self._translation_loop or not self._translation_loop.is_running():
            time.sleep(0.01)
        logger.info("翻译事件循环已启动")

    def _start_backend_thread(self):
        if self._startup_thread and self._startup_thread.is_alive():
            return
        self._startup_thread = threading.Thread(
            target=self._initialize_backend_services,
            name="startup-loader",
            daemon=True,
        )
        self._startup_thread.start()
        logger.info("后台启动线程已启动")

    def _initialize_backend_services(self):
        try:
            self._notify_user("语音识别模型", "正在后台加载 Whisper 模型，首次运行可能需要等待", "状态")
            self._speech_recognizer = SpeechRecognizer(self.config.whisper)
            self._translator = GameTranslator(self.config.translation)
            self._start_translation_loop()
            self._speech_recognizer.initialize()
            if self._stopping:
                return
            self._backend_ready = True
            if self._startup_signals:
                self._startup_signals.backend_ready.emit()
        except Exception as e:
            self._stats["errors"] += 1
            self._write_crash_report("启动失败", e)
            logger.exception(f"启动失败: {e}")
            if self._startup_signals:
                self._startup_signals.backend_failed.emit(str(e))

    def _finish_backend_startup(self):
        if self._stopping or self._running:
            return
        self._setup_hotkeys()
        signal.signal(signal.SIGINT, lambda s, f: self.stop())
        signal.signal(signal.SIGTERM, lambda s, f: self.stop())

        self._running = True
        self._start_speech_worker()
        self._print_banner()
        self._notify_user(
            "程序已启动",
            (
                f"当前方向: {LANGUAGE_NAMES[self.config.translation.source_lang]} "
                f"→ {LANGUAGE_NAMES[self.config.translation.target_lang]}\n"
                f"手机端: {self._mobile_server.get_mobile_url()}"
            ),
            "状态",
        )

        try:
            self._start_audio_capture()
        except Exception as e:
            self._stats["errors"] += 1
            self._show_audio_startup_warning(e)

        from PyQt5.QtCore import QTimer

        self._audio_timer = QTimer()
        self._audio_timer.timeout.connect(self._process_audio_tick)
        self._audio_timer.start(100)
        logger.info("后端服务已启动")

    def _handle_backend_startup_failure(self, message: str):
        if self._stopping:
            return
        self._notify_user("启动失败", message, "错误")
        self._show_error_dialog(
            "Game Voice Translator 启动失败",
            f"程序启动失败，已在程序目录生成 crash_report.txt。\n\n{message}",
        )
        if self._qt_app:
            self._qt_app.quit()

    def _start_audio_capture(self, notice_title: str = "音频捕获已启动"):
        if self._audio_capture:
            self._audio_capture.stop()
            self._audio_capture = None
        self._audio_capture = SystemAudioCapture(self.config.audio)
        self._audio_capture.set_speech_callback(self._on_speech_detected)
        self._audio_capture.start()
        self._notify_user(
            notice_title,
            f"{self._describe_selected_audio_device()} -> mono",
            "状态",
        )

    def _restart_audio_capture(self):
        try:
            self._start_audio_capture("音频设备已切换")
        except Exception as e:
            self._stats["errors"] += 1
            self._show_audio_startup_warning(e)

    def _list_audio_devices(self):
        try:
            return list_input_devices()
        except Exception as e:
            self._write_crash_report("音频设备枚举失败", e)
            logger.warning("音频设备枚举失败: {}", e)
            self._notify_user("音频设备枚举失败", str(e), "错误")
            return []

    def _refresh_overlay_audio_devices(self):
        if self._overlay and not self._stopping:
            self._overlay.request_audio_device_refresh()

    def _show_audio_startup_warning(self, exc: Exception):
        detail = (
            "音频采集启动失败，程序已继续运行，但暂时不会识别游戏声音。\n"
            "请在 Windows 声音设置里启用“立体声混音 / Stereo Mix”，"
            "或安装/选择可采集系统声音的虚拟声卡后重启本程序。\n"
            f"错误: {exc}"
        )
        self._write_crash_report("音频采集启动失败", exc, detail)
        logger.exception(detail)
        self._notify_user("音频采集未启动", detail, "错误")

    def _next_translation_item_id(self) -> str:
        self._translation_item_seq += 1
        return f"translation-{self._translation_item_seq}"

    def _run_in_private_event_loop(self, coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def _start_async_translation(self, item_id: str, text: str, detected_language: str = ""):
        if self._translation_loop and self._translation_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                self._translate_and_update(item_id, text, detected_language),
                self._translation_loop,
            )
            future.add_done_callback(
                lambda done, current_item_id=item_id: self._handle_translation_task_done(
                    current_item_id,
                    done,
                )
            )
            return

        def _run():
            try:
                self._run_in_private_event_loop(
                    self._translate_and_update(item_id, text, detected_language)
                )
            except Exception as e:
                self._handle_translation_error(item_id, e)

        threading.Thread(target=_run, name="translation-fallback", daemon=True).start()

    async def _translate_and_update(self, item_id: str, text: str, detected_language: str = ""):
        t0 = time.time()
        translated = await self._translator.translate(text, detected_language)
        if not translated or not translated.strip():
            translated = f"[翻译为空] {text}"
            logger.warning("翻译返回空结果，显示识别文本")

        elapsed = time.time() - t0
        logger.info(f"[翻译] {translated[:80]} ({elapsed:.1f}s)")
        is_notice = translated.startswith("[翻译") or translated.startswith("[未翻译]")

        if is_notice:
            if translated.startswith("[翻译"):
                self._stats["errors"] += 1
            if self._overlay:
                self._overlay.update_translation(item_id, translated)
            else:
                self._notify_user(
                    "翻译服务异常",
                    translated,
                    "错误" if translated.startswith("[翻译") else "提示",
                )
        else:
            self._stats["translations"] += 1
            if self._overlay:
                logger.info("更新浮窗翻译")
                self._overlay.update_translation(item_id, translated)

        if self._mobile_server:
            self._broadcast_to_mobile(text, translated)

    def _handle_translation_task_done(self, item_id: str, future):
        try:
            future.result()
        except Exception as e:
            logger.exception(f"异步翻译任务失败: {e}")
            self._stats["errors"] += 1
            if self._overlay:
                self._overlay.update_translation(item_id, f"[翻译失败] {str(e)[:180]}")

    def _handle_translation_error(self, item_id: str, exc: Exception):
        logger.exception(f"翻译任务失败: {exc}")
        self._stats["errors"] += 1
        if self._overlay:
            self._overlay.update_translation(item_id, f"[翻译失败] {str(exc)[:180]}")

    def _broadcast_to_mobile(self, original: str, translated: str):
        if not self._mobile_server:
            return
        if self._mobile_loop and self._mobile_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                self._mobile_server.broadcast_translation(original, translated),
                self._mobile_loop
            )
            future.add_done_callback(self._handle_mobile_broadcast_done)
            return
        logger.debug("手机端事件循环未运行，跳过本次手机端推送")

    def _handle_mobile_broadcast_done(self, future):
        try:
            future.result()
        except Exception as e:
            logger.warning("手机端推送失败: {}", e)

    def _process_audio_tick(self):
        if not self._running or self._paused:
            return
        if self._audio_capture:
            self._audio_capture.process_audio()

    def _print_banner(self):
        if sys.stdout is None:
            return
        hotkeys = self.config.hotkeys
        print("""
╔══════════════════════════════════════════════╗
║       游戏语音实时翻译器  v0.1.3          ║
╠══════════════════════════════════════════════╣
║  热键:                                       ║
║    {toggle_overlay:<14} 切换浮窗显示/隐藏       ║
║    {clear_history:<14} 清空翻译历史            ║
║    {toggle_translation:<14} 暂停/恢复翻译       ║
╠══════════════════════════════════════════════╣
║  手机端: {url}  ║
╠══════════════════════════════════════════════╣
║  按 Ctrl+C 停止                               ║
╚══════════════════════════════════════════════╝
""".format(
            toggle_overlay=hotkeys.toggle_overlay,
            clear_history=hotkeys.clear_history,
            toggle_translation=hotkeys.toggle_translation,
            url=self._mobile_server.get_mobile_url()
        ))

    def start(self):
        logger.info("正在启动...")
        try:
            self._start_mobile()
            self._start_qt()
            self._notify_user(
                "正在启动",
                "浮窗已显示，正在后台加载语音识别和翻译服务",
                "状态",
            )
            self._start_backend_thread()

            self._qt_app.exec_()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            self._write_crash_report("启动失败", e)
            logger.exception(f"启动失败: {e}")
            self._notify_user("启动失败", str(e), "错误")
            self._show_error_dialog(
                "Game Voice Translator 启动失败",
                f"程序启动失败，已在程序目录生成 crash_report.txt。\n\n{e}",
            )
        finally:
            self.stop()

    def stop(self):
        if self._stopping:
            return
        self._stopping = True
        logger.info("正在停止...")
        self._running = False
        if self._audio_timer:
            self._audio_timer.stop()
        if self._audio_capture:
            self._audio_capture.stop()
        speech_worker_stopped = self._stop_speech_worker()
        self._remove_hotkeys()
        startup_in_progress = self._startup_thread and self._startup_thread.is_alive()
        if startup_in_progress:
            logger.warning("后台启动仍在进行，跳过模型清理以避免资源释放冲突")
        if self._speech_recognizer and speech_worker_stopped and not startup_in_progress:
            self._speech_recognizer.cleanup()
        if self._mobile_server and self._mobile_loop and self._mobile_loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._mobile_server.stop_server(),
                    self._mobile_loop
                )
                future.result(timeout=3)
            except Exception as e:
                logger.warning(f"手机端服务停止失败: {e}")
        if self._translator and speech_worker_stopped and not startup_in_progress:
            try:
                if self._translation_loop and self._translation_loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(
                        self._translator.close(),
                        self._translation_loop
                    )
                    future.result(timeout=3)
                else:
                    self._run_in_private_event_loop(self._translator.close())
            except Exception as e:
                logger.warning(f"翻译器关闭失败: {e}")
        if self._translation_loop and self._translation_loop.is_running() and speech_worker_stopped and not startup_in_progress:
            self._translation_loop.call_soon_threadsafe(self._translation_loop.stop)
        if self._translation_thread and self._translation_thread.is_alive() and speech_worker_stopped and not startup_in_progress:
            self._translation_thread.join(timeout=3)
        if self._translation_loop and not self._translation_loop.is_closed() and speech_worker_stopped and not startup_in_progress:
            self._translation_loop.close()
        if self._overlay:
            self._overlay.close()
        if self._qt_app:
            self._qt_app.quit()

        if sys.stdout is not None:
            print(f"\n翻译统计: 识别 {self._stats['transcriptions']} 条, "
                  f"翻译 {self._stats['translations']} 条, 错误 {self._stats['errors']} 次")
        logger.info("已停止")


def main():
    config_path = None
    default_config = Path(__file__).parent / "config.json"
    if default_config.exists():
        config_path = str(default_config)

    app = GameVoiceTranslator(config_path)
    app.start()


if __name__ == "__main__":
    main()
