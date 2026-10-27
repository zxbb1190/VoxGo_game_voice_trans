"""Versioned, zero-inference review of immutable RU baseline raw events.

Use event order (not capture dictionary insertion order), separate the app language
gate from ASR filters, and export unfilled human segment review forms. No model
loads, new PCM, reference repair, or inference retries.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.offline_russian_capture_ab import create_output,offline_guard,write
from scripts.ru_benchmark_metrics import assess
from scripts.run_ru_continuous_baseline import summarize


def coverage(spans,start,end):
    intervals=sorted((max(a,start),min(b,end)) for a,b in spans if a<end and b>start)
    cursor=start;gaps=[];overlap=0
    for a,b in intervals:
        if a>cursor:gaps.append([cursor,a])
        if a<cursor:overlap+=max(0,min(cursor,b)-a)
        cursor=max(cursor,b)
    if cursor<end:gaps.append([cursor,end])
    return dict(uncovered_source_intervals=gaps,uncovered_source_frames=sum(b-a for a,b in gaps),
                duplicate_frame_occurrences=overlap,
                note="Silence/VAD inactivity often causes legitimate uncovered frames; not a semantic loss verdict")


def reviewed_assessment(result,record,events):
    compiled=copy.deepcopy(result)
    by_id={s["segment_id"]:s for s in result["segments"]}
    actual_order=[e["segment_id"] for e in events if e["kind"]=="whisper_end"]
    # This preserves actual Whisper order. It does NOT reorder text chronologically.
    completed=[by_id[sid] for sid in actual_order if "asr" in by_id[sid]]
    compiled["segments"]=completed+[s for s in result["segments"] if "asr" not in s]
    assessment=assess(compiled,record,events)
    assessment["analysis_version"]=2
    assessment["alignment"]["inference_segment_order"]=actual_order
    assessment["alignment"]["method"]="one full source; actual whisper_end event order; suppress CER/WER on overlapping, duplicated or reordered PCM; no per-segment gold"
    clip=result["clips"][0];start,end=clip["stream_start_frame"],clip["stream_end_frame"]
    cap_spans=[span for s in result["segments"] if s["captured"] for span in s["spans"]]
    asr_spans=[span for s in completed for span in s["spans"]]
    cap_coverage=coverage(cap_spans,start,end);asr_coverage=coverage(asr_spans,start,end)
    assessment["alignment"].update(capture_source_coverage=cap_coverage,asr_source_coverage=asr_coverage,
        capture_gap_intervals=cap_coverage["uncovered_source_intervals"],
        capture_only_silence_emissions=[s["segment_id"] for s in completed if not s["sources"]])
    gates=[s for s in result["segments"] if s["status"]=="language_gate_dropped"]
    assessment["counts"]["translation_language_gate_drops"]=len(gates)
    assessment["counts"]["captured"]=sum(s["captured"] for s in result["segments"])
    assessment["counts"]["all_post_inference_rejections"]=assessment["counts"]["post_asr_drops"]+len(gates)
    assessment["counts"]["budget_pre_asr_drops"]=sum(s.get("filter_reason")=="asr_budget_weak_drop" for s in result["segments"])
    assessment["counts"]["forced_capture_cuts"]=sum(s["captured"] and str(s["reason"]).startswith("达到最长") for s in result["segments"])
    for s in gates:
        assessment["issues"].append(dict(segment_id=s["segment_id"],first_observed_stage="Pipeline.translation_language_gate",
            reason=s["language_gate_reason"],raw=s["asr"]["raw_text"],associated_stages=["Whisper","Context","Pipeline"],
            earliest_confirmed_semantic_error_stage=None,semantic_error_status="pending human/word-boundary review; rejection is observed, upstream cause is not proven"))
    stamps={e["segment_id"]:e["elapsed_ms"] for e in events if e["kind"] in {"captured","merged_segment"}}
    def earliest(sid):
        parents=by_id[sid].get("parents",[])
        return min(earliest(p) for p in parents) if parents else stamps.get(sid)
    terminal=[]
    for e in events:
        if e["kind"] not in {"drop","translation_boundary"} or not e.get("segment_id"):continue
        detected=earliest(e["segment_id"])
        terminal.append(dict(segment_id=e["segment_id"],kind=e["kind"],reason=e.get("reason") or e.get("skip_reason", ""),
            capture_to_terminal_ms=max(0,e["elapsed_ms"]-detected) if detected is not None else None))
    assessment["performance"]["capture_to_terminal_all"]=terminal
    inject=next((e for e in events if e["kind"]=="injected"),None)
    if inject:
        replay_start=inject["elapsed_ms"]-inject["spans"][-1][1]/16-inject["scheduling_lateness_ms"]
        assessment["performance"]["capture_frame_delays"]= [dict(segment_id=e["segment_id"],
            first_pcm_frame_to_capture_emit_ms=e["elapsed_ms"]-replay_start-e["spans"][0][0]/16,
            last_pcm_frame_to_capture_emit_ms=e["elapsed_ms"]-replay_start-e["spans"][-1][1]/16)
            for e in events if e["kind"]=="captured"]
        assessment["performance"]["frame_clock_note"]="relative paced-stream clock estimated from first injection/deadline lateness; not voice-end/display latency"
    assessment["root_cause_semantic_distribution"]="No forced Capture/Whisper/Context root cause from edit distance. First observed rejection/loss is explicit; human word/frame semantics still pending."
    return assessment


def human_review_items(result,record,run_dir):
    out=[]
    for s in result["segments"]:
        identity=json.dumps([record["id"],s["spans"],s["pcm_sha256"]],sort_keys=True).encode()
        out.append(dict(id=hashlib.sha256(identity).hexdigest()[:20],recording_id=record["id"],split=record["split"],
            pcm_sha256=s["pcm_sha256"],stream_spans=s["spans"],original_wav_intersections=s["sources"],
            full_recording_audio=record["audio"],reference_for_whole_recording_only=record["reference_text"],
            reference_status=record["reference_status"],speaker_group=record.get("speaker_group"),
            observations=[dict(strategy=result["spec"]["strategy"],segment_wav=str((run_dir/(s["segment_id"]+".wav")).resolve()),
                raw=s.get("asr",{}).get("raw_text"),retained=s.get("retained_text",""),translation_input=s.get("translation_input",""),
                status=s["status"],reason=s.get("filter_reason") or s.get("language_gate_reason") or s["reason"],
                voice_seconds=s["voice_duration_seconds"],asr_language=s.get("asr",{}).get("language"))],
            human=dict(speech_present=None,valid_semantics=None,spoken_text=None,word_frame_labels=[],entities=[],numbers=[],
                       negation=[],tail_complete=None,first_error_stage=None,severity=None,reviewer=None,status="pending")))
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--raw-results",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    with offline_guard():
        if any(args.output.resolve().is_relative_to(p.resolve()) for p in [args.manifest.parent,args.raw_results,ROOT/"voxgo"]):
            raise ValueError("Review output must be outside immutable corpus/raw/runtime inputs")
        manifest=json.loads(args.manifest.read_text(encoding="utf-8"));lookup={r["id"]:r for r in manifest["records"]}
        plan=json.loads((args.raw_results/"plan.json").read_text(encoding="utf-8"))
        if hashlib.sha256(args.manifest.read_bytes()).hexdigest()!=plan["manifest_sha256"]:raise ValueError("manifest changed")
        output=create_output(args.output);review={}
        for spec in plan["schedule"]:
            record=lookup[spec["record_id"]]
            if record["split"] not in {"dev","negative"}:raise ValueError("holdout/quarantine review forbidden")
            run=args.raw_results/spec["id"]
            result=json.loads((run/"result.json").read_text(encoding="utf-8"))
            events=[json.loads(l) for l in (run/"events.jsonl").read_text(encoding="utf-8").splitlines()]
            (output/spec["id"]).mkdir()
            write(output/spec["id"]/"assessment.json",reviewed_assessment(result,record,events))
            for item in human_review_items(result,record,run):
                if item["id"] in review:review[item["id"]]["observations"]+=item["observations"]
                else:review[item["id"]]=item
        summary=summarize(output,plan["schedule"])
        write(output/"human-review-items.json",list(review.values()))
        write(output/"provenance.json",dict(analysis_version=2,no_inference=True,raw_results=str(args.raw_results.resolve()),
            raw_plan_sha256=hashlib.sha256((args.raw_results/"plan.json").read_bytes()).hexdigest(),
            review_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),human_labels_all_pending=True,
            note="Raw collector results/initial assessments are retained unchanged. Version 2 uses actual event order and separately counts app language-gate rejections."))
        print(json.dumps(summary["groups"],ensure_ascii=False,indent=2))


if __name__=="__main__":main()
