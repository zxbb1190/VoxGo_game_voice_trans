import json
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import aiohttp


@dataclass
class TranslationConfig:
    provider: str = "openai_compatible"
    api_key: str = ""
    model: str = "tencent/Hunyuan-MT-7B"
    endpoint: str = "https://api.siliconflow.cn/v1/chat/completions"
    max_tokens: int = 80
    temperature: float = 0.0
    source_lang: str = "en"
    target_lang: str = "zh"
    context_messages: int = 0
    timeout_seconds: float = 12.0
    max_concurrent_requests: int = 2
    skip_language_mismatch: bool = True
    language_gate_min_probability: float = 0.60
    language_gate_short_text_min_probability: float = 0.85
    language_gate_short_text_chars: int = 6
    enable_local_phrase_cache: bool = True
    local_phrase_cache: dict = None


@dataclass
class TranslationRequest:
    text: str
    source_lang: str
    target_lang: str
    detected_language: str = ""


@dataclass
class TranslationResult:
    translated: str
    source_lang: str
    target_lang: str
    provider: str
    elapsed_seconds: float = 0.0
    raw: Optional[dict] = None


@dataclass
class ProviderTestResult:
    ok: bool
    message: str
    elapsed_ms: int = 0


TRANSLATION_PROVIDERS = {
    "openai_compatible": "OpenAI 兼容",
    "google": "Google Cloud Translation",
}
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
OPPOSITE_LANGUAGE = {"en": "zh", "zh": "en"}
ZH_RE = re.compile(r"[\u4e00-\u9fff]")
LATIN_RE = re.compile(r"[A-Za-z]")
PLACEHOLDER_API_KEYS = {
    "",
    "YOUR_API_KEY",
    "YOUR_SILICONFLOW_API_KEY",
    "YOUR_OPENAI_COMPATIBLE_API_KEY",
    "YOUR_GOOGLE_TRANSLATE_API_KEY",
    "YOUR_GOOGLE_CLOUD_TRANSLATION_API_KEY",
}
LOCAL_ENDPOINT_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
PHRASE_NORMALIZE_RE = re.compile(r"[\W_]+", re.UNICODE)
DEFAULT_LOCAL_PHRASE_CACHE = {
    "en:zh": {
        "go": "走",
        "go go": "快走",
        "push": "压上",
        "push now": "现在压上",
        "run": "跑",
        "help": "救我",
        "cover me": "掩护我",
        "enemy": "敌人",
        "enemy spotted": "发现敌人",
        "need healing": "我需要治疗",
        "i need healing": "我需要治疗",
        "reload": "换弹",
        "reloading": "换弹中",
        "fall back": "撤退",
        "retreat": "撤退",
        "behind us": "在我们后面",
        "on me": "在我这里",
        "wait": "等一下",
        "now": "现在",
        "left": "左边",
        "right": "右边",
        "mid": "中路",
        "nice try": "打得不错",
        "good game": "打得好",
        "gg": "打得好",
    },
    "zh:en": {
        "撤退": "Fall back",
        "快走": "Go go",
        "走": "Go",
        "压上": "Push",
        "救我": "Help me",
        "掩护我": "Cover me",
        "敌人": "Enemy",
        "发现敌人": "Enemy spotted",
        "我需要治疗": "I need healing",
        "治疗": "Healing",
        "换弹": "Reloading",
        "换弹中": "Reloading",
        "左边": "Left",
        "右边": "Right",
        "中路": "Mid",
        "等一下": "Wait",
        "现在": "Now",
    },
}


def normalize_translation_provider(value: str, default: str = "openai_compatible") -> str:
    value = (value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "openai": "openai_compatible",
        "openai_compat": "openai_compatible",
        "compatible": "openai_compatible",
        "chat_completions": "openai_compatible",
        "siliconflow": "openai_compatible",
        "google_translate": "google",
        "google_translation": "google",
        "google_cloud": "google",
        "google_cloud_translation": "google",
        "cloud_translation": "google",
    }
    value = aliases.get(value, value)
    return value if value in TRANSLATION_PROVIDERS else default


def normalize_language_code(value: str, default: str = "") -> str:
    value = (value or "").strip().lower()
    normalized = LANGUAGE_ALIASES.get(value, value)
    return normalized if normalized in OPPOSITE_LANGUAGE else default


