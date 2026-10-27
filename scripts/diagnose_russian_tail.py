"""Four bounded zero-network runs of the saved RU tail: direct A / idle Pipeline B.

No recutting, warmup audio, decoder search, translation, or production changes.
"""
import argparse
from collections import defaultdict
import copy
from dataclasses import asdict, fields
import difflib
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


def metadata_from_windows(pcm, windows, reason, noise_floor, latency_mode):
    """Aggregate official capture decisions, not a second activity classifier."""
    from voxgo.audio.capture import SpeechSegment
    if not windows or sum(b-a for w in windows for a,b in w["spans"])*2 != len(pcm):
        raise ValueError("Activity windows do not exactly cover the diagnostic PCM")
    voice = [w for w in windows if w["accepted_activity"] and w["vad_speech"]]
    energy = [w for w in windows if w["accepted_activity"] and not w["vad_speech"] and w["energy_activity"]]
    active = [w for w in windows if w["accepted_activity"]]
    if not active or len({w["energy_threshold_dbfs"] for w in windows}) != 1:
        raise ValueError("Cannot faithfully aggregate active windows / changing gate")
    return SpeechSegment(audio_data=pcm, sample_rate=RATE, duration_seconds=len(pcm)/(RATE*2),
        voice_duration_seconds=sum(b-a for w in voice for a,b in w["spans"])/RATE,
        block_count=len(windows), voice_blocks=len(voice), peak_rms_dbfs=max(w["rms_dbfs"] for w in active),
        energy_threshold_dbfs=windows[-1]["energy_threshold_dbfs"], noise_floor_dbfs=noise_floor, reason=reason,
        vad_voice_blocks=len(voice), energy_voice_blocks=len(energy), vad_confidence=len(voice)/len(windows),
        activity_source="vad" if voice else "energy", latency_mode=latency_mode)


def context_pcm(tail, original_path, stream, arm):
    if arm not in {"A","B"}:
        raise ValueError("Only the fixed A/B context inputs are allowed")
    prefix=7680 if arm=="B" else 0
    start,wav_start=STREAM_SPAN[0]-prefix,WAV_SPAN[0]-prefix
    with wave.open(str(original_path),"rb") as audio:
        if (audio.getnchannels(),audio.getsampwidth(),audio.getframerate())!=(1,2,RATE):
            raise ValueError("Context source must be original mono PCM16 16kHz")
        audio.setpos(wav_start)
        data=audio.readframes(WAV_SPAN[1]-wav_start)
    if len(data)!=(13440+prefix)*2 or data[-len(tail):]!=tail or data!=stream[start*2:STREAM_SPAN[1]*2]:
        raise ValueError("Context input changed the saved tail / stream mapping")
    return tail if arm=="A" else data,[start,STREAM_SPAN[1]],[wav_start,WAV_SPAN[1]]


