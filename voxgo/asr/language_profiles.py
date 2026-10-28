"""Source-specific speech runtime views; persisted legacy settings stay intact."""
from dataclasses import dataclass, fields, replace

from voxgo.audio.capture import AudioConfig, normalize_latency_mode
from voxgo.asr.whisper_engine import DEFAULT_VAD_PARAMS
from voxgo.languages import ONLINE_DIRECTIONS

LANGUAGE_AWARE = "language_aware"
LEGACY = "legacy"


@dataclass
class LanguageAudioConfig(AudioConfig):
    # Internal event-time metadata, not a new telemetry field or a new preset.
    diagnostics_latency_mode: str = "custom"
    speech_strategy: str = ""


def normalize_multilingual_strategy(value):
    return LANGUAGE_AWARE if str(value or "").strip().lower() == LANGUAGE_AWARE else LEGACY


def effective_speech_config(config, *, experimental=False):
    """Resolve a fresh runtime view, never overwrite user/English/Chinese tuning.

    The client always uses the compatibility policy, including old candidate
    settings. Only research tools may explicitly opt into historical
    profiles; this keyword is not a persisted setting or a product UI option.
    Fast/Balanced/Accurate and explicit Custom tuning remain unchanged.
    """
    if not experimental:
        return config
    source = config.translation.source_lang
    if (source not in {"ja", "ko", "ru"} or (source, config.translation.target_lang) not in ONLINE_DIRECTIONS
            or config.translation.provider not in {"google", "openai_compatible"}
            or normalize_latency_mode(config.audio.latency_mode) != "fast"
            or getattr(config.whisper, "asr_impact_mode", "low") == "ultra_low"
            or normalize_multilingual_strategy(getattr(config.whisper, "multilingual_asr_strategy", LEGACY)) == LEGACY):
        return config
    audio = LanguageAudioConfig(**{field.name: getattr(config.audio, field.name) for field in fields(AudioConfig)},
                                speech_strategy=source + "_speech_v1")
    audio.max_speech_seconds = 4.5
    audio.pre_roll_ms = 450
    audio.speech_idle_timeout_ms = 450
    whisper = replace(config.whisper)
    whisper.vad_parameters = dict(DEFAULT_VAD_PARAMS if config.whisper.vad_parameters is None else config.whisper.vad_parameters)
    whisper.vad_parameters["max_speech_duration_s"] = audio.max_speech_seconds
    # Only replace the built-in Fast base choice, not an explicitly selected
    # custom/English-only model. The latter still gets its capability error.
    selected = str(whisper.active_model_size or whisper.model_size)
    if source == "ko" and selected == "base" and whisper.model_size == "small":
        whisper.active_model_size = "small"
    whisper.beam_size = 3 if source == "ja" else 1
    if whisper.device == "cpu":
        whisper.cpu_threads = max(2, int(whisper.cpu_threads or 1))
        whisper.auto_cpu_threads = False
    return replace(config, audio=audio, whisper=whisper)


def audio_runtime_signature(config):
    audio = effective_speech_config(config).audio
    return tuple(getattr(audio, name) for name in (
        "input_device_id", "input_device_index", "input_device_name", "latency_mode",
        "chunk_duration_ms", "speech_threshold_blocks", "silence_limit_blocks",
        "max_buffer_blocks", "max_speech_seconds", "pre_roll_ms", "speech_idle_timeout_ms",
    )) + (getattr(audio, "diagnostics_latency_mode", ""),)
