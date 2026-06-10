import asyncio
import threading
import time
from typing import Optional

from loguru import logger

from voxgo.runtime.events import TranslationReady
from voxgo.runtime.work_items import LatencyTrace
from voxgo.translation import (
    GameTranslator,
    TranslationConfig,
    clean_translation_output,
    should_skip_translation_for_language,
)


class TranslationRuntime:
    def __init__(self, event_bus, stats, latency_traces, overlay_getter):
        self._event_bus = event_bus
        self._stats = stats
        self._latency_traces = latency_traces
        self._overlay_getter = overlay_getter
        self._language_revision_getter = lambda: 0
        self.client: Optional[GameTranslator] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None

    def initialize(self, config: TranslationConfig):
        self.client = GameTranslator(config)
        self.start_loop()

    def update_config(self, config: TranslationConfig):
        if self.client:
            self.client.config = config

    def clear_context(self):
        if self.client:
            self.client.clear_context()

    def set_language_revision_getter(self, getter):
        self._language_revision_getter = getter or (lambda: 0)

    def start_loop(self):
        if self.loop and self.loop.is_running():
            return

        def _run():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        self.thread = threading.Thread(target=_run, daemon=True)
        self.thread.start()
        while not self.loop or not self.loop.is_running():
            time.sleep(0.01)
        logger.info("翻译事件循环已启动")

    def translate_async(
        self,
        item_id: str,
        text: str,
        detected_language: str = "",
        language_probability: float = 0.0,
        source_lang: str = "",
        target_lang: str = "",
        language_revision: int = 0,
        trace: Optional[LatencyTrace] = None,
    ):
        if isinstance(language_probability, LatencyTrace) and trace is None:
            trace = language_probability
            language_probability = 0.0
        if isinstance(source_lang, LatencyTrace) and trace is None:
            trace = source_lang
            source_lang = ""
            target_lang = ""
            language_revision = 0
        if self.loop and self.loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                self._translate_and_publish(
                    item_id,
                    text,
                    detected_language,
                    trace,
                    language_probability,
                    source_lang,
                    target_lang,
                    language_revision,
                ),
                self.loop,
            )
            future.add_done_callback(
                lambda done, current_item_id=item_id: self._handle_task_done(
                    current_item_id,
                    done,
                )
            )
            return

        def _run():
            try:
                self._run_in_private_event_loop(
                    self._translate_and_publish(
                        item_id,
                        text,
                        detected_language,
                        trace,
                        language_probability,
                        source_lang,
                        target_lang,
                        language_revision,
                    )
                )
            except Exception as exc:
                self._handle_error(item_id, exc)

        threading.Thread(target=_run, name="translation-fallback", daemon=True).start()

    def close(self, cleanup_allowed: bool = True):
        if not cleanup_allowed:
            return
        if self.client:
            try:
                if self.loop and self.loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(self.client.close(), self.loop)
                    future.result(timeout=3)
                else:
                    self._run_in_private_event_loop(self.client.close())
            except Exception as exc:
                logger.warning("翻译器关闭失败: {}", exc)
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)
        if self.loop and not self.loop.is_closed():
            self.loop.close()

    @staticmethod
    def _run_in_private_event_loop(coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    async def _translate_and_publish(
        self,
        item_id: str,
        text: str,
        detected_language: str = "",
        trace: Optional[LatencyTrace] = None,
        language_probability: float = 0.0,
        source_lang: str = "",
        target_lang: str = "",
        language_revision: int = 0,
    ):
        if not self.client:
            raise RuntimeError("翻译器未初始化")
        t0 = time.time()
        trace = trace or self._latency_traces.get(item_id)
        if trace:
            trace.translation_started_at = t0
            source_lang = source_lang or getattr(trace, "source_lang", "")
            target_lang = target_lang or getattr(trace, "target_lang", "")
            language_revision = language_revision or int(getattr(trace, "language_revision", 0) or 0)
        config = self._config_snapshot(source_lang, target_lang)
        if self._is_stale_language_flow(language_revision):
            if trace:
                trace.translation_finished_at = time.time()
            self._latency_traces.pop(item_id, None)
            self._remove_overlay_item(item_id)
            self._stats["skipped_translations"] = self._stats.get("skipped_translations", 0) + 1
            logger.info(
                "translation skipped: stale_language_flow, item_revision={}, current_revision={}, snapshot={}->{}, text={}",
                language_revision,
                int(self._language_revision_getter() or 0),
                source_lang or "unknown",
                target_lang or "unknown",
                text[:80],
            )
            return
        skip_reason = should_skip_translation_for_language(
            text,
            getattr(config, "source_lang", ""),
            detected_language,
            language_probability,
            config,
        )
        if skip_reason:
            if trace:
                trace.translation_finished_at = time.time()
            self._latency_traces.pop(item_id, None)
            self._stats["skipped_translations"] = self._stats.get("skipped_translations", 0) + 1
            logger.info(
                "translation skipped: {}, detected={}, expected={}, prob={:.2f}, text={}",
                skip_reason,
                detected_language or "unknown",
                getattr(config, "source_lang", "") or "unknown",
                float(language_probability or 0.0),
                text[:80],
            )
            return
        result = await self._translate_with_config_snapshot(config, text, detected_language)
        if self._is_stale_language_flow(language_revision):
            if trace:
                trace.translation_finished_at = time.time()
            self._latency_traces.pop(item_id, None)
            self._remove_overlay_item(item_id)
            self._stats["skipped_translations"] = self._stats.get("skipped_translations", 0) + 1
            logger.info(
                "translation result dropped: stale_language_flow, item_revision={}, current_revision={}, snapshot={}->{}, text={}",
                language_revision,
                int(self._language_revision_getter() or 0),
                source_lang or "unknown",
                target_lang or "unknown",
                text[:80],
            )
            return
        translated = clean_translation_output("" if result is None else result.translated)
        if trace:
            trace.translation_finished_at = time.time()
        if not translated or not translated.strip():
            translated = f"[翻译为空] {text}"
            logger.warning("翻译返回空结果，显示识别文本")
        source_lang = getattr(result, "source_lang", detected_language or "")
        target_lang = getattr(result, "target_lang", "")

        elapsed = time.time() - t0
        logger.info("translated: {} ({:.1f}s)", translated[:80], elapsed)
        self._event_bus.publish(
            TranslationReady(
                original=text,
                translated=translated,
                source_lang=source_lang,
                target_lang=target_lang,
                trace_id=item_id,
                language_revision=language_revision,
            )
        )

    def _config_snapshot(self, source_lang: str = "", target_lang: str = "") -> TranslationConfig:
        current = getattr(self.client, "config", TranslationConfig()) if self.client else TranslationConfig()
        return TranslationConfig(
            provider=getattr(current, "provider", TranslationConfig.provider),
            api_key=getattr(current, "api_key", TranslationConfig.api_key),
            model=getattr(current, "model", TranslationConfig.model),
            endpoint=getattr(current, "endpoint", TranslationConfig.endpoint),
            max_tokens=getattr(current, "max_tokens", TranslationConfig.max_tokens),
            temperature=getattr(current, "temperature", TranslationConfig.temperature),
            source_lang=source_lang or getattr(current, "source_lang", TranslationConfig.source_lang),
            target_lang=target_lang or getattr(current, "target_lang", TranslationConfig.target_lang),
            context_messages=getattr(current, "context_messages", TranslationConfig.context_messages),
            timeout_seconds=getattr(current, "timeout_seconds", TranslationConfig.timeout_seconds),
            max_concurrent_requests=getattr(
                current,
                "max_concurrent_requests",
                TranslationConfig.max_concurrent_requests,
            ),
            skip_language_mismatch=getattr(current, "skip_language_mismatch", TranslationConfig.skip_language_mismatch),
            language_gate_min_probability=getattr(
                current,
                "language_gate_min_probability",
                TranslationConfig.language_gate_min_probability,
            ),
            language_gate_short_text_min_probability=getattr(
                current,
                "language_gate_short_text_min_probability",
                TranslationConfig.language_gate_short_text_min_probability,
            ),
            language_gate_short_text_chars=getattr(
                current,
                "language_gate_short_text_chars",
                TranslationConfig.language_gate_short_text_chars,
            ),
            enable_local_phrase_cache=getattr(
                current,
                "enable_local_phrase_cache",
                TranslationConfig.enable_local_phrase_cache,
            ),
            local_phrase_cache=getattr(current, "local_phrase_cache", TranslationConfig.local_phrase_cache),
        )

    async def _translate_with_config_snapshot(self, config: TranslationConfig, text: str, detected_language: str):
        if hasattr(self.client, "translate_result_with_config"):
            return await self.client.translate_result_with_config(text, detected_language, config)
        return await self.client.translate_result(text, detected_language)

    def _is_stale_language_flow(self, language_revision: int) -> bool:
        current = int(self._language_revision_getter() or 0)
        return bool(language_revision and current and language_revision != current)

    def _remove_overlay_item(self, item_id: str):
        overlay = self._overlay_getter()
        if overlay and hasattr(overlay, "remove_translation"):
            overlay.remove_translation(item_id)

    def _handle_task_done(self, item_id: str, future):
        try:
            future.result()
        except Exception as exc:
            logger.exception("异步翻译任务失败: {}", exc)
            self._handle_error(item_id, exc, already_logged=True)

    def _handle_error(self, item_id: str, exc: Exception, already_logged: bool = False):
        if not already_logged:
            logger.exception("翻译任务失败: {}", exc)
        self._stats["errors"] += 1
        trace = self._latency_traces.get(item_id)
        if trace and not trace.translation_finished_at:
            trace.translation_finished_at = time.time()
        overlay = self._overlay_getter()
        if overlay:
            overlay.update_translation(item_id, f"[翻译失败] {str(exc)[:180]}")