def context_input(tail, row, previous, clips, stream, config, arm, output):
    """Exact 0/.48s input plus metadata witnessed in a production capture replay.

    Full original stream is used only to restore capture/VAD state, never ASR.
    B is a diagnostic prefix union, NOT a segment emitted by current capture.
    """
    from scripts.offline_asr_observer import Journal, ObservedCapture
    from voxgo.audio.capture import SpeechSegment
    output.mkdir(exist_ok=False)
    class ActivityCapture(ObservedCapture):
        def _should_force_split(self):
            self.journal.windows[-1]["accepted_activity"] = True
            return super()._should_force_split()
    with Journal(output, stream, clips) as journal:
        capture = ActivityCapture(copy.deepcopy(config.audio), journal)
        capture.set_speech_callback(capture.observe_segment)
        try:
            for offset in range(0,len(stream),1920*2):
                capture.feed(stream[offset:offset+1920*2],offset//2,(offset+1920*2)//2,time.perf_counter())
                capture.process_audio()
            for w in journal.windows:
                w.setdefault("accepted_activity",False)
            # Strict reproduction prevents silently substituting a new VAD state.
            def signature(rows):
                names=[f.name for f in fields(SpeechSegment) if f.name!="audio_data"]
                return [(s["spans"],s["pcm_sha256"],{k:s[k] for k in names}) for s in rows]
            if signature(list(journal.segments.values())) != signature([s for s in previous["segments"] if s["captured"]]):
                raise ValueError("Capture replay differs from source; no Pipeline success claim permitted")
            windows=copy.deepcopy(journal.windows)
        finally:
            capture._audio.terminate()
    def select(start,end):
        chosen=[w for w in windows if w["spans"][0][0]>=start and w["spans"][-1][1]<=end]
        spans=[span for w in chosen for span in w["spans"]]
        if not spans or spans[0][0]!=start or spans[-1][1]!=end or any(a[1]!=b[0] for a,b in zip(spans,spans[1:])):
            raise ValueError("Missing / overlapping capture windows")
        return chosen
    original=metadata_from_windows(tail,select(*STREAM_SPAN),row["reason"],row["noise_floor_dbfs"],row["latency_mode"])
    if any(getattr(original,f.name)!=row[f.name] for f in fields(original) if f.name!="audio_data"):
        raise ValueError("Derived A metadata does not match original tail")
    clip=next(c for c in clips if c["id"]==MOSQUITO)
    data,span,wav_span=context_pcm(tail,clip["audio"],stream,arm)
    selected=select(*span)
    segment=metadata_from_windows(data,selected,row["reason"] if arm=="A" else "diagnostic_context_prefix_0.48s",
                                 row["noise_floor_dbfs"],row["latency_mode"])
    return segment, span, dict(arm=arm, pcm_sha256=digest(data), frames=len(data)//2,
        wav_span=wav_span,stream_span=span,prefix_frames=7680 if arm=="B" else 0,
        tail_unchanged=True,source_capture_exactly_reproduced=True,actual_windows=selected,
        metadata_scope="Original capture decisions aggregated for exact PCM. B prefix union is diagnostic, not emitted by current capture.",
        previous_raw=next(s["asr"]["raw_text"] for s in previous["segments"] if s["spans"]==[[245760,293760]]))


def overlap_review(previous, current):
    """Evaluation-only text alignment; never repair or deduplicate ASR output."""
    tokenize=lambda text: re.findall(r"[а-яё]+",text.casefold())
    left,right=tokenize(previous),tokenize(current)
    exact=0
    for n in range(1,min(len(left),len(right))+1):
        if left[-n:]==right[:n]:
            exact=n
    pairs=[dict(previous_index=i,current_index=j,previous_token=left[i],current_token=right[j],
                similarity=difflib.SequenceMatcher(None,left[i],right[j]).ratio())
           for i in range(max(0,len(left)-4),len(left)) for j in range(min(4,len(right)))
           if min(len(left[i]),len(right[j]))>=4 and difflib.SequenceMatcher(None,left[i],right[j]).ratio()>=.70]
    return dict(previous_raw=previous,current_raw=current,unaltered_concatenation=previous+" "+current,
                exact_suffix_prefix_tokens=exact,fuzzy_boundary_pairs=pairs,
                verdict="auxiliary alignment only; semantic conflict/repetition requires review",text_modified=False)


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
    context_mode=getattr(args,"context_ab",False)
    if context_mode:
        segment, spans, context = context_input(pcm,row,previous,clips,stream,config,args.child,output/"capture-metadata")
        provenance=dict(source_tail=provenance,context_input=context,pcm_sha256=context["pcm_sha256"],
            inference_input="original saved tail A" if args.child=="A" else "NEW 0.48s original-WAV acoustic prefix plus unchanged saved tail; diagnostic context B")
    else:
        segment = SpeechSegment(audio_data=pcm, **{f.name: row[f.name] for f in fields(SpeechSegment) if f.name != "audio_data"})
        spans=STREAM_SPAN
    journal = Journal(output, stream, clips)
    journal.segment(segment, [spans])
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
        if args.child == "A" and not context_mode:
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
        if context_mode:
            result["context_mode"] = True
            result["overlap_review"] = overlap_review(context["previous_raw"],observed.get("asr",{}).get("raw_text",""))
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
    parser.add_argument("--context-ab",action="store_true",help="Fixed 0/.48s acoustic prefix experiment; both arms use idle Pipeline")
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
        if args.context_ab:
            previous_diagnostic=ROOT/"docs/testing/evidence/v0.5.3-ru-tail-diagnostic-2026-10-27"
            before.update({str(p):digest(p.read_bytes()) for p in previous_diagnostic.rglob("*") if p.is_file()})
        output = create_output(args.output)
        schedule = [("r1-A","A"),("r1-B","B"),("r2-B","B"),("r2-A","A")]
        status = dict(status="running", completed=[], api_requests=0)
        write(output/"plan.json",dict(schedule=schedule, unique_recordings=1, model_files=model_files,
                                      source_run=str(args.source_run.resolve()),
                                      scope="Fixed 0/.48s context, idle Pipeline; no decoder/filter changes" if args.context_ab else "Exact saved PCM only, no warmup/context/decoder changes"))
        try:
            for name, arm in schedule:
                print("Starting "+name, flush=True)
                with (output/(name+".log")).open("x",encoding="utf-8") as log:
                    command=[sys.executable,"-B","-X","utf8",str(Path(__file__).resolve()),
                        "--source-run",str(args.source_run.resolve()),"--models-directory",str(args.models_directory.resolve()),
                        "--output",str((output/name).resolve()),"--child",arm]
                    if args.context_ab:
                        command.append("--context-ab")
                    child = subprocess.run(command,cwd=ROOT,stdout=log,stderr=log,timeout=60)
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
            status.update(original_evidence_unchanged=all(Path(p).is_file() and digest(Path(p).read_bytes())==h for p,h in before.items()),
                          runtime_and_existing_tools_unchanged=source["files"] == fingerprint()["files"],
                          models_unchanged=model_files == local_base(args.models_directory)[1],
                          safety={k:v for k,v in safety.items() if k!="active"})
            if status["status"]=="running":
                status["status"]="stopped_incomplete"
            write(output/"status.json",status)


if __name__ == "__main__":
    main()
