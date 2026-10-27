"""Zero-network, paced RU capture-duration experiment using production Pipeline.

Each round/cadence/arm runs in a fresh subprocess. Forward/reverse order checks
repeatability; recordings already used for development are not new holdouts.
"""
import argparse
from collections import defaultdict
from contextlib import contextmanager
import copy
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import statistics
import subprocess
import sys
import threading
import time
import wave
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")
sys.modules["torch"] = None
sys.modules["transformers"] = None

RADIATION = "fleurs-ru-test-1692-10024935581249406669"
MOSQUITO = "fleurs-ru-holdout-1762-10098401296465388159"
IDS = (RADIATION, MOSQUITO)
RATE, CHUNK = 16000, 1920


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write(path, data):
    # Only inside an exclusively created run directory. Never used on inputs.
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


@contextmanager
def offline_guard():
    """Fail closed before a Python network connection/DNS or Analytics import."""
    state = dict(active=True, blocked_network_attempts=0, blocked_analytics_imports=0)
    def audit(event, args):
        if not state["active"]:
            return
        if event in {"socket.connect", "socket.getaddrinfo", "socket.sendto", "socket.bind"}:
            state["blocked_network_attempts"] += 1
            raise RuntimeError("Offline experiment: network disabled")
        if event == "import" and (args[0].startswith("voxgo.analytics") or args[0].startswith("voxgo.telemetry")):
            state["blocked_analytics_imports"] += 1
            raise RuntimeError("Offline experiment: Analytics disabled")
    sys.addaudithook(audit)
    try:
        yield state
    finally:
        state["active"] = False


def create_output(path):
    path.mkdir(parents=True, exist_ok=False)
    return path


def validate_output(path, manifest, models):
    target = path.resolve()
    protected = [manifest.parent.resolve(), models.resolve(), (ROOT/"voxgo").resolve(),
                 (ROOT/"docs/testing/evidence/v0.5.3-paired-speech-2026-10-27").resolve()]
    if any(target == p or target.is_relative_to(p) for p in protected):
        raise ValueError("Output must be outside original evidence, model and runtime directories")


