"""Execute the separately approved 20-text blocker plan; no ASR/user-state IO.

Reuse the existing durable budget, strict credential loader and measured HTTP
client. Render real outcomes with TranslationRuntime + the app handler + native
Qt. This is not Full EXE, voice-end, game or bilingual human acceptance.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from collections import defaultdict
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_five_language_online import (
    AttemptBudget, MeasuredClient, MODEL, TRACE, CURRENT,
    atomic, claim_run, credentials, load, sha,
)
from voxgo.languages import ONLINE_DIRECTIONS
from voxgo.translation.prompt import translation_system_prompt

ENDPOINT = "https://api.siliconflow.cn/v1/chat/completions"
SETTINGS = dict(max_tokens=80, temperature=0, context_messages=0,
                max_concurrent_requests=1, timeout_seconds=12, local_phrase_cache=False)


def validate_plan(plan):
    if (plan.get("provider") != "openai_compatible" or plan.get("endpoint") != ENDPOINT
            or plan.get("model") != MODEL or plan.get("config") != SETTINGS
            or plan.get("expected_requests") != 20 or plan.get("hard_request_cap") != 20
            or plan.get("automatic_retries") != 0 or plan.get("new_audio_api_runs") != 0
            or len(plan.get("cases", [])) != 20):
        raise ValueError("Only the approved fixed 20-text plan is allowed")
    ids = set()
    for case in plan["cases"]:
        if (case["id"] in ids or (case["source"], case["target"]) not in ONLINE_DIRECTIONS
                or not isinstance(case.get("input"), str) or not case["input"].strip()):
            raise ValueError("Duplicate case or unsupported/empty input")
        ids.add(case["id"])


def validate_approval(approval, plan_hash):
    if (approval.get("authorized") is not True or approval.get("plan_sha256") != plan_hash
            or approval.get("model") != MODEL or approval.get("call_limit") != 20
            or approval.get("confirmed_free_price_date_utc") != datetime.now(timezone.utc).date().isoformat()):
        raise ValueError("New matching authorization for exactly 20 attempts and current free price required")


class BlockerClient(MeasuredClient):
    def __init__(self, config, budget, cases, *, fixture=False):
        super().__init__(config, budget, "blocker_text", allow_loopback_fixture=fixture)
        self.allowed_cases = {c["id"]: c for c in cases}

    async def _get_session(self):
        session = await super()._get_session()
        if not getattr(session, "_blocker_plan_guard", False):
            original = session.post

            def post(url, *args, **kwargs):
                context = CURRENT.get() or {}
                case = self.allowed_cases.get(context.get("case_id"))
                payload = kwargs.get("json") or {}
                messages = payload.get("messages") or []
                if (not case or context.get("source") != case["source"]
                        or context.get("target") != case["target"] or context.get("input") != case["input"]
                        or payload.get("model") != MODEL or payload.get("max_tokens") != 80
                        or payload.get("temperature") != 0 or payload.get("stream") is not False
                        or len(messages) != 2
                        or messages[0] != {"role": "system", "content": translation_system_prompt(case["source"], case["target"])}
                        or f"<source_text>{case['input']}</source_text>" not in messages[-1].get("content", "")
                        or (not self.fixture and str(url) != ENDPOINT)):
                    raise ValueError("Unplanned route/prompt/payload; no request sent")
                return original(url, *args, **kwargs)

            session.post = post
            session._blocker_plan_guard = True
        return session

    async def translate_result_with_config(self, text, detected_language="", config=None):
        result = await super().translate_result_with_config(text, detected_language, config)
        raw = getattr(result, "raw", None) or {}
        choice = (raw.get("choices") or [{}])[0]
        partial = (choice.get("message") or {}).get("content") or ""
        # Preserve actual partial output for review, without publishing it to UI.
        key = self.config.api_key.strip()
        if key:
            partial = partial.replace(key, "[REDACTED]")
        self.rows[-1]["raw_output"] = partial
        self.rows[-1].update(provider=getattr(result, "provider", ""),
            result_source=getattr(result, "source_lang", ""), result_target=getattr(result, "target_lang", ""))
        case = self.allowed_cases[self.case_id]
        if result is not None and (result.provider != "openai_compatible"
                or (result.source_lang, result.target_lang) != (case["source"], case["target"])):
            self.budget.data["stop_reason"] = "unexpected_result_route_or_provider"
            atomic(self.budget.path, self.budget.data)
        return result


def percentile(values, q):
    from scripts.ru_benchmark_metrics import percentile as calculate
    return calculate(values, q)


def summarize(rows, budget, planned):
    attempts = budget.data["attempts"]
    return dict(planned=planned, attempted=len(attempts), completed_case_results=len(rows),
        http_200=sum(r.get("http_status") == 200 for r in rows),
        complete_stop=sum(r.get("http_status") == 200 and r.get("finish_reason") == "stop" and not r.get("failure_reason") for r in rows),
        length=sum(r.get("finish_reason") == "length" for r in rows),
        timeouts=sum(r.get("failure_reason") == "timeout" for r in rows),
        cancelled=sum(r.get("exception_type") in {"CancelledError", "Cancelled"} for r in rows),
        unfinished=sum(r.get("state") == "unfinished_or_exception" for r in rows),
        normal_copyable_subtitles=sum(bool(r.get("ui", {}).get("copyable")) for r in rows),
        error_notices=sum(bool(r.get("ui")) and not r["ui"].get("copyable") for r in rows),
        api_all_p50_ms=percentile([r["elapsed_ms"] for r in rows if r.get("attempt_id")], .5),
        api_all_p95_ms=percentile([r["elapsed_ms"] for r in rows if r.get("attempt_id")], .95),
        submit_to_qt_p50_ms=percentile([r["submit_to_widget_ms"] for r in rows if r.get("submit_to_widget_ms") is not None], .5),
        submit_to_qt_p95_ms=percentile([r["submit_to_widget_ms"] for r in rows if r.get("submit_to_widget_ms") is not None], .95),
        stop_reason=budget.data["stop_reason"], automatic_retries=0,
        human_language_accuracy=None, human_intelligibility_rate=None, semantic_correctness=None,
        speech_latency=None, game_fps=None, scope="20 text inputs -> real provider -> native Qt app handler; no ASR/Full EXE")


def run_cases(plan, budget, config, output, *, platform="windows", fixture=False):
    import os
    os.environ["QT_QPA_PLATFORM"] = platform
    from loguru import logger
    logger.remove()  # Never log provider bodies/credentials; persist sanitized rows only.
    from PyQt5.QtWidgets import QApplication
    from voxgo.app import VoxGoApp
    from voxgo.runtime.events import EventBus, TranslationReady
    from voxgo.translation.runtime import TranslationRuntime
    from voxgo.ui.overlay_window import GameOverlay
    from voxgo.ui.config_models import OverlayConfig

    qt = QApplication.instance() or QApplication([])
    if platform == "windows" and qt.platformName() != "windows":
        raise ValueError("Native Windows Qt required")
    overlay = GameOverlay(config=OverlayConfig(window_width=720, window_height=300), translation_config=config)
    owner = VoxGoApp.__new__(VoxGoApp)
    owner._stopping = False
    owner._language_flow_revision = 1
    owner._stats, owner._latency_traces = defaultdict(int), {}
    owner._overlay, owner._mobile, owner._analytics = overlay, SimpleNamespace(server=None), None
    bus = EventBus()
    runtime = TranslationRuntime(bus, owner._stats, owner._latency_traces, lambda: overlay)
    client = BlockerClient(config, budget, plan["cases"], fixture=fixture)
    runtime.client = client
    runtime.set_language_revision_getter(lambda: owner._language_flow_revision)
    bus.subscribe(TranslationReady, owner._handle_translation_ready)
    widgets, origins = {}, {}

    def updated(item_id):
        item = next((x for x in overlay._translations if x.item_id == item_id), None)
        if item and not item.translated.startswith("..."):
            widgets[item_id] = dict(translated=item.translated, copyable=item.copyable,
                qt_updated_monotonic=time.perf_counter(), original=item.original)

    overlay._on_overlay_updated = updated
    overlay.show()
    qt.processEvents()
    if platform == "windows":
        import ctypes
        from ctypes import wintypes
        visible = ctypes.windll.user32.IsWindowVisible
        visible.argtypes, visible.restype = [wintypes.HWND], wintypes.BOOL
        if not visible(int(overlay.winId())):
            raise ValueError("Native widget not visible")
    results = []
    try:
        runtime.start_loop()
        for case in plan["cases"]:
            if budget.data["stop_reason"] or len(budget.data["attempts"]) >= budget.limit:
                break
            owner._language_flow_revision += 1
            runtime.clear_context()
            config.source_lang, config.target_lang = case["source"], case["target"]
            client.case_id = case["id"]
            overlay.clear_history()
            overlay._apply_language_flow(case["source"], case["target"])
            overlay.add_translation_with_id(case["id"], case["input"], "...正在翻译")
            qt.processEvents()
            origins[case["id"]] = time.perf_counter()
            token = TRACE.set(case["id"])
            try:
                runtime.translate_async(case["id"], case["input"], case["source"], 1.,
                    case["source"], case["target"], owner._language_flow_revision)
            finally:
                TRACE.reset(token)
            deadline = time.monotonic() + config.timeout_seconds + 5
            while time.monotonic() < deadline:
                qt.processEvents()
                with runtime._pending_lock:
                    pending = bool(runtime._pending or runtime._active_translations)
                if not pending:
                    break
                time.sleep(.01)
            else:
                runtime.clear_context()
                budget.data["stop_reason"] = "bounded_drain_timeout"
                atomic(budget.path, budget.data)
            qt.processEvents()
            row = copy.deepcopy(next((r for r in reversed(client.rows) if r["case_id"] == case["id"]),
                dict(case_id=case["id"], state="unfinished_or_exception", source=case["source"], target=case["target"])))
            row["kind"] = case["kind"]
            row["ui"] = copy.deepcopy(widgets.get(case["id"], {}))
            row["submit_to_widget_ms"] = ((row["ui"]["qt_updated_monotonic"] - origins[case["id"]]) * 1000) if row["ui"] else None
            row["critical_meanings"] = case["critical_meanings"]
            row["human_semantic_review"] = "pending"
            if row.get("finish_reason") == "length":
                row["truncation_guard_passed"] = (bool(row["ui"]) and not row["ui"]["copyable"]
                    and row["ui"]["translated"].startswith("[翻译不完整]"))
                if not row["truncation_guard_passed"]:
                    budget.data["stop_reason"] = "truncation_display_guard_failed"
            if not row.get("attempt_id"):
                budget.data["stop_reason"] = budget.data["stop_reason"] or "no_planned_provider_attempt"
            if row.get("http_status") and row["http_status"] != 200:
                budget.data["stop_reason"] = budget.data["stop_reason"] or "http_" + str(row["http_status"])
            results.append(row)
            atomic(output / "results.json", results)
            atomic(budget.path, budget.data)
            overlay.grab().save(str(output / (case["id"] + ".png")))
            print(f"{len(budget.data['attempts'])}/20 {case['id']} HTTP={row.get('http_status')} finish={row.get('finish_reason')} failure={row.get('failure_reason') or '-'}", flush=True)
    finally:
        closed = runtime.close()
        overlay._allow_close = True
        overlay.close()
        qt.processEvents()
        atomic(output / "cleanup.json", dict(runtime_closed=closed, thread_stopped=not runtime.thread or not runtime.thread.is_alive(),
            qt_platform=qt.platformName(), native_visible_checked=platform == "windows", production_telemetry_initialized=False, asr_runs=0))
    summary = summarize(results, budget, len(plan["cases"]))
    summary["status"] = "complete" if len(results) == len(plan["cases"]) else "stopped_incomplete"
    atomic(output / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("plan", "approval", "settings", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--run-live", action="store_true")
    args = parser.parse_args()
    if not args.run_live:
        parser.error("Explicit --run-live required")
    plan, approval = load(args.plan), load(args.approval)
    validate_plan(plan)
    validate_approval(approval, sha(args.plan))
    if args.output.resolve() != (ROOT / plan["output_directory"]).resolve() or args.output.exists():
        raise ValueError("Only the new authorized output directory is allowed")
    if subprocess.check_output(["git", "diff", plan["runtime_fix_commit"], "--", "voxgo"], cwd=ROOT):
        raise ValueError("Formal runtime differs from the approved fix commit")
    config = credentials(args.settings)
    for name, value in SETTINGS.items():
        if name != "local_phrase_cache":
            setattr(config, name, value)
    config.enable_local_phrase_cache = False
    before = sha(args.settings)
    budget = AttemptBudget(args.output / "attempt-ledger.json", approval, sha(args.plan))
    claim_run(args.approval, args.output, sha(args.plan))
    args.output.mkdir()
    atomic(args.output / "authorization.json", approval)
    atomic(args.output / "plan.json", plan)
    try:
        summary = run_cases(plan, budget, config, args.output)
        print(json.dumps(summary), flush=True)
    finally:
        atomic(args.output / "provenance.json", dict(plan_sha256=sha(args.plan), settings_sha256_before=before,
            settings_sha256_after=sha(args.settings), settings_unchanged=sha(args.settings) == before,
            runtime_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
            script_sha256=sha(__file__), runtime_fix_commit=plan["runtime_fix_commit"], api_requests=len(budget.data["attempts"]),
            asr_runs=0, real_audio_inputs=0, retries=0, human_acceptance="pending"))


if __name__ == "__main__":
    main()
