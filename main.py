"""
主程序 - VoxGo
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
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import keyboard
from loguru import logger

from app_info import APP_NAME, APP_VERSION, USER_AGENT
from audio_capture import (
    LATENCY_MODE_ACCURATE,
    LATENCY_MODE_BALANCED,
    LATENCY_MODE_FAST,
    SystemAudioCapture,
    AudioConfig,
    SpeechSegment,
    SAFE_MAX_SPEECH_THRESHOLD_DBFS,
    apply_audio_latency_preset,
    infer_latency_mode,
    list_input_devices,
    normalize_latency_mode,
    should_drop_speech_segment,
)
from speech_recognition import (
    MODEL_DOWNLOAD_SOURCE_CUSTOM_HF_ENDPOINT,
    ModelDownloadProgress,
    SpeechRecognizer,
    WhisperConfig,
    DEFAULT_VAD_PARAMS,
    describe_model_download_source,
    normalize_model_download_endpoint,
    normalize_model_download_source,
    sanitize_vad_parameters,
    should_drop_transcription_result,
)
from translator import (
    GameTranslator,
    TranslationConfig,
    TRANSLATION_PROVIDERS,
    normalize_translation_provider,
)
from mobile_server import MobileWebSocketManager, WebSocketConfig
from update_checker import (
    UpdateCheckResult,
    UpdateSettings,
    check_for_update,
    normalize_update_channel,
    should_check_for_update,
)


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
WHISPER_BEAM_SIZE_BY_LATENCY_MODE = {
    LATENCY_MODE_FAST: 1,
    LATENCY_MODE_BALANCED: 1,
    LATENCY_MODE_ACCURATE: 5,
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


def _hotkey_label(value: str) -> str:
    return str(value or "").strip() or "未设置"


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
    window_x: Optional[int] = None
    window_y: Optional[int] = None
    opacity: float = 0.85
    original_text_color: str = "#B7C4D8"
    show_original: bool = True
    draggable: bool = True
    locked: bool = False
    compact_mode: bool = False
    mobile_url: str = ""


@dataclass
class HotkeyConfig:
    toggle_overlay: str = "ctrl+shift+t"
    toggle_translation: str = "ctrl+alt+s"
    clear_history: str = "ctrl+alt+c"
    toggle_lock: str = ""
    toggle_compact: str = ""


@dataclass
class RuntimeConfig:
    setup_completed: bool = False


@dataclass
class DebugConfig:
    enabled: bool = False
    log_level: str = "INFO"
    save_audio_chunks: bool = False
    save_transcripts: bool = False


@dataclass
class LatencyTrace:
    item_id: str
    speech_detected_at: float
    queued_at: float
    dequeued_at: float = 0.0
    transcription_started_at: float = 0.0
    transcription_finished_at: float = 0.0
    translation_started_at: float = 0.0
    translation_finished_at: float = 0.0
    overlay_updated_at: float = 0.0

    def summary_ms(self) -> dict:
        wait_ms = self._elapsed_ms(self.queued_at, self.dequeued_at)
        recognition_ms = self._elapsed_ms(self.transcription_started_at, self.transcription_finished_at)
        translation_ms = self._elapsed_ms(self.translation_started_at, self.translation_finished_at)
        overlay_ms = self._elapsed_ms(self.translation_finished_at, self.overlay_updated_at)
        total_ms = self._elapsed_ms(self.speech_detected_at, self.overlay_updated_at)
        return {
            "wait_ms": wait_ms,
            "recognition_ms": recognition_ms,
            "translation_ms": translation_ms,
            "overlay_ms": overlay_ms,
            "total_ms": total_ms,
        }

    @staticmethod
    def _elapsed_ms(start: float, end: float) -> int:
        if not start or not end:
            return 0
        return int(round(max(0.0, end - start) * 1000))


@dataclass
class SpeechWorkItem:
    segment: SpeechSegment
    trace: LatencyTrace


@dataclass
class AppConfig:
    audio: AudioConfig = None
    whisper: WhisperConfig = None
    translation: TranslationConfig = None
    overlay: OverlayConfig = None
    websocket: WebSocketConfig = None
    hotkeys: HotkeyConfig = None
    app: RuntimeConfig = None
    debug: DebugConfig = None
    update: UpdateSettings = None


class VoxGoApp:

    def __init__(self, config_path: str = None):
        self._setup_logging()
        self.config = self._load_config(config_path)
        self._audio_capture: Optional[SystemAudioCapture] = None
        self._speech_recognizer: Optional[SpeechRecognizer] = None
        self._translator: Optional[GameTranslator] = None
        self._overlay = None
        self._mobile_server: Optional[MobileWebSocketManager] = None
        self._qt_app = None
        self._tray_icon = None
        self._tray_menu = None
        self._tray_actions = {}
        self._audio_timer = None
        self._mobile_loop: Optional[asyncio.AbstractEventLoop] = None
        self._mobile_thread: Optional[threading.Thread] = None
        self._mobile_start_error: Optional[BaseException] = None
        self._translation_loop: Optional[asyncio.AbstractEventLoop] = None
        self._translation_thread: Optional[threading.Thread] = None
        self._startup_thread: Optional[threading.Thread] = None
        self._update_check_thread: Optional[threading.Thread] = None
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
        self._latency_traces = {}
        self._last_latency_summary = {}
        self._recent_transcripts = deque(maxlen=12)
        self._last_audio_device = (
            self.config.audio.input_device_id,
            self.config.audio.input_device_index,
            self.config.audio.input_device_name,
            self.config.audio.latency_mode,
            self.config.audio.chunk_duration_ms,
            self.config.audio.speech_threshold_blocks,
            self.config.audio.silence_limit_blocks,
            self.config.audio.max_buffer_blocks,
            self.config.audio.max_speech_seconds,
            self.config.audio.pre_roll_ms,
            self.config.audio.speech_idle_timeout_ms,
        )
        self._last_translation_settings = (
            normalize_translation_provider(self.config.translation.provider),
            self.config.translation.api_key,
            self.config.translation.model,
            self.config.translation.endpoint,
        )
        self._last_language_flow = (
            self.config.translation.source_lang,
            self.config.translation.target_lang,
        )
        self._last_whisper_device = _normalize_whisper_device(self.config.whisper.device)
        self._last_model_download_source = (
            normalize_model_download_source(
                getattr(self.config.whisper, "model_download_source", "modelscope"),
                getattr(self.config.whisper, "model_download_endpoint", ""),
            ),
            normalize_model_download_endpoint(
                getattr(self.config.whisper, "model_download_endpoint", "")
            ),
        )
        self._model_download_notice_started = False
        self._last_model_download_update = 0.0
        self._last_model_download_bytes = (0, 0, 0.0)
        self._stats = {
            "audio_chunks": 0, "speech_detected": 0,
            "transcriptions": 0, "translations": 0, "errors": 0,
            "dropped_speech": 0, "filtered_speech": 0
        }

    def _load_config(self, config_path: str = None) -> AppConfig:
        default_config = AppConfig(
            audio=AudioConfig(), whisper=WhisperConfig(),
            translation=TranslationConfig(), overlay=OverlayConfig(),
            websocket=WebSocketConfig(), hotkeys=HotkeyConfig(),
            app=RuntimeConfig(), debug=DebugConfig(), update=UpdateSettings()
        )
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
                for section in [
                    "audio", "whisper", "translation", "overlay", "websocket",
                    "hotkeys", "app", "debug", "update",
                ]:
                    if section in data:
                        target = getattr(default_config, section)
                        for k, v in data[section].items():
                            if hasattr(target, k):
                                setattr(target, k, v)
                self._migrate_legacy_model_download_settings(default_config, data.get("whisper", {}))
                self._migrate_runtime_defaults(
                    default_config,
                    preserve_existing_audio_tuning="latency_mode" not in data.get("audio", {}),
                )
                logger.info(f"已加载配置: {config_path}")
            except Exception as e:
                logger.error(f"配置加载失败: {e}")
        self._load_user_settings(default_config)
        self._migrate_runtime_defaults(default_config)
        self._sync_language_flow(default_config)
        self._sync_whisper_vad_limit(default_config)
        return default_config

    def _load_user_settings(self, config: AppConfig):
        settings_path = self._runtime_dir() / "user_settings.json"
        if not settings_path.exists():
            return
        try:
            with open(settings_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            for section in ["audio", "overlay", "hotkeys", "translation", "whisper", "app", "debug", "update"]:
                if section in data:
                    target = getattr(config, section)
                    for key, value in data[section].items():
                        if hasattr(target, key):
                            setattr(target, key, value)
            if "latency_mode" not in data.get("audio", {}):
                config.audio.latency_mode = ""
            self._migrate_legacy_model_download_settings(config, data.get("whisper", {}))
            self._migrate_runtime_defaults(
                config,
                preserve_existing_audio_tuning="latency_mode" not in data.get("audio", {}),
            )
            logger.info("已加载用户设置: {}", settings_path)
        except Exception as e:
            logger.warning("用户设置加载失败: {}", e)

    def _migrate_legacy_model_download_settings(self, config: AppConfig, whisper_data: dict):
        if not whisper_data:
            return
        endpoint = normalize_model_download_endpoint(whisper_data.get("model_download_endpoint", ""))
        if endpoint and "model_download_source" not in whisper_data:
            config.whisper.model_download_source = MODEL_DOWNLOAD_SOURCE_CUSTOM_HF_ENDPOINT

    def _migrate_runtime_defaults(self, config: AppConfig, preserve_existing_audio_tuning: bool = True):
        if not getattr(config, "update", None):
            config.update = UpdateSettings()
        try:
            if float(getattr(config.translation, "timeout_seconds", 0) or 0) < 12:
                config.translation.timeout_seconds = 12
        except Exception:
            config.translation.timeout_seconds = 12
        if not hasattr(config.translation, "max_concurrent_requests"):
            config.translation.max_concurrent_requests = 2
        try:
            config.translation.max_concurrent_requests = max(
                1,
                min(4, int(getattr(config.translation, "max_concurrent_requests", 2) or 2)),
            )
        except Exception:
            config.translation.max_concurrent_requests = 2
        if not hasattr(config.whisper, "cpu_threads"):
            config.whisper.cpu_threads = 2
        if not hasattr(config.whisper, "num_workers"):
            config.whisper.num_workers = 1
        if preserve_existing_audio_tuning:
            config.audio.latency_mode = infer_latency_mode(config.audio)
        else:
            config.audio.latency_mode = normalize_latency_mode(
                getattr(config.audio, "latency_mode", LATENCY_MODE_BALANCED)
            )
        latency_mode = apply_audio_latency_preset(config.audio)
        try:
            config.whisper.beam_size = max(
                1,
                min(5, int(getattr(config.whisper, "beam_size", 5) or 5)),
            )
        except Exception:
            config.whisper.beam_size = 5
        if latency_mode in WHISPER_BEAM_SIZE_BY_LATENCY_MODE:
            config.whisper.beam_size = WHISPER_BEAM_SIZE_BY_LATENCY_MODE[latency_mode]
        try:
            config.audio.chunk_duration_ms = max(
                60,
                min(1000, int(getattr(config.audio, "chunk_duration_ms", 220) or 220)),
            )
        except Exception:
            config.audio.chunk_duration_ms = 220
        try:
            config.audio.speech_threshold_blocks = max(
                1,
                min(20, int(getattr(config.audio, "speech_threshold_blocks", 2) or 2)),
            )
        except Exception:
            config.audio.speech_threshold_blocks = 2
        try:
            config.audio.silence_limit_blocks = max(
                1,
                min(50, int(getattr(config.audio, "silence_limit_blocks", 4) or 4)),
            )
        except Exception:
            config.audio.silence_limit_blocks = 4
        try:
            config.audio.max_buffer_blocks = max(
                10,
                min(1000, int(getattr(config.audio, "max_buffer_blocks", 120) or 120)),
            )
        except Exception:
            config.audio.max_buffer_blocks = 120
        try:
            config.audio.pre_roll_ms = max(
                0,
                min(2000, int(getattr(config.audio, "pre_roll_ms", 450) or 0)),
            )
        except Exception:
            config.audio.pre_roll_ms = 450
        try:
            config.audio.speech_idle_timeout_ms = max(
                100,
                min(3000, int(getattr(config.audio, "speech_idle_timeout_ms", 650) or 650)),
            )
        except Exception:
            config.audio.speech_idle_timeout_ms = 650
        try:
            config.whisper.min_language_probability = max(
                0.0,
                min(1.0, float(getattr(config.whisper, "min_language_probability", 0.35) or 0.0)),
            )
        except Exception:
            config.whisper.min_language_probability = 0.35
        try:
            config.audio.min_segment_seconds = max(
                0.0,
                min(3.0, float(getattr(config.audio, "min_segment_seconds", 0.35) or 0.0)),
            )
        except Exception:
            config.audio.min_segment_seconds = 0.35
        try:
            config.audio.min_segment_peak_margin_db = max(
                0.0,
                min(12.0, float(getattr(config.audio, "min_segment_peak_margin_db", 1.5) or 0.0)),
            )
        except Exception:
            config.audio.min_segment_peak_margin_db = 1.5
        try:
            config.audio.max_speech_threshold = min(
                SAFE_MAX_SPEECH_THRESHOLD_DBFS,
                float(
                    getattr(
                        config.audio,
                        "max_speech_threshold",
                        SAFE_MAX_SPEECH_THRESHOLD_DBFS,
                    )
                    or SAFE_MAX_SPEECH_THRESHOLD_DBFS
                ),
            )
        except Exception:
            config.audio.max_speech_threshold = SAFE_MAX_SPEECH_THRESHOLD_DBFS
        try:
            config.audio.min_speech_threshold = float(
                getattr(config.audio, "min_speech_threshold", -45.0) or -45.0
            )
        except Exception:
            config.audio.min_speech_threshold = -45.0
        if config.audio.min_speech_threshold > config.audio.max_speech_threshold:
            config.audio.min_speech_threshold = config.audio.max_speech_threshold
        config.update.enabled = bool(getattr(config.update, "enabled", True))
        config.update.channel = normalize_update_channel(getattr(config.update, "channel", "stable"))
        try:
            config.update.last_check_at = float(getattr(config.update, "last_check_at", 0) or 0)
        except Exception:
            config.update.last_check_at = 0
        config.update.ignored_version = str(getattr(config.update, "ignored_version", "") or "").strip().lstrip("v")
        config.update.manifest_url = str(getattr(config.update, "manifest_url", "") or "").strip()

    def _save_user_settings(self):
        settings_path = self._runtime_dir() / "user_settings.json"
        data = {
            "app": {
                "setup_completed": bool(getattr(self.config.app, "setup_completed", False)),
            },
            "audio": {
                "latency_mode": self.config.audio.latency_mode,
                "input_device_id": self.config.audio.input_device_id,
                "input_device_index": self.config.audio.input_device_index,
                "input_device_name": self.config.audio.input_device_name,
                "chunk_duration_ms": self.config.audio.chunk_duration_ms,
                "speech_threshold_blocks": self.config.audio.speech_threshold_blocks,
                "silence_limit_blocks": self.config.audio.silence_limit_blocks,
                "max_buffer_blocks": self.config.audio.max_buffer_blocks,
                "max_speech_seconds": self.config.audio.max_speech_seconds,
                "pre_roll_ms": self.config.audio.pre_roll_ms,
                "speech_idle_timeout_ms": self.config.audio.speech_idle_timeout_ms,
                "min_speech_threshold": self.config.audio.min_speech_threshold,
                "max_speech_threshold": self.config.audio.max_speech_threshold,
                "min_segment_seconds": self.config.audio.min_segment_seconds,
                "min_segment_peak_margin_db": self.config.audio.min_segment_peak_margin_db,
            },
            "overlay": {
                "font_size": self.config.overlay.font_size,
                "text_color": self.config.overlay.text_color,
                "original_text_color": self.config.overlay.original_text_color,
                "bg_color": self.config.overlay.bg_color,
                "bg_opacity": self.config.overlay.bg_opacity,
                "window_width": self.config.overlay.window_width,
                "window_height": self.config.overlay.window_height,
                "window_x": self.config.overlay.window_x,
                "window_y": self.config.overlay.window_y,
                "opacity": self.config.overlay.opacity,
                "show_original": self.config.overlay.show_original,
                "draggable": self.config.overlay.draggable,
                "locked": self.config.overlay.locked,
                "compact_mode": bool(getattr(self.config.overlay, "compact_mode", False)),
            },
            "hotkeys": {
                "toggle_overlay": self.config.hotkeys.toggle_overlay,
                "toggle_translation": self.config.hotkeys.toggle_translation,
                "clear_history": self.config.hotkeys.clear_history,
                "toggle_lock": self.config.hotkeys.toggle_lock,
                "toggle_compact": self.config.hotkeys.toggle_compact,
            },
            "whisper": {
                "device": _normalize_whisper_device(self.config.whisper.device),
                "cpu_threads": int(getattr(self.config.whisper, "cpu_threads", 2) or 2),
                "num_workers": int(getattr(self.config.whisper, "num_workers", 1) or 1),
                "model_download_source": normalize_model_download_source(
                    getattr(self.config.whisper, "model_download_source", "modelscope"),
                    getattr(self.config.whisper, "model_download_endpoint", ""),
                ),
                "model_download_endpoint": normalize_model_download_endpoint(
                    getattr(self.config.whisper, "model_download_endpoint", "")
                ),
            },
            "translation": {
                "provider": normalize_translation_provider(self.config.translation.provider),
                "api_key": self.config.translation.api_key,
                "model": self.config.translation.model,
                "endpoint": self.config.translation.endpoint,
                "max_tokens": self.config.translation.max_tokens,
                "temperature": self.config.translation.temperature,
                "source_lang": self.config.translation.source_lang,
                "target_lang": self.config.translation.target_lang,
                "context_messages": self.config.translation.context_messages,
                "timeout_seconds": self.config.translation.timeout_seconds,
                "max_concurrent_requests": self.config.translation.max_concurrent_requests,
            },
            "debug": {
                "enabled": bool(getattr(self.config.debug, "enabled", False)),
                "log_level": getattr(self.config.debug, "log_level", "INFO"),
                "save_audio_chunks": bool(getattr(self.config.debug, "save_audio_chunks", False)),
                "save_transcripts": bool(getattr(self.config.debug, "save_transcripts", False)),
            },
            "update": {
                "enabled": bool(getattr(self.config.update, "enabled", True)),
                "channel": normalize_update_channel(getattr(self.config.update, "channel", "stable")),
                "last_check_at": float(getattr(self.config.update, "last_check_at", 0) or 0),
                "ignored_version": str(getattr(self.config.update, "ignored_version", "") or "").strip().lstrip("v"),
                "manifest_url": str(getattr(self.config.update, "manifest_url", "") or "").strip(),
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

    def _refresh_cached_settings(self):
        self._last_audio_device = (
            self.config.audio.input_device_id,
            self.config.audio.input_device_index,
            self.config.audio.input_device_name,
            self.config.audio.latency_mode,
            self.config.audio.chunk_duration_ms,
            self.config.audio.speech_threshold_blocks,
            self.config.audio.silence_limit_blocks,
            self.config.audio.max_buffer_blocks,
            self.config.audio.max_speech_seconds,
            self.config.audio.pre_roll_ms,
            self.config.audio.speech_idle_timeout_ms,
        )
        self._last_translation_settings = (
            normalize_translation_provider(self.config.translation.provider),
            self.config.translation.api_key,
            self.config.translation.model,
            self.config.translation.endpoint,
        )
        self._last_language_flow = (
            self.config.translation.source_lang,
            self.config.translation.target_lang,
        )
        self._last_whisper_device = _normalize_whisper_device(self.config.whisper.device)
        self._last_model_download_source = (
            normalize_model_download_source(
                getattr(self.config.whisper, "model_download_source", "modelscope"),
                getattr(self.config.whisper, "model_download_endpoint", ""),
            ),
            normalize_model_download_endpoint(
                getattr(self.config.whisper, "model_download_endpoint", "")
            ),
        )

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

    def _notify_model_download_progress(self, progress: ModelDownloadProgress):
        if progress.downloaded_bytes or progress.total_bytes:
            self._last_model_download_bytes = (
                progress.downloaded_bytes,
                progress.total_bytes,
                progress.percent,
            )

        now = time.time()
        if progress.status == "downloading" and now - self._last_model_download_update < 0.5:
            return
        self._last_model_download_update = now

        message = self._format_model_download_progress(progress)
        item_id = "model-download-progress"
        original = "[状态] 模型下载"
        if self._overlay:
            if self._model_download_notice_started:
                self._overlay.update_translation(item_id, message)
            else:
                self._overlay.add_translation_with_id(item_id, original, message)
                self._model_download_notice_started = True
        else:
            self._pending_notices.append((original, message))

    def _format_model_download_progress(self, progress: ModelDownloadProgress) -> str:
        model = progress.model_name or self.config.whisper.model_size
        repo = progress.repo_id or model
        source = progress.source or describe_model_download_source(
            getattr(self.config.whisper, "model_download_source", "modelscope"),
            getattr(self.config.whisper, "model_download_endpoint", "")
        )
        header = f"模型: {model}\n仓库: {repo}\n来源: {source}"

        if progress.status == "checking":
            return f"{header}\n正在检查本地缓存"
        if progress.status == "complete":
            detail = progress.message or "模型缓存已就绪"
            downloaded, total, percent = self._last_model_download_bytes
            progress_line = self._format_download_amount(downloaded, total, percent)
            if progress_line:
                return f"{header}\n已下载: {progress_line}\n{detail}，正在加载识别引擎"
            return f"{header}\n{detail}，正在加载识别引擎"
        if progress.status == "error":
            downloaded, total, percent = self._last_model_download_bytes
            progress_line = self._format_download_amount(downloaded, total, percent)
            suffix = f"\n已下载: {progress_line}" if progress_line else ""
            return f"{progress.message or '模型下载失败'}{suffix}"

        progress_line = self._format_download_amount(
            progress.downloaded_bytes,
            progress.total_bytes,
            progress.percent,
        )
        if not progress_line:
            progress_line = "正在准备下载"
        return f"{header}\n已下载: {progress_line}"

    def _format_download_amount(self, downloaded: int, total: int, percent: float) -> str:
        if total:
            return f"{self._format_bytes(downloaded)} / {self._format_bytes(total)} ({percent:.1f}%)"
        if downloaded:
            return self._format_bytes(downloaded)
        return ""

    @staticmethod
    def _format_bytes(value: int) -> str:
        size = float(max(0, int(value or 0)))
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                if unit == "B":
                    return f"{int(size)} B"
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} GB"

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

    def _coerce_speech_segment(self, speech_segment) -> SpeechSegment:
        if isinstance(speech_segment, SpeechSegment):
            return speech_segment
        audio_data = speech_segment or b""
        sample_rate = max(1, int(getattr(self.config.audio, "sample_rate", 16000) or 16000))
        duration = (len(audio_data) // 2) / sample_rate
        return SpeechSegment(
            audio_data=audio_data,
            sample_rate=sample_rate,
            duration_seconds=duration,
            voice_duration_seconds=duration,
            block_count=0,
            voice_blocks=0,
            peak_rms_dbfs=-120.0,
            energy_threshold_dbfs=-120.0,
            noise_floor_dbfs=None,
            reason="兼容旧音频字节",
        )

    def _recent_transcript_texts(self, now: float = None) -> list:
        now = now or time.time()
        recent = [
            (created_at, text)
            for created_at, text in self._recent_transcripts
            if now - created_at <= 8.0
        ]
        self._recent_transcripts = deque(recent, maxlen=12)
        return [text for _, text in recent]

    def _remember_transcript(self, text: str):
        self._recent_transcripts.append((time.time(), text))

    def _on_speech_detected(self, speech_segment):
        if self._paused or not self._running:
            return
        segment = self._coerce_speech_segment(speech_segment)
        self._stats["speech_detected"] += 1
        drop_reason = should_drop_speech_segment(segment, self.config.audio)
        if drop_reason:
            self._stats["filtered_speech"] += 1
            logger.info(
                "丢弃疑似误触发音频片段: {}，voice={:.2f}s, total={:.2f}s, peak={:.1f} dBFS, gate={:.1f} dBFS, cut={}",
                drop_reason,
                segment.voice_duration_seconds,
                segment.duration_seconds,
                segment.peak_rms_dbfs,
                segment.energy_threshold_dbfs,
                segment.reason,
            )
            return
        now = time.time()
        work_item = SpeechWorkItem(
            segment=segment,
            trace=LatencyTrace(item_id="", speech_detected_at=now, queued_at=now),
        )
        try:
            self._speech_queue.put_nowait(work_item)
        except queue.Full:
            try:
                self._speech_queue.get_nowait()
                self._stats["dropped_speech"] += 1
                logger.warning("语音处理队列已满，丢弃最旧片段以保持实时性")
            except queue.Empty:
                pass
            try:
                work_item.trace.queued_at = time.time()
                self._speech_queue.put_nowait(work_item)
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
            work_item = self._speech_queue.get()
            if work_item is self._speech_stop_token:
                return
            self._process_speech(work_item)

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

    def _process_speech(self, work_item):
        try:
            if self._paused or not self._running:
                return
            if isinstance(work_item, SpeechWorkItem):
                segment = work_item.segment
                trace = work_item.trace
            elif isinstance(work_item, SpeechSegment):
                segment = work_item
                now = time.time()
                trace = LatencyTrace(item_id="", speech_detected_at=now, queued_at=now)
            else:
                segment = self._coerce_speech_segment(work_item)
                now = time.time()
                trace = LatencyTrace(item_id="", speech_detected_at=now, queued_at=now)
            drop_reason = should_drop_speech_segment(segment, self.config.audio)
            if drop_reason:
                self._stats["filtered_speech"] += 1
                logger.info("处理前丢弃疑似误触发音频片段: {}", drop_reason)
                return
            trace.dequeued_at = time.time()
            t0 = time.time()
            trace.transcription_started_at = t0
            logger.info(
                "开始识别语音片段: voice={:.2f}s, total={:.2f}s, peak={:.1f} dBFS, gate={:.1f} dBFS, cut={}",
                segment.voice_duration_seconds,
                segment.duration_seconds,
                segment.peak_rms_dbfs,
                segment.energy_threshold_dbfs,
                segment.reason,
            )
            with self._processing_lock:
                result = self._speech_recognizer.transcribe_audio_bytes_with_language(
                    segment.audio_data,
                    sample_rate=segment.sample_rate or self.config.audio.sample_rate
                )
            trace.transcription_finished_at = time.time()
            text = result.text
            if not text or len(text.strip()) < 2:
                self._stats["filtered_speech"] += 1
                logger.info(
                    "识别结果为空或过短: text_len={}, lang={}, prob={:.2f}, voice={:.2f}s, total={:.2f}s, peak={:.1f} dBFS, gate={:.1f} dBFS",
                    len(text.strip()) if text else 0,
                    result.language or "unknown",
                    result.language_probability,
                    segment.voice_duration_seconds,
                    segment.duration_seconds,
                    segment.peak_rms_dbfs,
                    segment.energy_threshold_dbfs,
                )
                return
            recent_texts = self._recent_transcript_texts()
            drop_reason = should_drop_transcription_result(
                result,
                expected_language=self.config.whisper.language,
                recent_texts=recent_texts,
                config=self.config.whisper,
            )
            if drop_reason:
                self._stats["filtered_speech"] += 1
                logger.info(
                    "丢弃疑似误识别文本: {}，text={}, lang={}, prob={:.2f}",
                    drop_reason,
                    text[:120],
                    result.language or "unknown",
                    result.language_probability,
                )
                return
            self._stats["transcriptions"] += 1
            self._remember_transcript(text)
            logger.info(
                "[识别] {} (lang={}, prob={:.2f}, {:.1f}s)",
                text[:80],
                result.language or "unknown",
                result.language_probability,
                time.time()-t0
            )

            item_id = self._next_translation_item_id()
            trace.item_id = item_id
            self._latency_traces[item_id] = trace
            if self._overlay:
                self._overlay.add_translation_with_id(item_id, text, "...正在翻译")
            self._start_async_translation(item_id, text, result.language, trace)
        except Exception as e:
            self._stats["errors"] += 1
            logger.exception(f"处理失败: {e}")
            self._notify_user("处理失败", str(e), "错误")

    def _setup_hotkeys(self):
        try:
            self._remove_hotkeys()
            hotkeys = self.config.hotkeys
            registrations = (
                ("显示/隐藏", hotkeys.toggle_overlay, self._toggle_overlay),
                ("清空历史", hotkeys.clear_history, self._clear_history),
                ("暂停/恢复", hotkeys.toggle_translation, self._toggle_translation),
                ("锁定/解锁", hotkeys.toggle_lock, self._toggle_lock),
                ("紧凑模式", hotkeys.toggle_compact, self._toggle_compact_mode),
            )
            self._hotkey_handles = []
            active_hotkeys = []
            for label, value, callback in registrations:
                value = str(value or "").strip()
                if not value:
                    continue
                self._hotkey_handles.append(keyboard.add_hotkey(value, callback))
                active_hotkeys.append(f"{label}={value}")
            logger.info(
                "热键已注册: {}",
                ", ".join(active_hotkeys) or "无",
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
            self._sync_tray_state()

    def _clear_history(self):
        if self._overlay:
            logger.info("触发热键: 清空历史")
            self._overlay._signals.clear_history.emit()
            self._notify_user("翻译历史", "已清空", "状态")

    def _toggle_translation(self):
        self._paused = not self._paused
        logger.info(f"翻译{'暂停' if self._paused else '恢复'}")
        if self._overlay:
            self._overlay.set_paused(self._paused)
        self._sync_tray_state()
        self._notify_user("翻译状态", "翻译暂停" if self._paused else "翻译恢复", "状态")

    def _toggle_lock(self):
        if self._overlay:
            logger.info("触发热键: 锁定/解锁浮窗")
            self._overlay._signals.toggle_lock.emit()
            self._sync_tray_state()

    def _toggle_compact_mode(self):
        if self._overlay:
            logger.info("触发热键: 切换紧凑浮窗")
            self._overlay._signals.toggle_compact.emit()
            self._sync_tray_state()

    def _start_qt(self):
        from PyQt5.QtWidgets import QApplication, QMenu, QSystemTrayIcon
        from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, Qt, QTimer
        from PyQt5.QtGui import QIcon
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
        self._qt_app.setApplicationName(APP_NAME)
        self._qt_app.setApplicationDisplayName(APP_NAME)
        icon_path = Path(__file__).parent / "assets" / "voxgo.ico"
        if icon_path.exists():
            self._qt_app.setWindowIcon(QIcon(str(icon_path)))
        self._app_icon = QIcon(str(icon_path)) if icon_path.exists() else QIcon()
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
            config=self.config.overlay,
            hotkeys=self.config.hotkeys,
            audio_config=self.config.audio,
            translation_config=self.config.translation,
            audio_devices=[],
            whisper_config=self.config.whisper,
            app_config=self.config.app,
            debug_config=self.config.debug,
            update_config=self.config.update,
            app_version=APP_VERSION,
            runtime_dir=str(self._runtime_dir()),
            get_last_latency_summary=self._get_last_latency_summary,
            on_settings_changed=self._apply_overlay_settings,
            on_audio_devices_refresh=self._list_audio_devices,
            on_update_check_requested=self._request_update_check,
            on_update_version_ignored=self._ignore_update_version,
            on_shutdown_requested=self._request_shutdown,
            on_overlay_updated=self._on_overlay_updated,
        )
        self._overlay.show()
        self._setup_tray_icon(QSystemTrayIcon, QMenu)
        self._flush_pending_notices()
        QTimer.singleShot(300, self._refresh_overlay_audio_devices)
        QTimer.singleShot(1200, lambda: self._request_update_check(manual=False))
        logger.info("浮窗已启动")

    def _setup_tray_icon(self, tray_cls=None, menu_cls=None):
        if not self._qt_app or self._tray_icon:
            return
        if tray_cls is None or menu_cls is None:
            from PyQt5.QtWidgets import QMenu, QSystemTrayIcon
            tray_cls = QSystemTrayIcon
            menu_cls = QMenu
        if not tray_cls.isSystemTrayAvailable():
            logger.warning("系统托盘不可用，跳过托盘入口")
            return

        self._tray_icon = tray_cls(getattr(self, "_app_icon", None) or self._qt_app.windowIcon(), self._qt_app)
        self._tray_icon.setToolTip(f"{APP_NAME} v{APP_VERSION}")
        self._tray_menu = menu_cls(self._qt_app.activeWindow())

        self._tray_actions = {
            "toggle_overlay": self._tray_menu.addAction("隐藏浮窗"),
            "toggle_translation": self._tray_menu.addAction("暂停翻译"),
            "clear_history": self._tray_menu.addAction("清空字幕"),
            "compact_mode": self._tray_menu.addAction("启用紧凑浮窗"),
        }
        self._tray_menu.addSeparator()
        self._tray_actions["settings"] = self._tray_menu.addAction("设置")
        self._tray_actions["fullscreen_help"] = self._tray_menu.addAction("全屏兼容说明")
        self._tray_menu.addSeparator()
        self._tray_actions["quit"] = self._tray_menu.addAction("退出")

        self._tray_actions["toggle_overlay"].triggered.connect(self._tray_toggle_overlay)
        self._tray_actions["toggle_translation"].triggered.connect(self._toggle_translation)
        self._tray_actions["clear_history"].triggered.connect(self._clear_history)
        self._tray_actions["compact_mode"].triggered.connect(self._tray_toggle_compact_mode)
        self._tray_actions["settings"].triggered.connect(self._tray_open_settings)
        self._tray_actions["fullscreen_help"].triggered.connect(self._tray_show_fullscreen_help)
        self._tray_actions["quit"].triggered.connect(self._request_shutdown)
        self._tray_icon.activated.connect(self._handle_tray_activated)
        self._tray_icon.setContextMenu(self._tray_menu)
        self._sync_tray_state()
        self._tray_icon.show()

    def _sync_tray_state(self):
        if not self._tray_actions:
            return
        if "toggle_overlay" in self._tray_actions and self._overlay:
            self._tray_actions["toggle_overlay"].setText("隐藏浮窗" if self._overlay.isVisible() else "显示浮窗")
        if "toggle_translation" in self._tray_actions:
            self._tray_actions["toggle_translation"].setText("恢复翻译" if self._paused else "暂停翻译")
        if "compact_mode" in self._tray_actions:
            compact = bool(getattr(self.config.overlay, "compact_mode", False))
            self._tray_actions["compact_mode"].setText("退出紧凑浮窗" if compact else "启用紧凑浮窗")
        if self._tray_icon:
            state = "暂停" if self._paused else "运行中"
            self._tray_icon.setToolTip(f"{APP_NAME} v{APP_VERSION} - {state}")

    def _tray_toggle_overlay(self):
        self._toggle_overlay()

    def _tray_toggle_compact_mode(self):
        if self._overlay:
            self._overlay.toggle_compact_mode()
            self.config.overlay = self._overlay.config
        self._save_user_settings()
        self._sync_tray_state()

    def _tray_open_settings(self):
        if self._overlay:
            self._overlay.show()
            self._overlay.raise_()
            self._overlay.show_settings()
        self._sync_tray_state()

    def _tray_show_fullscreen_help(self):
        if self._overlay:
            self._overlay.show()
            self._overlay.raise_()
            self._overlay.show_fullscreen_help()
        self._sync_tray_state()

    def _handle_tray_activated(self, reason):
        try:
            from PyQt5.QtWidgets import QSystemTrayIcon
            if reason == QSystemTrayIcon.Trigger:
                self._tray_toggle_overlay()
        except Exception:
            return

    def _start_backend_after_setup(self):
        self._sync_language_flow()
        self._sync_whisper_vad_limit()
        self.config.app.setup_completed = True
        self._save_user_settings()
        self._refresh_cached_settings()
        self._notify_user(
            "设置已保存",
            "正在后台加载语音识别和翻译服务",
            "状态",
        )
        self._start_backend_thread()

    def _request_shutdown(self):
        logger.info("收到退出按钮请求")
        if self._tray_icon:
            self._tray_icon.hide()
        if self._qt_app:
            self._qt_app.quit()

    def _apply_overlay_settings(
        self,
        overlay_config: OverlayConfig,
        hotkey_config: HotkeyConfig,
        audio_config: AudioConfig,
        translation_config: TranslationConfig,
        whisper_config: WhisperConfig,
        update_config: UpdateSettings,
    ):
        previous_device = self._last_audio_device
        previous_translation = self._last_translation_settings
        previous_whisper_device = self._last_whisper_device
        previous_model_download_source = self._last_model_download_source
        previous_update = (
            bool(getattr(self.config.update, "enabled", True)),
            normalize_update_channel(getattr(self.config.update, "channel", "stable")),
        )
        self.config.overlay = overlay_config
        self.config.hotkeys = hotkey_config
        self.config.translation = translation_config
        self.config.translation.provider = normalize_translation_provider(self.config.translation.provider)
        self.config.update = update_config or self.config.update or UpdateSettings()
        self.config.whisper.device = _normalize_whisper_device(
            getattr(whisper_config, "device", self.config.whisper.device)
        )
        self.config.whisper.model_download_source = normalize_model_download_source(
            getattr(whisper_config, "model_download_source", getattr(self.config.whisper, "model_download_source", "modelscope")),
            getattr(whisper_config, "model_download_endpoint", getattr(self.config.whisper, "model_download_endpoint", "")),
        )
        self.config.whisper.model_download_endpoint = normalize_model_download_endpoint(
            getattr(whisper_config, "model_download_endpoint", getattr(self.config.whisper, "model_download_endpoint", ""))
        )
        self.config.audio.input_device_id = getattr(audio_config, "input_device_id", "")
        self.config.audio.input_device_index = audio_config.input_device_index
        self.config.audio.input_device_name = audio_config.input_device_name
        self.config.audio.latency_mode = normalize_latency_mode(
            getattr(audio_config, "latency_mode", self.config.audio.latency_mode)
        )
        self.config.audio.chunk_duration_ms = getattr(
            audio_config,
            "chunk_duration_ms",
            self.config.audio.chunk_duration_ms,
        )
        self.config.audio.speech_threshold_blocks = getattr(
            audio_config,
            "speech_threshold_blocks",
            self.config.audio.speech_threshold_blocks,
        )
        self.config.audio.silence_limit_blocks = getattr(
            audio_config,
            "silence_limit_blocks",
            self.config.audio.silence_limit_blocks,
        )
        self.config.audio.max_buffer_blocks = getattr(
            audio_config,
            "max_buffer_blocks",
            self.config.audio.max_buffer_blocks,
        )
        self.config.audio.max_speech_seconds = audio_config.max_speech_seconds
        self.config.audio.pre_roll_ms = getattr(
            audio_config,
            "pre_roll_ms",
            self.config.audio.pre_roll_ms,
        )
        self.config.audio.speech_idle_timeout_ms = getattr(
            audio_config,
            "speech_idle_timeout_ms",
            self.config.audio.speech_idle_timeout_ms,
        )
        self.config.audio.min_segment_seconds = getattr(
            audio_config,
            "min_segment_seconds",
            self.config.audio.min_segment_seconds,
        )
        self.config.audio.min_segment_peak_margin_db = getattr(
            audio_config,
            "min_segment_peak_margin_db",
            self.config.audio.min_segment_peak_margin_db,
        )
        self._migrate_runtime_defaults(self.config, preserve_existing_audio_tuning=False)
        previous_language_flow = self._last_language_flow
        current_language_flow = self._sync_language_flow()
        self._sync_whisper_vad_limit()
        if self._speech_recognizer:
            self._speech_recognizer.config = self.config.whisper
        if self._translator:
            self._translator.config = self.config.translation
        self._setup_hotkeys()
        self._save_user_settings()
        current_device = (
            self.config.audio.input_device_id,
            self.config.audio.input_device_index,
            self.config.audio.input_device_name,
            self.config.audio.latency_mode,
            self.config.audio.chunk_duration_ms,
            self.config.audio.speech_threshold_blocks,
            self.config.audio.silence_limit_blocks,
            self.config.audio.max_buffer_blocks,
            self.config.audio.max_speech_seconds,
            self.config.audio.pre_roll_ms,
            self.config.audio.speech_idle_timeout_ms,
        )
        current_translation = (
            normalize_translation_provider(self.config.translation.provider),
            self.config.translation.api_key,
            self.config.translation.model,
            self.config.translation.endpoint,
        )
        current_whisper_device = _normalize_whisper_device(self.config.whisper.device)
        current_model_download_source = (
            normalize_model_download_source(
                getattr(self.config.whisper, "model_download_source", "modelscope"),
                getattr(self.config.whisper, "model_download_endpoint", ""),
            ),
            normalize_model_download_endpoint(
                getattr(self.config.whisper, "model_download_endpoint", "")
            ),
        )
        current_update = (
            bool(getattr(self.config.update, "enabled", True)),
            normalize_update_channel(getattr(self.config.update, "channel", "stable")),
        )
        if self._running and current_device != previous_device:
            self._restart_audio_capture(reuse_noise_gate=current_device[:3] == previous_device[:3])
        if current_language_flow != previous_language_flow:
            if self._translator:
                self._translator.clear_context()
            self._notify_user(
                "语言方向已更新",
                f"{LANGUAGE_NAMES[current_language_flow[0]]} → {LANGUAGE_NAMES[current_language_flow[1]]}",
                "状态",
            )
        if current_translation != previous_translation:
            provider_label = TRANSLATION_PROVIDERS.get(
                normalize_translation_provider(self.config.translation.provider),
                self.config.translation.provider,
            )
            detail = f"服务商: {provider_label}"
            if normalize_translation_provider(self.config.translation.provider) == "google":
                detail += "\n接口: Google Cloud Translation Basic v2"
            else:
                detail += f"\n模型: {self.config.translation.model}\n兼容地址: {self.config.translation.endpoint}"
            self._notify_user(
                "翻译接口已更新",
                detail,
                "状态",
            )
        if current_whisper_device != previous_whisper_device:
            self._notify_user(
                "识别设备已更新",
                f"当前选择: {WHISPER_DEVICE_NAMES[current_whisper_device]}\n重启程序后生效",
                "状态",
            )
        if current_model_download_source != previous_model_download_source:
            self._notify_user(
                "模型下载源已更新",
                f"当前选择: {describe_model_download_source(*current_model_download_source)}\n重启程序后生效",
                "状态",
            )
        if current_update != previous_update:
            self._notify_user(
                "更新检查已更新",
                f"自动检查: {'开启' if current_update[0] else '关闭'}\n通道: {current_update[1]}",
                "状态",
            )
        self._last_audio_device = current_device
        self._last_translation_settings = current_translation
        self._last_language_flow = current_language_flow
        self._last_whisper_device = current_whisper_device
        self._last_model_download_source = current_model_download_source
        self._sync_tray_state()
        logger.info(
            "浮窗设置已应用: opacity={:.2f}, bg_opacity={:.2f}, text_color={}, show_original={}, audio_device={} {}, latency_mode={}, beam_size={}, max_speech={}s, min_segment={:.2f}s, min_peak_margin={:.1f}dB, language={}→{}, whisper_device={}, model_download_source={}, provider={}, model={}, endpoint={}, hotkeys={}/{}/{}/{}/{}",
            overlay_config.opacity,
            overlay_config.bg_opacity,
            overlay_config.text_color,
            overlay_config.show_original,
            self.config.audio.input_device_index,
            self.config.audio.input_device_name,
            self.config.audio.latency_mode,
            self.config.whisper.beam_size,
            self.config.audio.max_speech_seconds,
            self.config.audio.min_segment_seconds,
            self.config.audio.min_segment_peak_margin_db,
            current_language_flow[0],
            current_language_flow[1],
            current_whisper_device,
            describe_model_download_source(*current_model_download_source),
            normalize_translation_provider(self.config.translation.provider),
            self.config.translation.model,
            self.config.translation.endpoint,
            hotkey_config.toggle_overlay,
            hotkey_config.clear_history,
            hotkey_config.toggle_translation,
            hotkey_config.toggle_lock,
            hotkey_config.toggle_compact,
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
            self._speech_recognizer = SpeechRecognizer(
                self.config.whisper,
                self._notify_model_download_progress,
            )
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
            f"{APP_NAME} 启动失败",
            f"程序启动失败，已在程序目录生成 crash_report.txt。\n\n{message}",
        )
        if self._qt_app:
            self._qt_app.quit()

    def _start_audio_capture(self, notice_title: str = "音频捕获已启动", reuse_noise_gate: bool = False):
        previous_noise_gate = None
        if self._audio_capture:
            if reuse_noise_gate and hasattr(self._audio_capture, "current_noise_gate"):
                previous_noise_gate = self._audio_capture.current_noise_gate()
            self._audio_capture.stop()
            self._audio_capture = None
        if previous_noise_gate and previous_noise_gate[2]:
            self.config.audio.initial_noise_floor_dbfs = previous_noise_gate[0]
            self.config.audio.initial_energy_threshold_dbfs = min(
                float(previous_noise_gate[1]),
                SAFE_MAX_SPEECH_THRESHOLD_DBFS,
            )
        else:
            self.config.audio.initial_noise_floor_dbfs = None
            self.config.audio.initial_energy_threshold_dbfs = None
        self._audio_capture = SystemAudioCapture(self.config.audio)
        self._audio_capture.set_speech_callback(self._on_speech_detected)
        self._audio_capture.start()
        self._notify_user(
            notice_title,
            f"{self._describe_selected_audio_device()} -> mono",
            "状态",
        )

    def _restart_audio_capture(self, reuse_noise_gate: bool = False):
        try:
            self._start_audio_capture("音频设置已更新", reuse_noise_gate=reuse_noise_gate)
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

    def _snapshot_update_settings(self) -> UpdateSettings:
        self._migrate_runtime_defaults(self.config)
        return UpdateSettings(
            enabled=bool(getattr(self.config.update, "enabled", True)),
            channel=normalize_update_channel(getattr(self.config.update, "channel", "stable")),
            last_check_at=float(getattr(self.config.update, "last_check_at", 0) or 0),
            ignored_version=str(getattr(self.config.update, "ignored_version", "") or "").strip().lstrip("v"),
            manifest_url=str(getattr(self.config.update, "manifest_url", "") or "").strip(),
        )

    def _request_update_check(self, manual: bool = False):
        if self._stopping:
            return
        settings = self._snapshot_update_settings()
        if not manual and not should_check_for_update(settings):
            logger.info("跳过自动更新检查：尚未到达检查间隔或自动检查已关闭")
            return
        if self._update_check_thread and self._update_check_thread.is_alive():
            logger.info("更新检查正在进行，跳过重复请求")
            if manual and self._overlay:
                self._overlay.set_update_checking(True)
            return
        if manual and self._overlay:
            self._overlay.set_update_checking(True)
        self._update_check_thread = threading.Thread(
            target=self._run_update_check,
            args=(settings, bool(manual)),
            name="update-check",
            daemon=True,
        )
        self._update_check_thread.start()

    def _run_update_check(self, settings: UpdateSettings, manual: bool):
        try:
            result = check_for_update(
                APP_VERSION,
                settings,
                manual=manual,
                user_agent=USER_AGENT,
            )
        except Exception as exc:
            result = UpdateCheckResult("error", message=str(exc))

        self.config.update.last_check_at = float(getattr(result, "checked_at", time.time()) or time.time())
        self._save_user_settings()
        logger.info("更新检查完成: status={}, message={}", result.status, result.message)
        if self._overlay and not self._stopping:
            self._overlay.handle_update_check_result(result, manual)
        if manual and result.status == "error":
            self._notify_user("更新检查失败", result.message, "错误")

    def _ignore_update_version(self, version: str):
        self.config.update.ignored_version = str(version or "").strip().lstrip("v")
        self._save_user_settings()
        logger.info("已忽略更新版本: v{}", self.config.update.ignored_version)

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

    def _start_async_translation(
        self,
        item_id: str,
        text: str,
        detected_language: str = "",
        trace: Optional[LatencyTrace] = None,
    ):
        if self._translation_loop and self._translation_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                self._translate_and_update(item_id, text, detected_language, trace),
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
                    self._translate_and_update(item_id, text, detected_language, trace)
                )
            except Exception as e:
                self._handle_translation_error(item_id, e)

        threading.Thread(target=_run, name="translation-fallback", daemon=True).start()

    async def _translate_and_update(
        self,
        item_id: str,
        text: str,
        detected_language: str = "",
        trace: Optional[LatencyTrace] = None,
    ):
        t0 = time.time()
        trace = trace or self._latency_traces.get(item_id)
        if trace:
            trace.translation_started_at = t0
        translated = await self._translator.translate(text, detected_language)
        if trace:
            trace.translation_finished_at = time.time()
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
            trace = self._latency_traces.get(item_id)
            if trace and not trace.translation_finished_at:
                trace.translation_finished_at = time.time()
            if self._overlay:
                self._overlay.update_translation(item_id, f"[翻译失败] {str(e)[:180]}")

    def _handle_translation_error(self, item_id: str, exc: Exception):
        logger.exception(f"翻译任务失败: {exc}")
        self._stats["errors"] += 1
        trace = self._latency_traces.get(item_id)
        if trace and not trace.translation_finished_at:
            trace.translation_finished_at = time.time()
        if self._overlay:
            self._overlay.update_translation(item_id, f"[翻译失败] {str(exc)[:180]}")

    def _on_overlay_updated(self, item_id: str):
        trace = self._latency_traces.pop(item_id, None)
        if not trace:
            return
        trace.overlay_updated_at = time.time()
        self._last_latency_summary = trace.summary_ms()
        if getattr(self.config.debug, "enabled", False):
            logger.info(
                "[延迟] item={} wait={}ms recognition={}ms translation={}ms overlay={}ms total={}ms",
                item_id,
                self._last_latency_summary.get("wait_ms", 0),
                self._last_latency_summary.get("recognition_ms", 0),
                self._last_latency_summary.get("translation_ms", 0),
                self._last_latency_summary.get("overlay_ms", 0),
                self._last_latency_summary.get("total_ms", 0),
            )

    def _get_last_latency_summary(self) -> dict:
        return dict(self._last_latency_summary or {})

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
        title = f"{APP_NAME} v{APP_VERSION}"
        print("""