def load_pcm(manifest):
    rows = json.loads(manifest.read_text(encoding="utf-8-sig"))
    clips, parts, cursor = [], [b"\0" * (RATE*3*2)], RATE*3
    selected = {r["id"]: r for r in rows if r["id"] in IDS}
    if set(selected) != set(IDS):
        raise ValueError("Both existing RU recordings required")
    for clip_id in IDS:
        row = copy.deepcopy(selected[clip_id])
        path = Path(row["audio"])
        if not path.is_absolute():
            path = manifest.parent / path
        if digest(path.read_bytes()) != row["sha256"]:
            raise ValueError("WAV SHA256 mismatch: " + clip_id)
        with wave.open(str(path), "rb") as source:
            if (source.getnchannels(), source.getsampwidth(), source.getframerate()) != (1, 2, RATE):
                raise ValueError("Expected mono PCM16 16kHz")
            pcm = source.readframes(source.getnframes())
        row.update(audio=str(path.resolve()), sample_rate=RATE, pcm_sha256=digest(pcm),
                   stream_start_frame=cursor, stream_end_frame=cursor+len(pcm)//2)
        clips.append(row)
        parts.extend([pcm, b"\0" * (RATE*2*2)])
        cursor += len(pcm)//2 + RATE*2
    parts.append(b"\0" * (RATE*2))
    data = b"".join(parts)
    # Match paired: last short audio callback is zero padded to a full chunk.
    padding = (-len(data)) % (CHUNK*2)
    return clips, data + b"\0" * padding, len(data)//2


def local_base(models):
    base = models / "models--Systran--faster-whisper-base"
    ref = base / "refs/main"
    if not ref.is_file():
        raise FileNotFoundError("Local base model ref missing; no download allowed")
    revision = ref.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("Invalid cached model revision")
    snapshot = base / "snapshots" / revision
    files = [snapshot / name for name in ("config.json", "model.bin", "tokenizer.json", "vocabulary.txt")]
    if not all(p.is_file() for p in files):
        raise FileNotFoundError("Local base model incomplete; stop without download")
    return snapshot, {p.name: dict(bytes=p.stat().st_size, sha256=digest(p.read_bytes())) for p in files}


def make_config(models, maximum, pre_roll, idle):
    from voxgo.config.loader import default_app_config, migrate_runtime_defaults, sync_language_flow, apply_language_runtime_policy
    from voxgo.asr.language_profiles import effective_speech_config
    user = copy.deepcopy(default_app_config())  # No load_config() or user-settings access.
    user.translation.source_lang, user.translation.target_lang = "ru", "zh"
    user.whisper.multilingual_asr_strategy = "language_aware"
    migrate_runtime_defaults(user)
    sync_language_flow(user)
    apply_language_runtime_policy(user)
    before = copy.deepcopy(user)
    config = copy.deepcopy(effective_speech_config(user))
    # Overrides AFTER profile resolution, used by BOTH capture and work snapshots.
    config.audio.max_speech_seconds = maximum
    config.audio.pre_roll_ms = pre_roll
    config.audio.speech_idle_timeout_ms = idle
    whisper = config.whisper
    whisper.active_model_size = "base"
    whisper.model_dir = str(models.resolve())
    whisper.local_files_only = True
    whisper.device, whisper.compute_type = "cpu", "int8"
    whisper.beam_size, whisper.cpu_threads, whisper.num_workers = 1, 2, 1
    whisper.auto_cpu_threads = False
    whisper.language, whisper.source_language = "auto", "ru"
    whisper.temperature, whisper.condition_on_previous_text = 0., False
    whisper.prompt_profile, whisper.initial_prompt = "none", ""
    if user != before:
        raise AssertionError("Source configuration mutated")
    return config


def schedule(maxima, cadences, pre_roll, idle, rounds):
    plan = []
    for repeat in range(1, rounds+1):
        cases = [(ms, maximum) for ms in cadences for maximum in maxima]
        if repeat % 2 == 0:
            cases.reverse()
        for cadence, maximum in cases:
            plan.append(dict(id=f"r{repeat}-tick{cadence}-max{maximum:g}", repeat=repeat,
                             cadence_ms=cadence, max_speech_seconds=maximum,
                             pre_roll_ms=pre_roll, idle_ms=idle))
    return plan


def semantic_flags(clip_id, raw, retained, translations, languages):
    """Suspicion flags, never a translation/ASR rewrite or human verdict."""
    def scan(text):
        if clip_id == RADIATION:
            return dict(radioactivity=bool(re.search(r"радиоактив", text, re.I)),
                        cesium_suspected=bool(re.search(r"(?:цез|циз|ц[еи]с)[а-яё]*", text, re.I)),
                        iodine_suspected=bool(re.search(r"[йи]од[а-яё]*", text, re.I)))
        return dict(pigs=bool(re.search(r"свин", text, re.I)),
                    mosquito_word_suspected=bool(re.search(r"комар[а-яё]*", text, re.I)),
                    person_capitalization_suspected=bool(re.search(r"\bКомаров\b", text)),
                    transmission_relation_suspected=bool(re.search(r"через\s+комар", text, re.I)) and bool(re.search(r"переда[её]|передают|передают[сья]*", text, re.I)),
                    disease_word_suspected=bool(re.search(r"боле[зс]", text, re.I)),
                    human_recipient_suspected=bool(re.search(r"человек|люд", text, re.I)))
    return dict(raw=scan(raw), retained=scan(retained), translation_input=scan(translations),
                non_russian_detected=[r for r in languages if r and r != "ru"],
                semantic_correctness="pending_bilingual_review", word_timestamps="missing; inspect segment WAVs; no inferred word boundaries")


def memory():
    if os.name != "nt":
        import resource
        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (n, ctypes.c_size_t) for n in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage",
                                         "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return int(counters.WorkingSetSize)


def fingerprint():
    paths = subprocess.check_output(["git", "ls-files", "voxgo", "scripts/offline_asr_observer.py", "scripts/offline_russian_capture_ab.py"], cwd=ROOT, text=True).splitlines()
    paths += ["scripts/offline_asr_observer.py", "scripts/offline_russian_capture_ab.py"]
    return dict(head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                files={p: digest((ROOT/p).read_bytes()) for p in sorted(set(paths))},
                python=sys.version, platform=platform.platform(), processor=platform.processor(),
                packages={p: importlib.metadata.version(p) for p in ("faster-whisper", "ctranslate2", "numpy", "webrtcvad-wheels")})


def run_child(args):
    from loguru import logger
    logger.remove()
    import voxgo.asr.pipeline as production_pipeline
    from scripts.offline_asr_observer import Journal, ObservedCapture, ObservedPipeline, ObservedRecognizer, observe_merge, write_wav
    from voxgo.runtime.events import EventBus, TranscriptReady
    from voxgo.translation.base import should_skip_translation_for_language
    spec = json.loads(args.child.read_text(encoding="utf-8"))
    output = create_output(args.output)
    clips, stream, unpadded_frames = load_pcm(args.manifest)
    snapshot, model_files = local_base(args.models_directory)
    config = make_config(args.models_directory, spec["max_speech_seconds"], spec["pre_roll_ms"], spec["idle_ms"])
    initial = dict(audio=asdict(config.audio), whisper=asdict(config.whisper))
    journal = Journal(output, stream, clips)
    sink = logger.add(journal.log, level="DEBUG", enqueue=False)
    samples, sample_stop = [], threading.Event()
    def sample():
        while not sample_stop.wait(.05):
            value = memory()
            samples.append(value)
            row = journal.active_asr_segment
            if row is not None:
                row["peak_sampled_rss_bytes"] = max(value, row.get("peak_sampled_rss_bytes", 0))
    sampler = threading.Thread(target=sample, name="local-memory-sampler", daemon=True)
    sampler.start()
    recognizer = ObservedRecognizer(config.whisper, journal)
    # Pin the already verified local directory; bypass cache lookup entirely.
    recognizer._model_path = str(snapshot)
    pipeline = capture = feeder = None
    cancel_feed, done = threading.Event(), threading.Event()
    result = dict(status="running", spec=spec, scope="paced public read PCM, production Capture/Pipeline/filter; no GUI/game/API",
                  clips=clips, unique_recordings=2, api_requests=0, initial_effective_config=initial,
                  model_snapshot=str(snapshot), model_files=model_files, fingerprint=fingerprint(), human_review="pending")
    cpu_start, run_start = time.process_time(), time.perf_counter()
    try:
        recognizer.initialize()
        # Same whole-clip warmup/order as paired; never forwarded to Pipeline/API.
        warmup = []
        for clip in clips:
            a, b = clip["stream_start_frame"], clip["stream_end_frame"]
            start = time.perf_counter()
            from voxgo.asr.whisper_engine import SpeechRecognizer
            transcript = SpeechRecognizer.transcribe_audio_bytes_with_language(recognizer, stream[a*2:b*2], RATE)
            warmup.append(dict(id=clip["id"], asr=asdict(transcript), elapsed_ms=(time.perf_counter()-start)*1000))
        result["whole_clip_warmup"] = warmup
        stats, traces, bus = defaultdict(int), {}, EventBus()
        counter = iter(range(1, 10000))
        pipeline = ObservedPipeline(lambda: config, lambda: recognizer, bus, stats, lambda: True, lambda: False,
                                    lambda: str(next(counter)), traces, lambda *a: journal.event("notice", value=str(a)),
                                    lambda: 1, journal=journal)
        result["queue_policy"] = asdict(pipeline._mode_policy(config))
        def accepted(event):
            # Same remember + language gate as app._handle_transcript_ready.
            pipeline.remember_transcript(event.text)
            row = journal.segment(journal.current().segment)
            reason = should_skip_translation_for_language(event.text, event.source_lang, event.language,
                                                          event.language_probability, config.translation)
            row.update(retained_text=event.text, translation_input="" if reason else event.text,
                       language_gate_reason=reason or "", status="language_gate_dropped" if reason else "translation_ready")
            journal.event("translation_boundary", segment_id=row["segment_id"], event=asdict(event),
                           skip_reason=reason or "", translation_input=row["translation_input"])
            stats["transcriptions"] += 1
        bus.subscribe(TranscriptReady, accepted)
        capture = ObservedCapture(config.audio, journal)
        def on_segment(segment):
            capture.observe_segment(segment)
            pipeline.on_speech_detected(segment)
        capture.set_speech_callback(on_segment)
        start_clock, replay_cpu = time.perf_counter(), time.process_time()
        def feed():
            try:
                for offset in range(0, len(stream), CHUNK*2):
                    deadline = start_clock + min(offset+CHUNK*2, unpadded_frames*2)/(RATE*2)
                    if cancel_feed.wait(max(0, deadline-time.perf_counter())):
                        return
                    capture.feed(stream[offset:offset+CHUNK*2], offset//2, (offset+CHUNK*2)//2, deadline)
            finally:
                done.set()
        pipeline.start()
        feeder = threading.Thread(target=feed, name="fixed-PCM-feeder", daemon=True)
        feeder.start()
        ticks, quiet, pending = [], None, True
        deadline = start_clock + unpadded_frames/RATE + args.drain_seconds
        next_tick = start_clock
        with patch.object(production_pipeline, "merge_speech_work_items", observe_merge(journal, production_pipeline.merge_speech_work_items)):
            while time.perf_counter() < deadline:
                ticks.append(time.perf_counter()-start_clock)
                capture.process_audio()
                pending = (not pipeline._queue.empty() or pipeline._recognition_busy or pipeline._pending_buffer.has_pending()
                           or pipeline._busy_weak_buffer.has_pending() or bool(capture._speech_buffer) or not capture._audio_queue.empty())
                if done.is_set() and not pending:
                    quiet = quiet or time.perf_counter()
                    if time.perf_counter()-quiet >= 1.:
                        break
                else:
                    quiet = None
                # Like the paired tool: delay after processing. This is a paced
                # main-loop simulation, not QTimer or a real loopback/GUI test.
                next_tick = time.perf_counter()+spec["cadence_ms"]/1000
                time.sleep(max(0, next_tick-time.perf_counter()))
        result.update(drain_complete=not pending, replay_wall_seconds=time.perf_counter()-start_clock,
                      replay_cpu_seconds=time.process_time()-replay_cpu,
                      actual_process_tick_intervals_ms=[(b-a)*1000 for a,b in zip(ticks,ticks[1:])],
                      replay_stream_sha256=digest(stream), unpadded_stream_frames=unpadded_frames,
                      padded_stream_frames=len(stream)//2, stats=dict(stats))
        result["status"] = "complete" if not pending else "incomplete_drain"
    finally:
        cancel_feed.set()
        if feeder:
            feeder.join(3)
        if pipeline:
            # Record cancellation targets BEFORE stop() drains its queue.
            for item in list(pipeline._queue.queue):
                row = journal.item(item)
                if row:
                    row["status"] = "cancelled_at_shutdown"
                    journal.event("cancelled_at_shutdown", item_id=row["item_id"])
            for buffer in (pipeline._pending_buffer, pipeline._busy_weak_buffer):
                if buffer.pending:
                    row = journal.item(buffer.pending)
                    journal.event("pending_at_shutdown", item_id=row["item_id"])
            result["worker_stopped"] = pipeline.stop()
        if capture:
            result["capture_buffer_frames_at_shutdown"] = capture._speech_buffer_samples
            capture._audio.terminate()
        if not pipeline or result.get("worker_stopped"):
            recognizer.cleanup()
        sample_stop.set()
        sampler.join(3)
        for key, item in journal.items.items():
            if item["status"] not in {"cancelled_at_shutdown", "merged_into"}:
                item["status"] = journal.segment(journal.refs[key].segment)["status"]
        result.update(feeder_stopped=not feeder or not feeder.is_alive(), sampler_stopped=not sampler.is_alive(),
                      peak_sampled_rss_bytes=max(samples, default=memory()),
                      total_process_cpu_seconds=time.process_time()-cpu_start, total_wall_seconds=time.perf_counter()-run_start,
                      segments=list(journal.segments.values()), work_items=list(journal.items.values()), activity_windows=journal.windows,
                      config_unchanged=initial == dict(audio=asdict(config.audio), whisper=asdict(config.whisper)))
        result["per_clip"] = per_clip(result)
        write(output/"result.json", result)
        journal.event("shutdown", status=result["status"], worker_stopped=result.get("worker_stopped"),
                      feeder_stopped=result["feeder_stopped"], sampler_stopped=result["sampler_stopped"])
        journal.handle.close()
        logger.remove(sink)
    if result["status"] != "complete" or not result["worker_stopped"] or not result["config_unchanged"] or stats["errors"]:
        raise RuntimeError("Offline replay did not finish cleanly; retained local evidence")


def per_clip(result):
    out = []
    for clip in result["clips"]:
        rows = [r for r in result["segments"] if any(s["id"] == clip["id"] for s in r["sources"])]
        asr = [r for r in rows if "asr" in r]
        raw = " ".join(r["asr"].get("raw_text", r["asr"]["text"]) for r in asr)
        retained = " ".join(r.get("retained_text", "") for r in asr).strip()
        translations = " ".join(r.get("translation_input", "") for r in asr).strip()
        captured = [r for r in rows if r["captured"]]
        ranges = [s for r in captured for s in r["sources"] if s["id"] == clip["id"]]
        coverage = [0] * (clip["stream_end_frame"]-clip["stream_start_frame"])
        for s in ranges:
            for frame in range(s["wav_start_frame"], s["wav_end_frame"]):
                coverage[frame] += 1
        gaps = []
        for left, right in zip(captured, captured[1:]):
            gaps.append(right["spans"][0][0]-left["spans"][-1][1])
        out.append(dict(id=clip["id"], reference=clip["reference_text"], raw=raw, retained=retained,
                        translation_input=translations, segment_ids=[r["segment_id"] for r in rows],
                        flags=semantic_flags(clip["id"], raw, retained, translations, [r["asr"]["language"] for r in asr]),
                        captured_segments=len(captured), whisper_calls=len(asr),
                        language_filter_drops=[r["segment_id"] for r in rows if re.search(r"language|语言",r.get("filter_reason", "")) or r.get("language_gate_reason")],
                        boundary_deltas_frames=gaps, duplicate_capture_frames=sum(v>1 for v in coverage),
                        not_captured_frames=sum(v==0 for v in coverage),
                        missing_frame_note="Uncaptured leading/trailing silence is not automatically a semantic omission; see activity windows/WAVs",
                        asr_ms=[r["asr_ms"] for r in asr], asr_cpu_seconds=sum(r["asr_process_cpu_seconds"] for r in asr)))
    return out


def original_hashes(manifest):
    roots = [manifest.parent, ROOT/"docs/testing/evidence/v0.5.3-paired-speech-2026-10-27"]
    files = [p for root in roots for p in root.rglob("*") if p.is_file()]
    files += [p for p in (ROOT/"user_settings.json", ROOT/"telemetry_consent.json") if p.is_file()]
    return {str(p): digest(p.read_bytes()) for p in files}


def summarize(output, plan):
    results = [json.loads((output/s["id"]/"result.json").read_text(encoding="utf-8")) for s in plan]
    comparisons = []
    for spec in plan:
        if spec["repeat"] != 1:
            continue
        same = [r for r in results if all(r["spec"][k] == spec[k] for k in ("cadence_ms", "max_speech_seconds", "pre_roll_ms", "idle_ms"))]
        def stable(r):
            return [(s["spans"], s.get("asr",{}),
                     s.get("translation_input", ""), s.get("filter_reason", "")) for s in r["segments"]]
        comparisons.append(dict(cadence_ms=spec["cadence_ms"], maximum=spec["max_speech_seconds"],
                                repetitions=len(same), identical_boundaries_text_filters=all(stable(r)==stable(same[0]) for r in same)))
    summary = dict(api_requests=0, unique_recordings=2, recording_replays=len(results)*2,
                   independent_validation=False, human_review="pending", release_approved=False,
                   repeats=comparisons, rows=[dict(spec=r["spec"], per_clip=r["per_clip"],
                   replay_cpu_seconds=r["replay_cpu_seconds"], peak_rss_mib=r["peak_sampled_rss_bytes"]/2**20,
                   replay_wall_seconds=r["replay_wall_seconds"], stats=r["stats"], drain_complete=r["drain_complete"]) for r in results])
    write(output/"summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--models-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-speech-seconds", nargs="+", type=float, default=[4.5, 3., 3.5, 4.])
    parser.add_argument("--cadence-ms", nargs="+", type=int, default=[5, 100])
    parser.add_argument("--pre-roll-ms", type=int, default=450)
    parser.add_argument("--idle-ms", type=int, default=450)
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--drain-seconds", type=float, default=30.)
    parser.add_argument("--child", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    validate_output(args.output, args.manifest, args.models_directory)
    if any(not .5 <= v <= 15 for v in args.max_speech_seconds) or any(not 1 <= v <= 1000 for v in args.cadence_ms):
        parser.error("invalid capture duration/cadence")
    if not 1 <= args.rounds <= 4 or not 0 <= args.pre_roll_ms <= 2000 or not 1 <= args.idle_ms <= 2000:
        parser.error("invalid repetitions/pre-roll/idle")
    if not 1 <= args.drain_seconds <= 120:
        parser.error("invalid drain timeout")
    with offline_guard() as safety:
        if args.child:
            run_child(args)
            write(args.output/"safety.json", {k:v for k,v in safety.items() if k != "active"})
            return
        # Preflight before creating any run: hashes and model must already exist.
        clips, stream, frames = load_pcm(args.manifest)
        snapshot, model = local_base(args.models_directory)
        before = original_hashes(args.manifest)
        source_before = fingerprint()
        output = create_output(args.output)
        plan = schedule(args.max_speech_seconds, args.cadence_ms, args.pre_roll_ms, args.idle_ms, args.rounds)
        write(output/"plan.json", dict(schedule=plan, clips=clips, model_snapshot=str(snapshot), model_files=model,
                                      pcm_sha256=digest(stream), unpadded_frames=frames, fingerprint=source_before,
                                      scope="Known public read speech; 2 independent recordings; no game/release acceptance",
                                      requested_cadence="sleep after process_audio; real monotonic clock, production worker; not real QTimer"))
        status = dict(status="running", completed=[], api_requests=0)
        write(output/"status.json", status)
        try:
            for spec in plan:
                spec_file = output/(spec["id"]+".json")
                write(spec_file, spec)
                print("Starting "+spec["id"], flush=True)
                with (output/(spec["id"]+".log")).open("x", encoding="utf-8") as log:
                    child = subprocess.run([sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()),
                                            "--manifest", str(args.manifest.resolve()), "--models-directory", str(args.models_directory.resolve()),
                                            "--output", str((output/spec["id"]).resolve()), "--drain-seconds", str(args.drain_seconds),
                                            "--child", str(spec_file.resolve())], cwd=ROOT, stdout=log, stderr=log,
                                           timeout=frames/RATE+args.drain_seconds+120)
                if child.returncode:
                    raise RuntimeError("Child failed; stop all arms without selective retry: "+spec["id"])
                status["completed"].append(spec["id"])
                write(output/"status.json", status)
                print(f"Completed {len(status['completed'])}/{len(plan)}", flush=True)
            summarize(output, plan)
            status["status"] = "complete"
        finally:
            status.update(original_evidence_and_settings_unchanged=before == original_hashes(args.manifest),
                          source_files_unchanged=source_before["files"] == fingerprint()["files"],
                          safety={k:v for k,v in safety.items() if k != "active"})
            if status["status"] == "running":
                status["status"] = "stopped_incomplete"
            write(output/"status.json", status)


if __name__ == "__main__":
    main()
