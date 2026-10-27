"""Four bounded zero-network runs of the saved RU tail: direct A / idle Pipeline B.

No recutting, warmup audio, decoder search, translation, or production changes.
"""
import argparse
from collections import defaultdict
import copy
from dataclasses import asdict, fields
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.offline_russian_capture_ab import (
    MOSQUITO, RATE, create_output, digest, fingerprint, load_pcm, local_base,
    make_config, memory, offline_guard, write,
)

STREAM_SPAN = [293760, 307200]
WAV_SPAN = [98560, 112000]
PCM_SHA = "5eae1b016d16a547fd91129fd379f44613f493c1a2d980f829bcdfb4b6ac5459"
INDEX = ROOT / "docs/testing/evidence/v0.5.3-ru-capture-ab-2026-10-27/artifact-index.json"
MANIFEST = ROOT / "build/multilingual-online/paired-live-2026-10-27/manifest.json"


def load_tail(source_run, index_path=INDEX):
    """Decode ONLY the saved WAV; independently verify provenance and padding."""
    result_path = source_run / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    row = next(s for s in result["segments"] if s["spans"] == [STREAM_SPAN])
    path = source_run / (row["segment_id"] + ".wav")
    index = {Path(p["path"]).resolve(): p for p in json.loads(index_path.read_text(encoding="utf-8"))}
    for file in (result_path, path):
        if file.resolve() not in index or digest(file.read_bytes()) != index[file.resolve()]["sha256"]:
            raise ValueError("Saved experiment artifact SHA256 mismatch")
    with wave.open(str(path), "rb") as audio:
        if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate(), audio.getnframes(), audio.getcomptype()) != (1, 2, RATE, 13440, "NONE"):
            raise ValueError("Saved tail WAV format/frame mismatch")
        pcm = audio.readframes(audio.getnframes())
    if digest(pcm) != PCM_SHA or digest(pcm) != row["pcm_sha256"]:
        raise ValueError("Tail PCM SHA256 mismatch")
    if row["voice_duration_seconds"] != .36 or row.get("filter_reason") != "asr_budget_weak_drop":
        raise ValueError("Unexpected original capture metadata")
    origin = row["sources"]
    if len(origin) != 1 or origin[0]["id"] != MOSQUITO or [origin[0]["wav_start_frame"], origin[0]["wav_end_frame"]] != WAV_SPAN:
        raise ValueError("Tail source frame mismatch")
    clip = next(c for c in result["clips"] if c["id"] == MOSQUITO)
    original = Path(clip["audio"])
    if digest(original.read_bytes()) != clip["sha256"]:
        raise ValueError("Original WAV SHA256 mismatch")
    with wave.open(str(original), "rb") as audio:
        if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (1, 2, RATE) or audio.getnframes() < WAV_SPAN[1]:
            raise ValueError("Original source format/range mismatch")
        audio.setpos(WAV_SPAN[0])
        if audio.readframes(13440) != pcm:
            raise ValueError("Saved tail differs from original WAV interval")
    # This comparison verifies the stream mapping; inference still uses saved pcm.
    clips, stream, _ = load_pcm(MANIFEST)
    if digest(stream) != result["replay_stream_sha256"] or stream[STREAM_SPAN[0]*2:STREAM_SPAN[1]*2] != pcm:
        raise ValueError("Original replay stream mismatch")
    provenance = dict(saved_wav=str(path.resolve()), wav_sha256=digest(path.read_bytes()), pcm_sha256=digest(pcm),
                      original_wav=str(original.resolve()), original_wav_sha256=clip["sha256"],
                      source_result_sha256=digest(result_path.read_bytes()), stream_span=STREAM_SPAN, wav_span=WAV_SPAN,
                      sample_rate=RATE, frames=13440, seconds=.84, replay_padding_frames=0,
                      padding_note="Entire span lies inside the original WAV. Natural silence/zero samples retained unchanged.",
                      inference_input="saved WAV PCM, not reconstructed/resegmented input")
    return pcm, row, result, clips, stream, provenance


class CachedResultRecognizer:
    """Replay an actual A result through production _process; never infer twice."""
    def __init__(self, recognizer, result):
        self.recognizer, self.result, self.calls = recognizer, result, 0

    def __getattr__(self, name):
        return getattr(self.recognizer, name)

    def transcribe_audio_bytes_with_language(self, *args, **kwargs):
        self.calls += 1
        if self.calls != 1:
            raise RuntimeError("Unexpected second cached result consumption")
        return self.result


def recipient_flags(asr, retained, translated_input):
    hit = lambda text: bool(re.search(r"человек[а-яё]*|люд[а-яё]*", text, re.I))
    return dict(raw_recipient_suspected=hit(asr.get("raw_text", "")),
                retained_recipient_suspected=hit(retained), translation_recipient_suspected=hit(translated_input),
                non_russian_suspected=bool(asr.get("raw_text", "").strip() and asr.get("language") != "ru"),
                runaway_guarded=asr.get("runaway_guarded", False), human_semantic_review="pending")


