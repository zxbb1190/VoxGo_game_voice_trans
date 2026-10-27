"""Strict manifest gates and recording-level diagnostics; no semantic gold by AI."""
from collections import Counter
import hashlib
import re
import unicodedata
import wave
from pathlib import Path

from scripts.benchmark_multilingual_asr_profiles import errors as character_errors
from scripts.run_asr_benchmark import _word_errors


def ru_tokens(text):
    return re.findall(r"[^\W_]+",unicodedata.normalize("NFKC",text).casefold(),re.UNICODE)


def validate_manifest(manifest, *, historical_hashes=(), check_audio=True):
    ids,pcm_hashes=set(),set()
    groups={"dev":set(),"locked_holdout":set()}
    sources={"dev":set(),"locked_holdout":set()}
    for row in manifest["records"]:
        if row["id"] in ids or row["pcm_sha256"] in pcm_hashes:
            raise ValueError("duplicate record id/PCM")
        ids.add(row["id"]);pcm_hashes.add(row["pcm_sha256"])
        if row["wav_sha256"] in historical_hashes or row["pcm_sha256"] in historical_hashes or row.get("historical_match"):
            raise ValueError("historically used input cannot be new validation data")
        if row["split"] not in {"dev","locked_holdout","negative","quarantine"}:
            raise ValueError("unknown split")
        if not row.get("license") or not row.get("license_source") or not row.get("source_revision"):
            raise ValueError("missing license/version evidence")
        if row["split"]=="locked_holdout":
            if not row.get("speaker_id") or not row.get("lock_eligible") or row.get("speaker_isolation_status")!="verified":
                raise ValueError("unknown speakers cannot be declared validated locked holdout")
        if row["split"] in groups:
            groups[row["split"]].add(row.get("speaker_group") or "unknown-speaker-all")
            sources[row["split"]].add(row["source_group"])
        if check_audio:
            path=Path(row["audio"])
            if hashlib.sha256(path.read_bytes()).hexdigest()!=row["wav_sha256"]:
                raise ValueError("WAV SHA256 mismatch")
            with wave.open(str(path),"rb") as wav:
                if (wav.getnchannels(),wav.getsampwidth(),wav.getframerate(),wav.getnframes())!=(1,2,16000,row["frames"]):
                    raise ValueError("WAV format/frames mismatch")
                if hashlib.sha256(wav.readframes(wav.getnframes())).hexdigest()!=row["pcm_sha256"]:
                    raise ValueError("PCM SHA256 mismatch")
    if groups["dev"] & groups["locked_holdout"] or sources["dev"] & sources["locked_holdout"]:
        raise ValueError("speaker/source leakage across dev and locked holdout")
    if groups["locked_holdout"] and any(not r.get("speaker_id") for r in manifest["records"] if r["split"]=="dev"):
        raise ValueError("Cannot certify locked isolation while dev speaker identities remain unknown")
    return True


def evaluation_rows(manifest):
    # Deliberately no allow-holdout flag; quarantine cannot enter inference.
    return [r for r in manifest["records"] if r["split"] in {"dev","negative"}]


def text_metrics(reference,hypothesis, *, alignment_valid, reference_status):
    result=dict(accepted_cer=None,accepted_wer=None,reference_status=reference_status,
                scope="whole-recording workflow edit distance against pending publisher transcript, not per-segment or human accuracy")
    if not reference or not alignment_valid:
        return dict(result,proxy_cer=None,proxy_wer=None,unavailable="empty/no speech reference or ambiguous PCM/order")
    chars=character_errors(reference,hypothesis)
    words=_word_errors(reference,hypothesis,ru_tokens)
    return dict(result,proxy_cer=chars["cer"],proxy_wer=words["errors"]/max(1,words["reference_words"]),
                character_counts=chars,word_counts=words)


def lexical_suspicions(reference,hypothesis):
    ref,hyp=ru_tokens(reference),ru_tokens(hypothesis)
    negative={"не","нет","ни","нельзя","никогда","без"}
    digits=lambda text:re.findall(r"\d+(?:[.,]\d+)*",text)
    # Cues only: digit-vs-spoken-number forms and source errors can cause flags.
    return dict(reference_digits=digits(reference),hypothesis_digits=digits(hypothesis),
        digits_changed=digits(reference)!=digits(hypothesis),
        reference_negation_tokens=[x for x in ref if x in negative],hypothesis_negation_tokens=[x for x in hyp if x in negative],
        negation_token_counts_changed=Counter(x for x in ref if x in negative)!=Counter(x for x in hyp if x in negative),
        reference_tail_tokens=ref[-3:],hypothesis_tail_tokens=hyp[-3:],tail_lexically_different=ref[-3:]!=hyp[-3:],
        manual_entity_retention=None,manual_semantic_accuracy=None,label_status="pending_human_review; lexical flags are not gold")


def percentile(values,q):
    if not values:return None
    ordered=sorted(values);where=(len(ordered)-1)*q;left=int(where);right=min(left+1,len(ordered)-1)
    return ordered[left]+(ordered[right]-ordered[left])*(where-left)


