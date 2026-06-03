"""
翻译模块
使用 OpenAI 兼容 Chat Completions API 进行中英文双向翻译
"""

import asyncio
import json
import re
import time
from dataclasses import dataclass
from urllib.parse import urlparse
from typing import Optional, List

import aiohttp
from loguru import logger


@dataclass
class TranslationConfig:
    api_key: str = ""
    model: str = "tencent/Hunyuan-MT-7B"
    endpoint: str = "https://api.siliconflow.cn/v1/chat/completions"
    max_tokens: int = 80
    temperature: float = 0.0
    source_lang: str = "en"
    target_lang: str = "zh"
    context_messages: int = 0
    timeout_seconds: float = 8.0


SYSTEM_PROMPT = """你是实时语音字幕翻译器。输入来自语音识别，可能有错字、断句和不完整内容。

翻译规则：
1. 只翻译用户消息中 <source_text> 和 </source_text> 之间的文本，不要翻译标签本身。
2. 只做忠实翻译，不补全没听到的内容。
3. 不要扩写，不要解释，不要润色成完整句。
4. 如果原文明显不完整，保留不完整感。
5. 如果某个词无法确定，用“（听不清）”或保留原词。
6. 术语、地图点位、技能名、人名、枪械名、品牌名、产品名、应用名、文件格式和缩写优先保留英文，例如 Speechify、Discord、Steam、PDFs、Google Docs、OpenAI、GG、FPS。
7. 如果原文是中文，翻译成英文；如果原文是英文，翻译成中文。
8. 只输出译文，不输出解释、说明、标签或思考过程。
"""

ZH_RE = re.compile(r"[\u4e00-\u9fff]")
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


def normalize_language_code(value: str, default: str = "") -> str:
    value = (value or "").strip().lower()
    return LANGUAGE_ALIASES.get(value, value) if LANGUAGE_ALIASES.get(value, value) in OPPOSITE_LANGUAGE else default