def direct_then_filter(pipeline, recognizer, item, holder, journal):
    """Direct official recognition, then official filters on its unchanged result."""
    pre_reason = pipeline._weak_pre_whisper_drop_reason(item, pipeline._mode_policy(pipeline._config_getter()))
    journal.local.item = item
    try:
        result = recognizer.transcribe_audio_bytes_with_language(item.segment.audio_data, RATE,
            language_override=item.whisper_language, config_override=item.whisper_config_snapshot)
    finally:
        journal.local.item = None
    holder[0] = CachedResultRecognizer(recognizer, result)
    pipeline._process(item)  # Actual production filter ordering, no admission budget.
    return dict(weak_pre_check=pre_reason, cached_result_consumptions=holder[0].calls,
                note="_process trace ASR time is cached-result delivery, not inference timing; use segment.asr_ms")


def run_idle(pipeline, segment, journal, timeout=12.):
    before = dict(last_transcription_finished_at=pipeline._last_transcription_finished_at,
                  recognition_busy=pipeline._recognition_busy, queue_depth=pipeline._queue.qsize(),
                  recent_transcripts=list(pipeline._recent_transcripts), pending=pipeline._pending_buffer.has_pending())
    if before["last_transcription_finished_at"] or before["recognition_busy"] or before["queue_depth"] or before["recent_transcripts"] or before["pending"]:
        raise ValueError("Pipeline must be naturally fresh/idle; no state reset allowed")
    pipeline.start()
    pipeline.on_speech_detected(segment)
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        row = journal.segment(segment)
        idle = (not pipeline._recognition_busy and pipeline._queue.empty()
                and not pipeline._pending_buffer.has_pending() and not pipeline._busy_weak_buffer.has_pending())
        if idle and row["status"] in {"dropped", "translation_ready", "language_gate_dropped"}:
            return dict(initial_state=before, completed=True)
        time.sleep(.01)
    return dict(initial_state=before, completed=False)


def run_child(args, safety):
    from loguru import logger
    logger.remove()
    from scripts.offline_asr_observer import Journal, ObservedPipeline, ObservedRecognizer
    from voxgo.audio.capture import SpeechSegment
    from voxgo.runtime.events import EventBus, TranscriptReady
    from voxgo.runtime.work_items import SpeechWorkItem
    from voxgo.translation.base import should_skip_translation_for_language
    output = create_output(args.output)
    pcm, row, previous, clips, stream, provenance = load_tail(args.source_run)
    snapshot, model_files = local_base(args.models_directory)
    config = make_config(args.models_directory, 3., 450, 450)
    initial = dict(audio=asdict(config.audio), whisper=asdict(config.whisper))
    if initial != previous["initial_effective_config"]:
        raise ValueError("Configuration differs from the actual 3.0s source run")
    segment = SpeechSegment(audio_data=pcm, **{f.name: row[f.name] for f in fields(SpeechSegment) if f.name != "audio_data"})
    journal = Journal(output, stream, clips)
    journal.segment(segment, [STREAM_SPAN])
    sink = logger.add(journal.log, level="DEBUG", enqueue=False)
    recognizer = ObservedRecognizer(copy.deepcopy(config.whisper), journal)
    recognizer._model_path = str(snapshot)
    holder, stats, traces, bus = [recognizer], defaultdict(int), {}, EventBus()
    pipeline = ObservedPipeline(lambda:config, lambda:holder[0], bus, stats, lambda:True, lambda:False,
                                lambda:"tail", traces, lambda *a:journal.event("notice", message=str(a)), lambda:1, journal=journal)
    def accepted(event):
        pipeline.remember_transcript(event.text)
        observed = journal.segment(segment)
        reason = should_skip_translation_for_language(event.text, event.source_lang, event.language,
                                                      event.language_probability, config.translation)
        observed.update(retained_text=event.text, translation_input="" if reason else event.text,
                        language_gate_reason=reason or "", status="language_gate_dropped" if reason else "translation_ready")
        journal.event("translation_boundary", text=event.text, skip_reason=reason or "")
    bus.subscribe(TranscriptReady, accepted)
    cpu, started, baseline_rss = time.process_time(), time.perf_counter(), memory()
    samples, stop = [], threading.Event()
    def sample():
        while not stop.wait(.02):
            rss = memory()
            samples.append(rss)
            active = journal.active_asr_segment
            if active is not None:
                active["peak_sampled_rss_bytes"] = max(rss, active.get("peak_sampled_rss_bytes", 0))
    sampler = threading.Thread(target=sample, daemon=True, name="local-memory-sampler")
    sampler.start()
    result = dict(experiment=args.child, provenance=provenance, api_requests=0, actual_config=initial,
                  fingerprint=fingerprint(), tool_sha256=digest(Path(__file__).read_bytes()),
                  model_snapshot=str(snapshot), model_files=model_files, human_review="pending", warmup_calls=0)
    try:
        recognizer.initialize()
        result["model_loaded_rss_bytes"] = memory()
        decision = pipeline._candidate_policy.classify(segment, config.audio)
        result["candidate"] = asdict(decision)
        if args.child == "A":
            now = time.time()
            item = SpeechWorkItem(segment, pipeline._make_latency_trace(now, config), candidate_labels=decision.labels,
                                  candidate_reason=decision.reason, low_confidence=decision.low_confidence,
                                  short_segment=decision.short_segment)
            pipeline._apply_language_snapshot(item, config)
            result["execution"] = direct_then_filter(pipeline, recognizer, item, holder, journal)
        else:
            result["execution"] = run_idle(pipeline, segment, journal)
            if not result["execution"]["completed"]:
                raise RuntimeError("Idle Pipeline did not drain; stop without retries")
        result["status"] = "complete"
    finally:
        result["worker_stopped"] = pipeline.stop() if pipeline._worker_thread is not None else True
        if result["worker_stopped"]:
            recognizer.cleanup()
        stop.set()
        sampler.join(3)
        observed = journal.segment(segment)
        result.update(segment=observed, work_items=list(journal.items.values()), stats=dict(stats),
                      api_requests=0, queue_empty=pipeline._queue.empty(),
                      pending_empty=not pipeline._pending_buffer.has_pending() and not pipeline._busy_weak_buffer.has_pending(),
                      total_cpu_seconds=time.process_time()-cpu, total_wall_seconds=time.perf_counter()-started,
                      baseline_rss_bytes=baseline_rss, final_rss_bytes=memory(), peak_sampled_rss_bytes=max(samples, default=memory()),
                      sampler_stopped=not sampler.is_alive(), safety={k:v for k,v in safety.items() if k!="active"},
                      config_unchanged=initial == dict(audio=asdict(config.audio), whisper=asdict(config.whisper)))
        result["flags"] = recipient_flags(observed.get("asr",{}), observed.get("retained_text",""), observed.get("translation_input",""))
        journal.event("shutdown", worker_stopped=result["worker_stopped"], queue_empty=result["queue_empty"], pending_empty=result["pending_empty"])
        write(output/"result.json", result)
        logger.remove(sink)
        journal.handle.close()
    if not result["worker_stopped"] or not result["config_unchanged"] or stats["errors"]:
        raise RuntimeError("Diagnostic did not finish cleanly")


