from dataclasses import dataclass
from voxgo.config.models import (
    OverlayConfig as OverlayConfig,
    HotkeyConfig as HotkeyConfig,
    RuntimeConfig as RuntimeConfig,
    DebugConfig as DebugConfig,
)

from voxgo.audio.capture import AudioConfig
from voxgo.i18n import UI_LANGUAGE_ZH, normalize_ui_language
from voxgo.mobile.server import WebSocketConfig
from voxgo.asr.whisper_engine import WhisperConfig
from voxgo.translation import TranslationConfig
from voxgo.update.checker import UpdateSettings
from voxgo.languages import LANGUAGE_ALIASES as LANGUAGE_ALIASES, LANGUAGE_NAMES as LANGUAGE_NAMES, OPPOSITE_LANGUAGE as OPPOSITE_LANGUAGE
from voxgo.languages import normalize_language_code as _normalize_language_code


WHISPER_DEVICE_NAMES = {
    "auto": "自动检测（GPU 优先）",
    "cuda": "NVIDIA GPU / CUDA",
    "cpu": "CPU",
}


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


def normalize_language_code(value: str, default: str = "en") -> str:
    return _normalize_language_code(value, default)


def normalize_whisper_device(value: str) -> str:
    value = (value or "").strip().lower()
    aliases = {
        "gpu": "cuda",
        "nvidia": "cuda",
        "nvidia gpu": "cuda",
        "自动": "auto",
        "自动检测": "auto",
    }
    value = aliases.get(value, value)
    return value if value in WHISPER_DEVICE_NAMES else "auto"


def ui_language_of(config) -> str:
    return normalize_ui_language(getattr(getattr(config, "app", None), "language", UI_LANGUAGE_ZH))