def assess(result,record,events):
    completed=[s for s in result["segments"] if "asr" in s]
    # Inference insertion order is production emission order. Never silently
    # sort/deduplicate words to improve the score.
    flattened=[span for s in completed for span in s["spans"]]
    overlap=any(b[0]<a[1] for a,b in zip(flattened,flattened[1:]))
    duplicate=len({(tuple(map(tuple,s["spans"])),s["pcm_sha256"]) for s in completed})!=len(completed)
    alignment_valid=not overlap and not duplicate and len(result["clips"])==1
    raw=" ".join(s["asr"].get("raw_text",s["asr"]["text"]) for s in completed).strip()
    retained=" ".join(s.get("retained_text","") for s in completed if s.get("retained_text")).strip()
    translated=" ".join(s.get("translation_input","") for s in completed if s.get("translation_input")).strip()
    drops=[s for s in result["segments"] if s["status"]=="dropped"]
    before=[s for s in drops if "asr" not in s];after=[s for s in drops if "asr" in s]
    queue_drops=[e for e in events if e["kind"]=="raw_queue_drop"]
    issues=[]
    for s in before+after:
        issues.append(dict(segment_id=s["segment_id"],first_observed_stage="Pipeline.pre_asr" if s in before else "Pipeline.post_asr",
            reason=s.get("filter_reason"),raw=s.get("asr",{}).get("raw_text"),
            effective_semantic_loss="pending segment-level human alignment",
            associated_stages=["Pipeline"]+(["Context"] if "asr" not in s else [])))
    for e in queue_drops:issues.append(dict(first_observed_stage="Capture.raw_queue",reason=e["reason"],spans=e["spans"],pcm_loss_proven=True))
    if record["split"]=="negative" and (raw or translated):
        issues.append(dict(first_observed_stage="Whisper" if not translated else "Whisper_then_Pipeline",
            reason="publisher-labelled noise produced text",associated_stages=["Capture","Whisper","Pipeline"],
            confirmed_false_acceptance=False,human_noise_absence_review="pending"))
    captured=[s for s in result["segments"] if s["captured"]]
    capture_spans=[span for s in captured for span in s["spans"]]
    gaps=[dict(start=a[1],end=b[0],frames=b[0]-a[1]) for a,b in zip(capture_spans,capture_spans[1:]) if b[0]!=a[1]]
    times=[s["asr_ms"] for s in completed]
    waits=[w["queue_wait_ms"] for w in result["work_items"] if w.get("queue_wait_ms") is not None]
    starts=[e for e in events if e["kind"]=="whisper_start"]
    terminal_times=[dict(segment_id=e.get("segment_id"),reason=e.get("reason"),elapsed_ms=e["elapsed_ms"]) for e in events if e["kind"]=="drop"]
    return dict(id=record["id"],split=record["split"],strategy=result["spec"]["strategy"],seconds=record["seconds"],
        raw=raw,retained=retained,translation_input=translated,
        raw_metrics=text_metrics(record["reference_text"],raw,alignment_valid=alignment_valid,reference_status=record["reference_status"]),
        retained_metrics=text_metrics(record["reference_text"],retained,alignment_valid=alignment_valid,reference_status=record["reference_status"]),
        translated_metrics=text_metrics(record["reference_text"],translated,alignment_valid=alignment_valid,reference_status=record["reference_status"]),
        alignment=dict(valid=alignment_valid,method="one immutable full source per fresh process; inference order; no overlap/duplicate/interleaving permitted; all padding emissions count as insertions",
                       word_timestamps=None,per_segment_reference=None,capture_gap_intervals=gaps,
                       capture_gaps_are_not_automatically_errors=True,duplicate_submission=duplicate,overlap_or_reorder=overlap),
        lexical_suspicions=lexical_suspicions(record["reference_text"],translated) if record["split"]!="negative" else None,
        counts=dict(captured=len(captured),work_items=len(result["work_items"]),merges=sum(e["kind"]=="work_merge" for e in events),
                    asr_attempted=len(starts),asr_completed=len(completed),asr_missing_completion=len(starts)-len(completed),
                    pre_asr_drops=len(before),post_asr_drops=len(after),translation_ready=sum(bool(s.get("translation_input")) for s in completed),
                    raw_queue_drops=len(queue_drops),unresolved_work_items=sum(w["status"] not in {"dropped","translation_ready","language_gate_dropped","merged_into","cancelled_at_shutdown"} for w in result["work_items"])),
        languages=[dict(segment_id=s["segment_id"],language=s["asr"]["language"],probability=s["asr"]["language_probability"]) for s in completed],
        performance=dict(asr_all_completed_ms=times,asr_p50_ms=percentile(times,.5),asr_p95_ms=percentile(times,.95),
            queue_wait_all_ms=waits,queue_wait_p95_ms=percentile(waits,.95),replay_cpu_seconds=result["replay_cpu_seconds"],
            cpu_seconds_per_audio_minute=result["replay_cpu_seconds"]/(record["seconds"]/60),peak_sampled_rss_bytes=result["peak_sampled_rss_bytes"],
            replay_wall_seconds=result["replay_wall_seconds"],drop_terminal_events=terminal_times,
            note="ASR timings include filtered calls. Pre-ASR drops have no invented ASR duration; all admission/drop events retained."),
        negative_raw_nonempty=record["split"]=="negative" and bool(raw),negative_translation_nonempty=record["split"]=="negative" and bool(translated),
        issues=issues,root_cause_semantic_distribution="unresolved until references/word spans manually verified; raw mismatch is not automatically Whisper or Capture fault")