╔══════════════════════════════════════════════╗
║{title:^46}║
╠══════════════════════════════════════════════╣
║  热键:                                       ║
║    {toggle_overlay:<14} 切换浮窗显示/隐藏       ║
║    {clear_history:<14} 清空翻译历史            ║
║    {toggle_translation:<14} 暂停/恢复翻译       ║
║    {toggle_lock:<14} 锁定/解锁浮窗            ║
║    {toggle_compact:<14} 切换紧凑模式          ║
╠══════════════════════════════════════════════╣
║  手机端: {url}  ║
╠══════════════════════════════════════════════╣
║  按 Ctrl+C 停止                               ║
╚══════════════════════════════════════════════╝
""".format(
            title=title,
            toggle_overlay=_hotkey_label(hotkeys.toggle_overlay),
            clear_history=_hotkey_label(hotkeys.clear_history),
            toggle_translation=_hotkey_label(hotkeys.toggle_translation),
            toggle_lock=_hotkey_label(hotkeys.toggle_lock),
            toggle_compact=_hotkey_label(hotkeys.toggle_compact),
            url=self._mobile_server.get_mobile_url()
        ))

    def start(self):
        logger.info("正在启动...")
        try:
            self._start_mobile()
            self._start_qt()
            if getattr(self.config.app, "setup_completed", False):
                self._notify_user(
                    "正在启动",
                    "浮窗已显示，正在后台加载语音识别和翻译服务",
                    "状态",
                )
                self._start_backend_thread()
            else:
                self._notify_user(
                    "首次启动",
                    "请先完成翻译接口和音频设备测试",
                    "状态",
                )
                if self._overlay:
                    self._overlay.show_first_run_wizard(self._start_backend_after_setup)

            self._qt_app.exec_()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            self._write_crash_report("启动失败", e)
            logger.exception(f"启动失败: {e}")
            self._notify_user("启动失败", str(e), "错误")
            self._show_error_dialog(
                f"{APP_NAME} 启动失败",
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
        if self._tray_icon:
            self._tray_icon.hide()
        if self._qt_app:
            self._qt_app.quit()

        if sys.stdout is not None:
            print(f"\n翻译统计: 识别 {self._stats['transcriptions']} 条, "
                  f"翻译 {self._stats['translations']} 条, "
                  f"过滤 {self._stats['filtered_speech']} 段, 错误 {self._stats['errors']} 次")
        logger.info("已停止")


def main():
    config_path = None
    default_config = Path(__file__).parent / "config.json"
    if default_config.exists():
        config_path = str(default_config)

    app = VoxGoApp(config_path)
    app.start()


if __name__ == "__main__":
    main()
