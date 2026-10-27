"""Explicit, bounded SiliconFlow validation. Never reads or writes app settings
unless --run-live --settings PATH is given. No retries or provider fallback.
Public/authored material only; local artifacts are not release acceptance.
"""
import argparse
import asyncio
from collections import defaultdict
from dataclasses import asdict, fields
import hashlib
import itertools
import json
import os
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Match the shipped PyInstaller exclusions. Optional CT2 converter imports of
# development-only PyTorch/Transformers can load competing native DLLs on Windows.
sys.modules["torch"] = None
sys.modules["transformers"] = None
from loguru import logger
logger.remove()  # Provider error payloads are not evaluation logs.
from voxgo.translation import GameTranslator, TranslationConfig


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class CallBudget:
    """Durable attempt accounting BEFORE HTTP. Only one runner may own a ledger."""
    def __init__(self, path, limit=60):
        if not 1 <= limit <= 60:
            raise ValueError("request cap must be 1..60")
        self.path, self.limit = path, limit
        self.lock = threading.Lock()
        self.data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
            "model": "tencent/Hunyuan-MT-7B", "attempts": [],
            "price_source": "https://www.siliconflow.cn/pricing",
            "price_checked_date": time.strftime("%Y-%m-%d", time.gmtime()), "input_cny_per_million": 0,
            "output_cny_per_million": 0, "estimated_cost_cny": 0,
            "cost_basis": "Official input/output prices listed as free; not an invoice.",
        }
        if self.data["model"] != "tencent/Hunyuan-MT-7B" or self.data["estimated_cost_cny"] != 0:
            raise ValueError("price/model cannot be confirmed; stop")

    def reserve(self, label):
        with self.lock:
            if len(self.data["attempts"]) >= self.limit:
                raise RuntimeError("authorized HTTP attempt cap reached; stop")
            self.data["attempts"].append({"label": label, "reserved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
            write(self.path, self.data)


class BudgetClient(GameTranslator):
    def __init__(self, config, budget):
        super().__init__(config)
        self.budget = budget
        self.label = ""
        self.rows = []

    async def _get_session(self):
        session = await super()._get_session()
        if not getattr(session, "_voxgo_counted", False):
            post = session.post
            def counted(*args, **kwargs):
                self.budget.reserve(self.label)
                return post(*args, **kwargs)
            session.post = counted
            session._voxgo_counted = True
        return session

    async def translate_result_with_config(self, text, detected_language="", config=None):
        start = time.perf_counter()
        result = await super().translate_result_with_config(text, detected_language, config)
        if result:
            self.rows.append({"label": self.label, "text": text,
                "source_lang": result.source_lang, "target_lang": result.target_lang,
                "translated": result.translated.replace(self.config.api_key, "[REDACTED]"),
                "elapsed_ms": (time.perf_counter() - start) * 1000,
                "provider_elapsed_ms": result.elapsed_seconds * 1000 if not result.failure_reason else None,
                "failure_reason": result.failure_reason,
                "finish_reason": ((result.raw or {}).get("choices") or [{}])[0].get("finish_reason"),
                "usage": (result.raw or {}).get("usage"), "human_review": "pending"})
        return result


def load_config(path):
    from urllib.parse import urlparse
    data = json.loads(path.read_text(encoding="utf-8-sig"))["translation"]
    if (data.get("provider", "openai_compatible") != "openai_compatible"
        or data.get("model") != "tencent/Hunyuan-MT-7B"
        or urlparse(data.get("endpoint", "")).netloc != "api.siliconflow.cn"
        or urlparse(data.get("endpoint", "")).scheme != "https"
        or not data.get("api_key") or data["api_key"].startswith("YOUR_")):
        raise ValueError("authorized existing SiliconFlow/Hunyuan configuration unavailable; stop")
    config = TranslationConfig(**{f.name: data[f.name] for f in fields(TranslationConfig) if f.name in data})
    config.enable_local_phrase_cache = False  # Measure actual provider, not EN/ZH cache.
    return config


async def text_run(config, budget, output, case_ids=None):
    cases = json.loads((ROOT / "tests/assets/multilingual_online/cases.json").read_text(encoding="utf-8"))["cases"]
    client = BudgetClient(config, budget)
    selected = []
    limits = {("ja", "zh"): 8, ("ko", "zh"): 8, ("ru", "zh"): 8,
              ("zh", "ja"): 4, ("en", "zh"): 2, ("zh", "en"): 2}
    try:
        for pair, count in limits.items():
            pair_cases = [row for row in cases if (row["source_lang"], row["target_lang"]) == pair]
            for split in ("dev", "holdout"):
                selected.extend([r for r in pair_cases if r["split"] == split][:count//2])
        if case_ids:
            selected = [r for r in cases if r["id"] in set(case_ids)]
            if {r["id"] for r in selected} != set(case_ids):
                raise ValueError("unknown evaluation case ID")
        for row in selected:
            config.source_lang, config.target_lang = row["source_lang"], row["target_lang"]
            client.label = row["id"]
            await client.translate_result_with_config(row["text"], row["source_lang"])
            client.rows[-1].update({key: row[key] for key in ("reference_meaning", "key_meanings", "categories", "split", "scene")})
            write(output, {"kind": "authored_text_live", "rows": client.rows, "human_review": "pending"})
            if client.rows[-1]["failure_reason"]:
                raise RuntimeError("authorized provider failed; stop without substitution")
    finally:
        await client.close()


def pcm(row):
    path = Path(row["audio"])
    if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
        raise ValueError("audio hash mismatch")
    with wave.open(str(path), "rb") as stream:
        if (stream.getnchannels(), stream.getsampwidth(), stream.getframerate()) != (1,2,16000):
            raise ValueError("expected mono PCM16 16kHz")
        return stream.readframes(stream.getnframes())


def rss_bytes():
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in ("PeakWorkingSetSize", "WorkingSetSize",
            "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
            "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return counters.WorkingSetSize


def audio_run(config, budget, manifest, output, *, sources=("ja", "ko", "ru"),
              speech_strategy="language_aware", clips_per_source=2, client_factory=BudgetClient):
    """Actual capture segmentation -> SpeechPipeline -> online -> Qt widget.

    PCM replay replaces a physical loopback device; offscreen Qt callback is
    widget-update latency, not compositor/display latency or game FPS.
    """
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from voxgo.app import VoxGoApp
    from PyQt5.QtWidgets import QApplication
    from voxgo.audio.capture import SystemAudioCapture
    from voxgo.asr.pipeline import SpeechPipeline
    from voxgo.asr.whisper_engine import SpeechRecognizer
    from voxgo.asr.language_profiles import effective_speech_config
    from voxgo.config.loader import default_app_config, migrate_runtime_defaults, sync_language_flow, apply_language_runtime_policy
    from voxgo.runtime.events import EventBus, TranscriptReady, TranslationReady
    from voxgo.translation.runtime import TranslationRuntime
    from voxgo.ui.overlay_window import GameOverlay
    qt = QApplication.instance() or QApplication([])
    workload = json.loads(manifest.read_text(encoding="utf-8"))
    if isinstance(workload, dict):
        workload = workload["clips"]
    all_rows = []
    for source in sources:
        app_config = default_app_config()
        app_config.translation = config
        config.source_lang, config.target_lang = source, "zh"
        app_config.whisper.multilingual_asr_strategy = speech_strategy
        migrate_runtime_defaults(app_config)
        sync_language_flow(app_config)
        apply_language_runtime_policy(app_config)
        app_config = effective_speech_config(app_config)
        app_config.whisper.local_files_only = True
        recognizer = SpeechRecognizer(app_config.whisper)
        recognizer.initialize()
        clips = [r for r in workload if r.get("source_lang", r.get("language")) == source][:clips_per_source]
        if not clips:
            raise ValueError("no licensed audio for " + source)
        # Independent whole-clip ASR baseline; no additional API calls.
        whole = []
        for row in clips:
            start = time.perf_counter()
            result = recognizer.transcribe_audio_bytes_with_language(pcm(row), 16000)
            whole.append({"id": row["id"], "reference": row.get("reference_text", row.get("reference", row.get("text", ""))),
                "asr": asdict(result), "asr_ms": (time.perf_counter()-start)*1000})
        bus, traces, stats = EventBus(), {}, defaultdict(int)
        owner = VoxGoApp.__new__(VoxGoApp)
        owner.config, owner._stopping, owner._stats = app_config, False, stats
        owner._latency_traces, owner._language_flow_revision = traces, 1
        owner._mobile, owner._analytics = SimpleNamespace(server=None), None
        notices, subtitles, asr_rows, captures, diagnostics = [], [], [], [], []
        diagnostic_sink = logger.add(lambda message: diagnostics.append(str(message.record['message'])),
            filter=lambda record: record['name'] in {'voxgo.asr.pipeline', 'voxgo.translation.runtime'}, level='INFO')
        source_by_trace = {}
        owner._notify_user = lambda *args: notices.append(str(args))
        start_clock = time.perf_counter()
        def updated(item_id):
            item = next((r for r in overlay._translations if r.item_id == item_id), None)
            trace = traces.get(item_id)
            if trace and item and item.copyable:
                subtitles.append({"trace_id": item_id, "original": item.original, "translated": item.translated,
                    "capture_emit_to_widget_ms": (time.time()-trace.queued_at)*1000,
                    "trace": trace.summary_ms()})
                native = source_by_trace.get(item_id, {})
                if native.get("source_start_frame") is not None:
                    subtitles[-1].update({
                        "first_segment_pcm_frame_to_widget_ms": (time.perf_counter()-start_clock-native["source_start_frame"]/16000)*1000,
                        "last_segment_pcm_frame_to_widget_ms": (time.perf_counter()-start_clock-native["source_end_frame"]/16000)*1000,
                        "source_start_frame": native["source_start_frame"], "source_end_frame": native["source_end_frame"],
                    })
        overlay = GameOverlay(config=app_config.overlay, translation_config=config,
            whisper_config=app_config.whisper, audio_config=app_config.audio, on_overlay_updated=updated)
        owner._overlay = overlay
        overlay.show()
        client = client_factory(config, budget)
        client.label = source + "-pcm-replay"
        runtime = TranslationRuntime(bus, stats, traces, lambda: overlay)
        runtime.client = client
        runtime.set_language_revision_getter(lambda: 1)
        runtime.start_loop()
        owner._translation = runtime
        counter = itertools.count(1)
        class ObservedRecognizer:
            def __getattr__(self, name):
                return getattr(recognizer, name)
            def transcribe_audio_bytes_with_language(self, data, sample_rate=16000, language_override=None, config_override=None):
                started = time.perf_counter()
                result = recognizer.transcribe_audio_bytes_with_language(data, sample_rate, language_override, config_override)
                offset = data_stream.find(data)
                unique = offset >= 0 and offset % 2 == 0 and data_stream.find(data, offset+1) < 0
                asr_rows.append({"text": result.text, "language": result.language,
                    "probability": result.language_probability, "asr_ms": (time.perf_counter()-started)*1000,
                    "source_start_frame": offset//2 if unique else None,
                    "source_end_frame": (offset+len(data))//2 if unique else None})
                return result
        pipeline = SpeechPipeline(lambda: app_config, lambda: ObservedRecognizer(), bus, stats,
            lambda: True, lambda: False, lambda: str(next(counter)), traces, owner._notify_user, lambda: 1)
        owner._speech_pipeline = pipeline
        def transcript(event):
            if asr_rows:
                source_by_trace[event.trace_id] = asr_rows[-1]
            owner._handle_transcript_ready(event)
        bus.subscribe(TranscriptReady, transcript)
        bus.subscribe(TranslationReady, owner._handle_translation_ready)
        capture = SystemAudioCapture(app_config.audio)
        def segment(row):
            captures.append({"reason": row.reason, "duration": row.duration_seconds})
            pipeline.on_speech_detected(row)
        capture.set_speech_callback(segment)
        data = b"\0" * (32000 * 3) + b"".join(pcm(r) + b"\0" * (32000 * 2) for r in clips) + b"\0" * 32000
        data_stream = data
        frames = 16000 * app_config.audio.chunk_duration_ms // 1000
        done = threading.Event()
        def feed():
            for offset in range(0, len(data), frames*2):
                deadline = start_clock + min(offset + frames*2, len(data))/32000
                remaining = deadline-time.perf_counter()
                if remaining > 0:
                    time.sleep(remaining)
                capture._enqueue_audio_block(data[offset:offset+frames*2].ljust(frames*2, b"\0"))
            done.set()
        samples, cpu_start = [], time.process_time()
        pipeline.start()
        start_clock = time.perf_counter()
        feeder = threading.Thread(target=feed, daemon=True)
        feeder.start()
        try:
            quiet = None
            while time.perf_counter()-start_clock < len(data)/32000 + 45:
                capture.process_audio()
                qt.processEvents()
                if done.is_set():
                    capture._handle_idle_timeout(time.monotonic())
                samples.append(rss_bytes())
                pending = not pipeline._queue.empty() or pipeline._recognition_busy or pipeline._pending_buffer.has_pending() or pipeline._busy_weak_buffer.has_pending() or bool(runtime._pending) or bool(capture._speech_buffer)
                if done.is_set() and not pending:
                    quiet = quiet or time.monotonic()
                    if time.monotonic()-quiet > 1:
                        break
                else:
                    quiet = None
                time.sleep(.005)
            wall = time.perf_counter()-start_clock
            cpu_end = time.process_time()
            all_rows.append({"source_lang": source, "domain": "public_read_speech",
                "speech_strategy": speech_strategy, "drain_complete": not pending,
                "clip_ids": [row['id'] for row in clips], "diagnostics": diagnostics,
                "whole_clip_asr": whole, "stream_asr": asr_rows, "subtitles": subtitles,
                "captures": captures, "api": client.rows, "stats": dict(stats), "notices": notices,
                "cpu_one_core_percent": 100*(cpu_end-cpu_start)/wall,
                "peak_rss_bytes": max(samples, default=0), "wall_seconds": wall,
                "whisper": {k: getattr(app_config.whisper, k) for k in ("active_model_size", "beam_size", "cpu_threads", "language", "initial_prompt", "prompt_profile")},
                "effective_audio": {k: getattr(app_config.audio, k) for k in ("max_speech_seconds", "pre_roll_ms", "speech_idle_timeout_ms")},
                "effective_diagnostic_mode": getattr(app_config.audio, "diagnostics_latency_mode", app_config.audio.latency_mode),
                "measurement": "paced PCM replay, production capture/ASR/runtime/offscreen Qt; no physical loopback/display/game"})
            write(output, all_rows)
        finally:
            feeder.join(3)
            pipeline.stop()
            runtime.close()
            capture._audio.terminate()
            overlay.grab().save(str(output.with_name(source + "-overlay.png")))
            overlay._allow_close = True
            overlay.close()
            qt.processEvents()
            recognizer.cleanup()
            logger.remove(diagnostic_sink)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument("--settings", type=Path)
    parser.add_argument("--confirmed-free-price-date", required=True, help="Date official price was checked; must be today UTC")
    parser.add_argument("--stage", choices=("text", "audio"), required=True)
    parser.add_argument("--audio-manifest", type=Path)
    parser.add_argument("--output-name", default="audio-results.json")
    parser.add_argument("--case-ids", help="Explicit comma-separated authored text IDs; no retries")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "build/multilingual-online/live")
    args = parser.parse_args()
    if not args.run_live or not args.settings or args.confirmed_free_price_date != time.strftime("%Y-%m-%d", time.gmtime()):
        parser.error("explicit live authorization, existing settings and current official free-price confirmation required")
    # Reject overlapping processes even if they share the authorized ledger.
    lock = args.output_dir / "runner.lock"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with lock.open("x"):
        pass
    original = args.settings.read_bytes()
    try:
        config = load_config(args.settings)
        write(args.output_dir / (args.stage + "-config.json"), {
            "model": config.model, "provider": config.provider,
            **{key: getattr(config, key) for key in ("max_tokens", "temperature", "timeout_seconds", "max_concurrent_requests", "context_messages")},
            "enable_local_phrase_cache": False, "human_review": "pending",
        })
        budget = CallBudget(args.output_dir / "budget.json")
        if args.stage == "text":
            asyncio.run(text_run(config, budget, args.output_dir / ("text-extra.json" if args.case_ids else "text-results.json"), args.case_ids.split(",") if args.case_ids else None))
        else:
            audio_run(config, budget, args.audio_manifest, args.output_dir / args.output_name)
        print(json.dumps({"attempts": len(budget.data["attempts"]), "estimated_cost_cny": 0, "settings_unchanged": args.settings.read_bytes() == original}))
    finally:
        lock.unlink(missing_ok=True)
        if args.settings.read_bytes() != original:
            raise RuntimeError("settings changed externally during validation")


if __name__ == "__main__":
    main()
