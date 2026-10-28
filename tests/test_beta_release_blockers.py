"""Release-blocker regressions over loopback HTTP; no real provider requests."""
import asyncio
from collections import defaultdict
import json
from pathlib import Path
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import aiohttp
from aiohttp import web

from voxgo.app import VoxGoApp
from voxgo.languages import ONLINE_DIRECTIONS
from voxgo.runtime.events import EventBus, TranslationReady
from voxgo.runtime.work_items import LatencyTrace
from voxgo.translation import GameTranslator, TranslationConfig
from voxgo.translation.base import TranslationRequest
from voxgo.translation.openai_compatible import OpenAICompatibleProvider
from voxgo.translation.runtime import TranslationRuntime


class BetaReleaseBlockerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.requests = []
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.response = {"choices": [{"message": {"content": "fixture complete"}, "finish_reason": "stop"}]}

        async def chat(request):
            body = await request.json()
            self.requests.append(body)
            if "blocked fixture" in body["messages"][-1]["content"]:
                self.started.set()
                await self.release.wait()
            return web.json_response(self.response)

        app = web.Application()
        app.router.add_post("/chat/completions", chat)
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, "127.0.0.1", 0)
        await site.start()
        self.url = "http://127.0.0.1:" + str(site._server.sockets[0].getsockname()[1])
        self.clients = []

    async def asyncTearDown(self):
        self.release.set()
        for client in self.clients:
            await client.close()
        await self.runner.cleanup()

    def config(self, **kwargs):
        return TranslationConfig(endpoint=self.url, api_key="", enable_local_phrase_cache=False, **kwargs)

    def client(self, **kwargs):
        client = GameTranslator(self.config(**kwargs))
        self.clients.append(client)
        return client

    def runtime(self, client):
        self.bus = EventBus()
        self.seen = []
        self.bus.subscribe(TranslationReady, self.seen.append)
        self.stats = defaultdict(int)
        self.overlay = Mock()
        self.runtime_owner = TranslationRuntime(self.bus, self.stats, {}, lambda: self.overlay)
        self.runtime_owner.client = client
        self.revision = 1
        self.runtime_owner.set_language_revision_getter(lambda: self.revision)
        return self.runtime_owner

    async def test_all_four_saved_length_responses_are_not_subtitles_or_context(self):
        evidence = Path(__file__).resolve().parents[1] / "docs/testing/evidence/v0.5.3-five-language-beta-2026-10-27"
        rows = json.loads((evidence / "online-text-results.json").read_text("utf-8"))
        # The ledger stores response metadata rather than full response JSON;
        # recreate the OpenAI wire shape with the actual retained output.
        truncated = [r for r in rows if r.get("finish_reason") == "length"]
        self.assertEqual(len(truncated), 4)
        for row in truncated:
            self.response = {"choices": [{"message": {"content": row["translated"]}, "finish_reason": "length"}]}
            provider = OpenAICompatibleProvider(self.config(context_messages=2))
            async with aiohttp.ClientSession() as session:
                result = await provider.translate(TranslationRequest("long fixture", "en", "zh"), session)
            self.assertTrue(result.translated.startswith("[翻译不完整]"))
            self.assertEqual(result.failure_reason, "other")
            self.assertEqual(result.raw, self.response)
            self.assertEqual(provider._contexts[("en", "zh")], [])
        self.assertEqual(len(self.requests), 4)

    async def test_normal_results_keep_all_twenty_routes_and_context(self):
        provider = OpenAICompatibleProvider(self.config(context_messages=2))
        async with aiohttp.ClientSession() as session:
            for source, target in sorted(ONLINE_DIRECTIONS):
                result = await provider.translate(TranslationRequest("normal fixture", source, target), session)
                self.assertEqual((result.source_lang, result.target_lang), (source, target))
                self.assertEqual(result.translated, "fixture complete")
                self.assertFalse(result.failure_reason)
            # Older compatible servers may omit finish_reason entirely.
            self.response = {"choices": [{"message": {"content": "second complete"}}]}
            result = await provider.translate(TranslationRequest("next fixture", "en", "zh"), session)
            self.assertEqual(result.translated, "second complete")
            self.assertEqual(len(self.requests[-1]["messages"]), 4)

    async def test_truncation_reaches_noncopyable_app_notice_and_existing_failure_category(self):
        self.response["choices"][0]["finish_reason"] = "length"
        client = self.client()
        runtime = self.runtime(client)
        runtime.analytics = Mock()
        owner = VoxGoApp.__new__(VoxGoApp)
        owner._stopping = False
        owner._language_flow_revision = 1
        owner._latency_traces = runtime._latency_traces
        owner._stats = self.stats
        owner._overlay = self.overlay
        owner._mobile = SimpleNamespace(server=None)
        self.bus.subscribe(TranslationReady, owner._handle_translation_ready)
        await runtime._translate_and_publish("length", "long fixture", "en", source_lang="en", target_lang="zh", language_revision=1)
        self.assertEqual(self.stats["translations"], 0)
        self.assertEqual(self.stats["errors"], 1)
        self.overlay.update_translation.assert_called_once_with("length", self.seen[0].translated, copyable=False)
        args = runtime.analytics.translation_result.call_args.args
        self.assertEqual((args[0], args[2:]), (False, ("api", "other", "openai_compatible")))
        self.assertEqual(client.get_stats()["total_translations"], 0)

    async def test_switch_cancels_active_and_semaphore_waiter_before_new_flow(self):
        client = self.client(max_concurrent_requests=1)
        runtime = self.runtime(client)
        runtime.analytics = Mock()
        first = asyncio.create_task(runtime._translate_and_publish("old-active", "blocked fixture", "en", source_lang="en", target_lang="zh", language_revision=1))
        await asyncio.wait_for(self.started.wait(), 2)
        second = asyncio.create_task(runtime._translate_and_publish("old-queued", "queued fixture", "en", source_lang="en", target_lang="zh", language_revision=1))
        await asyncio.sleep(0)
        self.assertEqual(len(runtime._active_translations), 2)
        self.revision = 2
        runtime.clear_context()
        client.config.source_lang, client.config.target_lang = "ru", "ja"
        await asyncio.wait_for(runtime._translate_and_publish("new", "Новая команда", "ru", language_probability=.99, source_lang="ru", target_lang="ja", language_revision=2), 2)
        cancelled = await asyncio.gather(first, second, return_exceptions=True)
        self.assertTrue(all(isinstance(x, asyncio.CancelledError) for x in cancelled))
        self.assertEqual(len(self.requests), 2)  # active old + new; queued old never sent
        self.assertEqual([x.trace_id for x in self.seen], ["new"])
        self.assertEqual((self.seen[0].source_lang, self.seen[0].target_lang), ("ru", "ja"))
        self.assertEqual(self.stats["errors"], 0)
        self.assertEqual(self.stats["skipped_translations"], 2)
        self.assertEqual(runtime._active_translations, {})
        self.assertEqual(client._translation_semaphore()._value, 1)
        self.assertTrue(all(c.args[0] is True for c in runtime.analytics.translation_result.call_args_list))

    async def test_prestart_generation_race_does_not_send_or_publish_old_task(self):
        runtime = self.runtime(self.client())
        generation = runtime._request_generation
        runtime._latency_traces["old"] = LatencyTrace("old", 1., 1.)
        runtime.clear_context()
        await runtime._translate_and_publish("old", "not sent", request_generation=generation)
        self.assertEqual(self.requests, [])
        self.assertEqual(self.seen, [])
        self.assertNotIn("old", runtime._latency_traces)
        self.overlay.remove_translation.assert_called_once_with("old")
        await runtime._translate_and_publish("new", "normal fixture")
        self.assertEqual(len(self.requests), 1)

    async def test_http_timeout_releases_slot_for_valid_next_sentence(self):
        client = self.client(max_concurrent_requests=1, timeout_seconds=.08)
        first = asyncio.create_task(client.translate_result("blocked fixture", "en"))
        await asyncio.wait_for(self.started.wait(), 2)
        second = asyncio.create_task(client.translate_result("next valid fixture", "en"))
        a, b = await asyncio.wait_for(asyncio.gather(first, second), 2)
        self.assertEqual(a.failure_reason, "timeout")
        self.assertTrue(a.translated.startswith("[翻译超时]"))
        self.assertEqual(b.translated, "fixture complete")
        self.assertEqual(client._translation_semaphore()._value, 1)
        self.assertEqual(len(self.requests), 2)

    async def test_actual_background_runtime_switch_drains_cancelled_tasks(self):
        client = self.client(max_concurrent_requests=1)
        runtime = self.runtime(client)
        runtime.start_loop()
        try:
            runtime.translate_async("old", "blocked fixture", "en", .99, "en", "zh", 1)
            await asyncio.wait_for(self.started.wait(), 2)
            runtime.translate_async("queued", "must never send", "en", .99, "en", "zh", 1)
            self.revision = 2
            runtime.clear_context()
            runtime.translate_async("current", "Новая команда", "ru", .99, "ru", "ja", 2)
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline and not self.seen:
                await asyncio.sleep(.01)
            self.assertEqual([e.trace_id for e in self.seen], ["current"])
            self.assertEqual(len(self.requests), 2)
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline and runtime._pending:
                await asyncio.sleep(.01)
            self.assertEqual(runtime._pending, set())
            self.assertEqual(runtime._active_translations, {})
            self.assertEqual(self.stats["errors"], 0)
        finally:
            self.assertTrue(runtime.close())
        self.assertFalse(runtime.thread.is_alive())
        self.assertTrue(client._session.closed)

    async def test_fallback_request_cancels_on_its_own_loop_without_stopping_new_work(self):
        from voxgo.translation.base import TranslationResult
        started, cancelled = threading.Event(), threading.Event()

        async def translate(text, detected_language, config):
            if text == "old":
                started.set()
                try:
                    await asyncio.sleep(30)
                finally:
                    cancelled.set()
            return TranslationResult("fixture", config.source_lang, config.target_lang, "fake")

        async def close():
            pass

        client = SimpleNamespace(config=self.config(), translate_result_with_config=translate,
                                 clear_context=Mock(), close=close)
        runtime = self.runtime(client)
        runtime.translate_async("old", "old")
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline and not started.is_set():
            await asyncio.sleep(.01)
        self.assertTrue(started.is_set())
        runtime.clear_context()
        runtime.translate_async("new", "new")
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline and (not cancelled.is_set() or not self.seen or runtime._fallback_loops):
            await asyncio.sleep(.01)
        self.assertTrue(cancelled.is_set())
        self.assertEqual([e.trace_id for e in self.seen], ["new"])
        self.assertEqual(runtime._fallback_loops, set())
        self.assertEqual(runtime._active_translations, {})
        self.assertTrue(await asyncio.to_thread(runtime.close))


if __name__ == "__main__":
    unittest.main()
