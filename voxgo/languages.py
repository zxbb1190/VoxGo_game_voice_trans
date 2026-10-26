"""Language and direction capabilities shared by configuration, UI and runtime.

These are routing capabilities, not language quality or release acceptance.
"""

SPEECH_LANGUAGE_CODES = ("en", "zh", "ja", "ko", "ru")
LANGUAGE_NAMES = {"en": "英语", "zh": "中文", "ja": "日语", "ko": "韩语", "ru": "俄语"}
LANGUAGE_ALIASES = {
    "eng": "en", "english": "en", "英语": "en",
    "zh-cn": "zh", "zh-tw": "zh", "cmn": "zh", "yue": "zh", "chinese": "zh", "中文": "zh",
    "jpn": "ja", "japanese": "ja", "日语": "ja",
    "kor": "ko", "korean": "ko", "韩语": "ko",
    "rus": "ru", "russian": "ru", "俄语": "ru",
}
OPPOSITE_LANGUAGE = {"en": "zh", "zh": "en"}  # Legacy bidirectional flow only.
DEFAULT_TARGET_LANGUAGE = {**OPPOSITE_LANGUAGE, "ja": "zh", "ko": "zh", "ru": "zh"}
LOCAL_DIRECTIONS = frozenset(OPPOSITE_LANGUAGE.items())
NEW_SPEECH_LANGUAGES = ("ja", "ko", "ru")
ONLINE_DIRECTIONS = frozenset({
    *LOCAL_DIRECTIONS,
    *((source, target) for source in NEW_SPEECH_LANGUAGES for target in ("zh", "en")),
    *((source, target) for source in ("zh", "en") for target in NEW_SPEECH_LANGUAGES),
})


def normalize_language_code(value: str, default: str = "") -> str:
    value = str(value or "").strip().lower()
    value = LANGUAGE_ALIASES.get(value, value)
    return value if value in SPEECH_LANGUAGE_CODES else default


def normalize_language_flow(source: str, target: str):
    """Preserve unsupported explicit settings for validation, never guess a route.

    Missing settings and same-language legacy EN/ZH settings retain the old
    migration behavior. New explicit unsupported pairs remain blocked.
    """
    source = normalize_language_code(source, str(source or "en").strip().lower())
    target = normalize_language_code(target, str(target or DEFAULT_TARGET_LANGUAGE.get(source, "")).strip().lower())
    if target == source and source in OPPOSITE_LANGUAGE:
        target = OPPOSITE_LANGUAGE[source]
    return source, target


def translation_direction_error(provider: str, source: str, target: str) -> str:
    directions = LOCAL_DIRECTIONS if provider == "local" else ONLINE_DIRECTIONS
    if provider not in {"local", "google", "openai_compatible"} or (source, target) not in directions:
        if provider == "local":
            return "[未翻译] 离线翻译仅支持英语 ↔ 中文；日/韩/俄相关方向需自行选择在线服务并配置 API Key。Offline supports English ↔ Chinese only."
        return "[未翻译] 不支持此语言方向。Supported: English ↔ Chinese; Japanese/Korean/Russian ↔ English/Chinese."
    return ""


def whisper_model_error(model: str, source: str) -> str:
    import re
    if source != "en" and re.search(r"(?:^|[/\\-])(?:tiny|base|small|medium)\.en(?:$|[/\\])", str(model).lower()):
        return "[未识别] 此语言需要多语言 Whisper 模型，不能使用 .en 英语专用模型。Select a multilingual Whisper model for this language."
    return ""
