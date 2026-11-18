"""Shared configuration values used by persistence and editable UI copies."""
from dataclasses import dataclass
from typing import Optional

from voxgo.i18n import UI_LANGUAGE_ZH


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
    display_mode: str = "classic"
    cinema_font_size: int = 32
    cinema_original_font_size: int = 20
    cinema_text_color: str = "#FFFFFF"
    cinema_original_text_color: str = "#DCE4DF"
    cinema_show_original: bool = True
    cinema_bg_opacity: float = 0.0
    cinema_width: int = 900
    cinema_x: Optional[int] = None
    cinema_bottom: Optional[int] = None


DISPLAY_SETTING_NAMES = tuple(
    name for name in OverlayConfig.__dataclass_fields__
    if name == "display_mode" or name.startswith("cinema_")
)


def normalize_overlay_display(config):
    """Accept old settings and bound new presentation values before Qt sees them."""
    import math
    import re

    defaults = OverlayConfig()
    if config.display_mode not in ("classic", "cinema"):
        config.display_mode = "classic"
    for name, low, high in (("cinema_font_size", 18, 64), ("cinema_original_font_size", 10, 40),
                            ("cinema_width", 320, 2400), ("cinema_bg_opacity", 0, 0.8)):
        try:
            value = float(getattr(config, name))
            if not math.isfinite(value):
                raise ValueError(name)
            value = max(low, min(high, value))
            setattr(config, name, value if name == "cinema_bg_opacity" else int(value))
        except (ValueError, TypeError, OverflowError):
            setattr(config, name, getattr(defaults, name))
    for name in ("cinema_x", "cinema_bottom"):
        try:
            value = getattr(config, name)
            setattr(config, name, int(value) if value is not None and abs(float(value)) < 1000000 else None)
        except (ValueError, TypeError, OverflowError):
            setattr(config, name, None)
    for name in ("cinema_text_color", "cinema_original_text_color"):
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(getattr(config, name))):
            setattr(config, name, getattr(defaults, name))
    config.cinema_show_original = bool(config.cinema_show_original)


@dataclass
class HotkeyConfig:
    toggle_overlay: str = "ctrl+shift+t"
    toggle_translation: str = "ctrl+alt+s"
    clear_history: str = "ctrl+alt+c"
    toggle_lock: str = ""
    toggle_compact: str = ""
    toggle_display_mode: str = "ctrl+alt+m"


@dataclass
class RuntimeConfig:
    setup_completed: bool = False
    first_subtitle_at: str = ""
    first_translation_at: str = ""
    subtitle_check_completed: bool = False
    community_invitation_seen: bool = False
    community_invitation_dismissed: bool = False
    language: str = UI_LANGUAGE_ZH
    close_action: str = "ask"
    close_action_remember: bool = False
    telemetry_consent: str = 'unknown'
    telemetry_consent_version: int = 0
    telemetry_epoch: str = ''
    basic_install_seed: str = ''
    basic_first_run_date: str = ''
    telemetry_v2_migrated: bool = False
    telemetry_install_origin: str = 'historical_install'
    full_telemetry_source: str = 'migration_unknown'


@dataclass
class DebugConfig:
    enabled: bool = False
    log_level: str = "INFO"
    save_audio_chunks: bool = False
    save_transcripts: bool = False
    save_failed_audio: bool = False
    save_dropped_audio: bool = False
    save_empty_asr_audio: bool = False
    save_low_confidence_audio: bool = False
    diagnostics_audio_dir: str = "diagnostics/audio"
