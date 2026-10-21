import asyncio
import time

from loguru import logger

from .base import (
    ProviderTestResult,
    TranslationConfig,
    TranslationRequest,
    TranslationResult,
    TranslatorProvider,
    endpoint_requires_api_key,
    is_placeholder_api_key,
    normalized_chat_endpoint,
    short_error_text,
)
from .prompt import translation_system_prompt
from voxgo.languages import translation_direction_error
from .failures import classify_api_failure


class OpenAICompatibleProvider(TranslatorProvider):
    name = "openai_compatible"

    def __init__(self, config: TranslationConfig):
        super().__init__(config)
        self._context = []
        self._contexts = {}
        self._context_generation = 0

    async def test(self) -> ProviderTestResult:
        return ProviderTestResult(ok=True, message="Provider is configured")

    def requires_api_key(self) -> bool:
        return endpoint_requires_api_key(self.config.endpoint)

    def _language_name(self, language: str) -> str:
        return {"en": "英文", "zh": "中文", "ja": "日文", "ko": "韩文", "ru": "俄文"}[language]

    async def translate(self, request: TranslationRequest, session) -> TranslationResult:
        error = translation_direction_error(self.name, request.source_lang, request.target_lang)
        if error:
            return TranslationResult(error, request.source_lang, request.target_lang, self.name)
        pair = (request.source_lang, request.target_lang)
        generation = self._context_generation
        context = self._contexts.setdefault(pair, [])
        current_message = {
            "role": "user",
            "content": (
                f"请将 <source_text> 中的{self._language_name(request.source_lang)}"
                f"翻译成{self._language_name(request.target_lang)}，只输出译文。\n"
                f"<source_text>{request.text}</source_text>"
            ),
        }

        max_ctx = max(0, self.config.context_messages * 2)
        if max_ctx and len(context) > max_ctx:
            del context[:-max_ctx]

        messages = [
            {"role": "system", "content": translation_system_prompt(*pair)},
            *(context if max_ctx else []),
            current_message,
        ]
        headers = {"Content-Type": "application/json"}
        if not is_placeholder_api_key(self.config.api_key):
            headers["Authorization"] = f"Bearer {self.config.api_key.strip()}"

        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": False,
        }
        start_time = time.time()

        try:
            async with session.post(
                normalized_chat_endpoint(self.config.endpoint),
                headers=headers,
                json=payload,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    choice = data["choices"][0]
                    message = choice.get("message") or {}
                    translation = (message.get("content") or "").strip()
                    reasoning = (message.get("reasoning_content") or "").strip()
                    elapsed = time.time() - start_time
                    if not translation:
                        finish_reason = choice.get("finish_reason")
                        logger.warning(
                            "翻译 API 返回空 content: finish_reason={}, reasoning_len={}",
                            finish_reason,
                            len(reasoning),
                        )
                        if reasoning:
                            logger.debug(f"reasoning_content 预览: {reasoning[:200]}")
                    elif max_ctx and generation == self._context_generation:
                        context.extend([current_message, {"role": "assistant", "content": translation}])
                        if len(context) > max_ctx:
                            del context[:-max_ctx]
                    direction = f"{request.source_lang}->{request.target_lang}"
                    logger.info(f"翻译({direction}): {request.text[:50]}... → {translation[:50]}... ({elapsed:.2f}s)")
                    return TranslationResult(
                        translated=translation,
                        source_lang=request.source_lang,
                        target_lang=request.target_lang,
                        provider=self.name,
                        elapsed_seconds=elapsed,
                        raw=data,
                        failure_reason='' if translation else 'empty_result',
                    )

                error_text = await response.text()
                logger.error(f"翻译 API 错误: {response.status} - {error_text}")
                detail = short_error_text(error_text)
                if detail:
                    translated = f"[翻译错误 {response.status}] {detail}"
                else:
                    translated = f"[翻译错误 {response.status}] API 服务商返回错误"
                return TranslationResult(translated, request.source_lang, request.target_lang, self.name,
                                         failure_reason=classify_api_failure(status=response.status))

        except asyncio.TimeoutError:
            logger.error("翻译 API 超时")
            return TranslationResult(
                f"[翻译超时] API 请求超过 {self.config.timeout_seconds:g} 秒，请检查网络或服务商状态",
                request.source_lang,
                request.target_lang,
                self.name,
                failure_reason='timeout',
            )
        except Exception as e:
            logger.error(f"翻译异常: {e}")
            return TranslationResult(f"[翻译失败] {str(e)[:180]}", request.source_lang, request.target_lang, self.name,
                                     failure_reason=classify_api_failure(e))

    def clear_context(self):
        self._context.clear()
        self._contexts.clear()
        self._context_generation += 1