def detect_language(text: str, configured_source_lang: str = "", detected_language: str = "") -> str:
    configured = normalize_language_code(configured_source_lang)
    if configured:
        return configured
    lang = (detected_language or "").lower()
    if lang in ("zh", "zh-cn", "zh-tw", "chinese", "cmn", "yue"):
        return "zh"
    if lang in ("en", "eng", "english"):
        return "en"
    zh_count = len(ZH_RE.findall(text or ""))
    return "zh" if zh_count >= max(1, len(text.strip()) // 5) else "en"


def target_language(configured_target_lang: str, source_language: str) -> str:
    configured = normalize_language_code(configured_target_lang)
    if configured and configured != source_language:
        return configured
    return OPPOSITE_LANGUAGE.get(source_language, "zh")


def local_phrase_cache_lookup(text: str, source_lang: str, target_lang: str, config: TranslationConfig = None) -> str:
    config = config or TranslationConfig()
    if not bool(getattr(config, "enable_local_phrase_cache", True)):
        return ""
    source = normalize_language_code(source_lang)
    target = normalize_language_code(target_lang)
    if not source or not target or source == target:
        return ""
    cache = _merged_phrase_cache(getattr(config, "local_phrase_cache", None))
    phrases = cache.get(f"{source}:{target}", {})
    if not phrases:
        return ""
    key = _normalize_phrase_key(text, source)
    if not key:
        return ""
    return phrases.get(key, "")


def _merged_phrase_cache(custom_cache) -> dict:
    merged = {
        direction: dict(phrases)
        for direction, phrases in DEFAULT_LOCAL_PHRASE_CACHE.items()
    }
    if isinstance(custom_cache, dict):
        for direction, phrases in custom_cache.items():
            if not isinstance(phrases, dict):
                continue
            bucket = merged.setdefault(str(direction), {})
            for source, target in phrases.items():
                source_key = _normalize_phrase_key(str(source), direction.split(":", 1)[0])
                if source_key:
                    bucket[source_key] = str(target)
    return merged


def _normalize_phrase_key(text: str, source_lang: str = "") -> str:
    value = clean_translation_output(text)
    if not value:
        return ""
    if normalize_language_code(source_lang) == "en":
        value = value.casefold()
        value = PHRASE_NORMALIZE_RE.sub(" ", value)
        return " ".join(value.split())
    return "".join(value.split())


def should_skip_translation_for_language(
    text: str,
    configured_source_lang: str = "",
    detected_language: str = "",
    language_probability: float = 0.0,
    config: TranslationConfig = None,
) -> str:
    config = config or TranslationConfig()
    if not bool(getattr(config, "skip_language_mismatch", True)):
        return ""

    expected = normalize_language_code(configured_source_lang)
    if not expected:
        return ""

    detected = normalize_language_code(detected_language)
    try:
        probability = float(language_probability or 0.0)
    except Exception:
        probability = 0.0

    text = text or ""
    compact_len = len(text.strip())
    try:
        short_chars = max(0, int(getattr(config, "language_gate_short_text_chars", 6) or 0))
    except Exception:
        short_chars = 6
    try:
        min_probability = float(getattr(config, "language_gate_min_probability", 0.60) or 0.0)
    except Exception:
        min_probability = 0.60
    try:
        short_min_probability = float(
            getattr(config, "language_gate_short_text_min_probability", 0.85) or min_probability
        )
    except Exception:
        short_min_probability = 0.85

    threshold = short_min_probability if short_chars and compact_len <= short_chars else min_probability
    threshold = max(0.0, min(1.0, threshold))
    if detected and detected != expected and probability >= threshold:
        return f"language_mismatch:{detected}->{expected}:prob={probability:.2f}:threshold={threshold:.2f}"

    zh_count = len(ZH_RE.findall(text))
    latin_count = len(LATIN_RE.findall(text))
    if expected == "en" and zh_count > 0 and (zh_count >= latin_count or zh_count >= 2):
        return f"text_script_mismatch:zh->{expected}:zh={zh_count}:latin={latin_count}"
    if expected == "zh" and zh_count == 0 and latin_count >= 3:
        return f"text_script_mismatch:en->{expected}:latin={latin_count}"

    return ""


def is_placeholder_api_key(api_key: str) -> bool:
    return (api_key or "").strip() in PLACEHOLDER_API_KEYS


def normalized_chat_endpoint(endpoint: str) -> str:
    endpoint = (endpoint or "").strip().rstrip("/")
    if not endpoint:
        endpoint = TranslationConfig.endpoint.rstrip("/")
    if endpoint.endswith("/chat/completions"):
        return endpoint
    return f"{endpoint}/chat/completions"


def endpoint_requires_api_key(endpoint: str) -> bool:
    host = (urlparse(normalized_chat_endpoint(endpoint)).hostname or "").lower()
    return host not in LOCAL_ENDPOINT_HOSTS


def short_error_text(error_text: str) -> str:
    text = (error_text or "").strip()
    if not text:
        return ""
    try:
        data = json.loads(text)
        error = data.get("error") if isinstance(data, dict) else None
        if isinstance(error, dict):
            parts = [
                str(error.get("code") or "").strip(),
                str(error.get("message") or "").strip(),
            ]
            text = " ".join(part for part in parts if part)
        elif isinstance(data, dict):
            parts = [
                str(data.get("code") or "").strip(),
                str(data.get("message") or data.get("detail") or "").strip(),
            ]
            text = " ".join(part for part in parts if part)
    except Exception:
        pass
    text = " ".join(text.split())
    return text[:220]


def clean_translation_output(text: str) -> str:
    """Normalize provider output before displaying it."""
    cleaned = str(text or "")
    target_match = re.search(
        r"<\s*target_text\s*>(.*?)</\s*target_text\s*>",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if target_match:
        cleaned = target_match.group(1)
    cleaned = re.sub(r"</?\s*(?:source_text|target_text)\s*>", "", cleaned, flags=re.IGNORECASE)
    cleaned = " ".join(cleaned.split())
    return cleaned.strip()


class TranslatorProvider:
    name = ""

    def __init__(self, config: TranslationConfig):
        self.config = config

    async def test(self) -> ProviderTestResult:
        raise NotImplementedError

    async def translate(self, request: TranslationRequest, session: aiohttp.ClientSession) -> TranslationResult:
        raise NotImplementedError

    def missing_api_key_message(self) -> str:
        return "[未翻译] API Key 未配置，请在设置里填写 OpenAI 兼容 API Key"

    def requires_api_key(self) -> bool:
        return True