class GameTranslator:
    """游戏语音翻译器"""

    def __init__(self, config: TranslationConfig = None):
        self.config = config or TranslationConfig()
        self._context: List[dict] = []
        self._session: Optional[aiohttp.ClientSession] = None
        self._translation_count = 0
        self._total_time = 0

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            )
        return self._session

    def detect_language(self, text: str, detected_language: str = "") -> str:
        """Normalize language to zh/en for bidirectional translation."""
        configured = normalize_language_code(self.config.source_lang)
        if configured:
            return configured
        lang = (detected_language or "").lower()
        if lang in ("zh", "zh-cn", "zh-tw", "chinese", "cmn", "yue"):
            return "zh"
        if lang in ("en", "eng", "english"):
            return "en"
        zh_count = len(ZH_RE.findall(text or ""))
        return "zh" if zh_count >= max(1, len(text.strip()) // 5) else "en"

    def get_target_language(self, source_language: str) -> str:
        configured = normalize_language_code(self.config.target_lang)
        if configured and configured != source_language:
            return configured
        return OPPOSITE_LANGUAGE.get(source_language, "zh")

    def _language_name(self, language: str) -> str:
        return "英文" if language == "en" else "中文"

    def _normalized_endpoint(self) -> str:
        endpoint = (self.config.endpoint or "").strip().rstrip("/")
        if not endpoint:
            endpoint = TranslationConfig.endpoint.rstrip("/")
        if endpoint.endswith("/chat/completions"):
            return endpoint
        return f"{endpoint}/chat/completions"

    def _is_placeholder_api_key(self) -> bool:
        key = (self.config.api_key or "").strip()
        return key in {
            "",
            "YOUR_API_KEY",
            "YOUR_SILICONFLOW_API_KEY",
            "YOUR_OPENAI_COMPATIBLE_API_KEY",
        }

    def _requires_api_key(self) -> bool:
        host = (urlparse(self._normalized_endpoint()).hostname or "").lower()
        return host not in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}

    def _short_error_text(self, error_text: str) -> str:
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

    async def translate(self, text: str, detected_language: str = "") -> str:
        """按配置的固定语言方向翻译。"""
        if not text or not text.strip():
            return ""

        if self._is_placeholder_api_key() and self._requires_api_key():
            logger.warning("API Key 未配置，返回原文")
            return "[未翻译] API Key 未配置，请在设置里填写 OpenAI 兼容 API Key"

        source_language = self.detect_language(text, detected_language)
        target_language = self.get_target_language(source_language)
        current_message = {
            "role": "user",
            "content": (
                f"请将 <source_text> 中的{self._language_name(source_language)}"
                f"翻译成{self._language_name(target_language)}，只输出译文。\n"
                f"<source_text>{text}</source_text>"
            )
        }

        # 实时字幕更看重低延迟，context_messages=0 时完全不带历史。
        max_ctx = max(0, self.config.context_messages * 2)
        if max_ctx and len(self._context) > max_ctx:
            self._context = self._context[-max_ctx:]

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *(self._context if max_ctx else []),
            current_message
        ]

        headers = {"Content-Type": "application/json"}
        if not self._is_placeholder_api_key():
            headers["Authorization"] = f"Bearer {self.config.api_key.strip()}"

        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": False
        }

        start_time = time.time()

        try:
            session = await self._get_session()

            async with session.post(
                self._normalized_endpoint(),
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    choice = data["choices"][0]
                    message = choice.get("message") or {}
                    translation = (message.get("content") or "").strip()
                    reasoning = (message.get("reasoning_content") or "").strip()
                    elapsed = time.time() - start_time
                    self._translation_count += 1
                    self._total_time += elapsed
                    if not translation:
                        finish_reason = choice.get("finish_reason")
                        logger.warning(
                            "翻译 API 返回空 content: "
                            f"finish_reason={finish_reason}, reasoning_len={len(reasoning)}"
                        )
                        if reasoning:
                            logger.debug(f"reasoning_content 预览: {reasoning[:200]}")
                    else:
                        if max_ctx:
                            self._context.extend([
                                current_message,
                                {"role": "assistant", "content": translation}
                            ])
                            if len(self._context) > max_ctx:
                                self._context = self._context[-max_ctx:]
                    direction = f"{source_language}->{target_language}"
                    logger.info(f"翻译({direction}): {text[:50]}... → {translation[:50]}... ({elapsed:.2f}s)")
                    return translation
                else:
                    error_text = await response.text()
                    logger.error(f"翻译 API 错误: {response.status} - {error_text}")
                    detail = self._short_error_text(error_text)
                    if detail:
                        return f"[翻译错误 {response.status}] {detail}"
                    return f"[翻译错误 {response.status}] API 服务商返回错误"

        except asyncio.TimeoutError:
            logger.error("翻译 API 超时")
            return f"[翻译超时] API 请求超过 {self.config.timeout_seconds:g} 秒，请检查网络或服务商状态"
        except Exception as e:
            logger.error(f"翻译异常: {e}")
            return f"[翻译失败] {str(e)[:180]}"

    async def translate_batch(self, texts: List[str]) -> List[str]:
        """批量翻译"""
        tasks = [self.translate(text) for text in texts]
        return await asyncio.gather(*tasks)

    async def translate_streaming(self, text: str):
        """流式翻译（暂未实现流式，先降级为等待完整结果）"""
        result = await self.translate(text)
        yield result

    def get_stats(self) -> dict:
        """获取翻译统计"""
        avg_time = self._total_time / self._translation_count if self._translation_count > 0 else 0
        return {
            "total_translations": self._translation_count,
            "average_time": round(avg_time, 3),
            "total_time": round(self._total_time, 2)
        }

    def clear_context(self):
        """清除翻译上下文"""
        self._context.clear()

    async def close(self):
        """关闭 HTTP 会话"""
        if self._session and not self._session.closed:
            await self._session.close()