def protected_hashes(source_run):
    roots = [source_run.parent, INDEX.parent, MANIFEST.parent,
             ROOT/"docs/testing/evidence/v0.5.3-paired-speech-2026-10-27"]
    return {str(p):digest(p.read_bytes()) for root in roots for p in root.rglob("*") if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--models-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--child", choices=["A","B"], help=argparse.SUPPRESS)
    args = parser.parse_args()
    protected = [args.source_run.parent, args.models_directory, INDEX.parent, MANIFEST.parent, ROOT/"voxgo"]
    if any(args.output.resolve().is_relative_to(p.resolve()) for p in protected):
        parser.error("Output must be a new directory outside inputs/model/runtime")
    with offline_guard() as safety:
        if args.child:
            run_child(args, safety)
            return
        load_tail(args.source_run)
        _, model_files = local_base(args.models_directory)
        before, source = protected_hashes(args.source_run), fingerprint()
        output = create_output(args.output)
        schedule = [("r1-A","A"),("r1-B","B"),("r2-B","B"),("r2-A","A")]
        status = dict(status="running", completed=[], api_requests=0)
        write(output/"plan.json",dict(schedule=schedule, unique_recordings=1, model_files=model_files,
                                      source_run=str(args.source_run.resolve()), scope="Exact saved PCM only, no warmup/context/decoder changes"))
        try:
            for name, arm in schedule:
                print("Starting "+name, flush=True)
                with (output/(name+".log")).open("x",encoding="utf-8") as log:
                    child = subprocess.run([sys.executable,"-B","-X","utf8",str(Path(__file__).resolve()),
                        "--source-run",str(args.source_run.resolve()),"--models-directory",str(args.models_directory.resolve()),
                        "--output",str((output/name).resolve()),"--child",arm],cwd=ROOT,stdout=log,stderr=log,timeout=60)
                if child.returncode:
                    raise RuntimeError("Diagnostic child failed; stop without selective retries: "+name)
                status["completed"].append(name)
                write(output/"status.json",status)
            rows = [json.loads((output/name/"result.json").read_text(encoding="utf-8")) for name,_ in schedule]
            signature = lambda r: (r["segment"].get("asr"),r["segment"].get("filter_reason"),r["segment"].get("translation_input",""))
            write(output/"summary.json",dict(api_requests=0, runs=4, unique_recordings=1,
                all_outputs_filters_identical=all(signature(r)==signature(rows[0]) for r in rows),
                rows=[dict(run=name,**r) for (name,_),r in zip(schedule,rows)],release_approved=False))
            status["status"] = "complete"
        finally:
            status.update(original_evidence_unchanged=before == protected_hashes(args.source_run),
                          runtime_and_existing_tools_unchanged=source["files"] == fingerprint()["files"],
                          models_unchanged=model_files == local_base(args.models_directory)[1],
                          safety={k:v for k,v in safety.items() if k!="active"})
            if status["status"]=="running":
                status["status"]="stopped_incomplete"
            write(output/"status.json",status)


if __name__ == "__main__":
    main()
