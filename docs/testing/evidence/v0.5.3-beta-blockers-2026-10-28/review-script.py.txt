"""Read frozen acceptance evidence, without inference, API calls or new labels."""
import argparse
import ctypes
import difflib
import hashlib
import json
from pathlib import Path
import sys
import unicodedata
import wave

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.offline_russian_capture_ab import create_output, offline_guard, write
from scripts.run_asr_benchmark import _word_errors
from scripts.run_ru_continuous_baseline import input_stream


def chars(text):
    return [c for c in unicodedata.normalize("NFKC", text).casefold() if c.isalnum()]


def edit_review(reference, hypothesis):
    counts = _word_errors(reference, hypothesis, chars)
    counts["reference_characters"] = counts.pop("reference_words")
    # Excerpts use a display alignment, not a new semantic/error metric.
    a, b = chars(reference), chars(hypothesis)
    examples = [dict(operation=tag, reference="".join(a[i:j]), hypothesis="".join(b[k:l]))
                for tag, i, j, k, l in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
                if tag != "equal"]
    return dict(character_counts=counts, display_alignment=examples,
                human_semantic_verdict=None, entity_error_confirmed=None)


def simplified_for_sensitivity(text):
    """Windows linguistic mapping only for sensitivity, never runtime/scoring gold."""
    if sys.platform != "win32":
        return None
    if not text:
        return ""
    mapper = ctypes.windll.kernel32.LCMapStringEx
    mapper.argtypes = [ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_wchar_p, ctypes.c_int,
                       ctypes.c_wchar_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ssize_t]
    mapper.restype = ctypes.c_int
    size = mapper("zh-CN", 0x02000000, text, len(text), None, 0, None, None, 0)
    if not size:
        raise ctypes.WinError()
    output = ctypes.create_unicode_buffer(size)
    if not mapper("zh-CN", 0x02000000, text, len(text), output, size, None, None, 0):
        raise ctypes.WinError()
    return output[:size]


def choose_recordings(rows, language):
    relevant = [r for r in rows if r["language"] == language]
    ids = sorted({r["id"] for r in relevant}, key=lambda rid: (
        -max(r["cer"] for r in relevant if r["id"] == rid), rid))[:3]
    if language == "ru":
        pairs = {rid: {r["strategy"]: r["cer"] for r in relevant if r["id"] == rid}
                 for rid in {r["id"] for r in relevant}}
        worst = max(pairs, key=lambda rid: pairs[rid]["language_aware"] - pairs[rid]["legacy"])
        if worst not in ids:
            ids.append(worst)
    return ids


def read_pcm(record):
    path = Path(record["audio"])
    if hashlib.sha256(path.read_bytes()).hexdigest() != record["wav_sha256"]:
        raise ValueError("Source WAV fingerprint changed")
    with wave.open(str(path), "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()) != (1, 2, 16000, record["frames"]):
            raise ValueError("Source format/frame mismatch")
        pcm = wav.readframes(wav.getnframes())
    if hashlib.sha256(pcm).hexdigest() != record["pcm_sha256"]:
        raise ValueError("Source PCM fingerprint changed")
    return pcm


def energy(pcm):
    samples = np.frombuffer(pcm, dtype="<i2").astype(np.float64) / 32768
    rms = lambda x: float(20 * np.log10(max(float(np.sqrt(np.mean(x*x))), 1e-10)))
    return dict(rms_dbfs=rms(samples), peak_sample_dbfs=float(20*np.log10(max(float(np.max(np.abs(samples))), 1e-10))),
                max_120ms_rms_dbfs=max(rms(samples[i:i+1920]) for i in range(0, len(samples), 1920)))


def source_conversion(record, pcm):
    original = Path(record["original_file"])
    if hashlib.sha256(original.read_bytes()).hexdigest() != record["original_sha256"]:
        raise ValueError("Original source fingerprint changed")
    samples, rate = sf.read(original, dtype="float64")
    if samples.ndim != 1 or rate != 16000 or len(samples) != len(pcm)//2:
        raise ValueError("This review requires the frozen mono/16k full-source conversion")
    delta = float(np.max(np.abs(samples - np.frombuffer(pcm, dtype="<i2") / 32768.0)))
    expected = np.rint(np.clip(samples.astype(np.float32), -1., 32767/32768) * 32768).astype("<i2").tobytes()
    if expected != pcm:
        raise ValueError("Source differs beyond frozen PCM16 rounding/clipping; investigate preparation")
    return dict(original_sha256=record["original_sha256"], original_subtype=sf.info(original).subtype,
                max_amplitude_difference=delta, matches_frozen_conversion=True,
                clipped_source_frames=int(((samples < -1.) | (samples > 32767/32768)).sum()))


def segment_review(record, result, run, pcm):
    # Reconstruct the exact original padded stream; never rerun Capture or ASR.
    _, stream, _ = input_stream(record)
    if hashlib.sha256(stream).hexdigest() != result["replay_stream_sha256"]:
        raise ValueError("Frozen replay stream mismatch")
    segments = []
    captured = np.zeros(record["frames"], dtype=bool)
    budget = np.zeros(record["frames"], dtype=bool)
    vad = np.zeros(record["frames"], dtype=bool)
    activity = []
    for s in result["segments"]:
        reconstructed = b"".join(stream[a*2:b*2] for a, b in s["spans"])
        with wave.open(str(run / (s["segment_id"] + ".wav")), "rb") as wav:
            actual = wav.readframes(wav.getnframes())
        if actual != reconstructed or hashlib.sha256(actual).hexdigest() != s["pcm_sha256"]:
            raise ValueError("Exact saved segment mismatch")
        spans = [[x["wav_start_frame"], x["wav_end_frame"]] for x in s["sources"]]
        for a, b in spans:
            if s["captured"]:
                captured[a:b] = True
            if s.get("filter_reason") == "asr_budget_weak_drop":
                budget[a:b] = True
        segments.append({k: s.get(k) for k in (
            "segment_id", "pcm_sha256", "spans", "sources", "parents", "reason", "status",
            "voice_duration_seconds", "duration_seconds", "peak_rms_dbfs", "energy_threshold_dbfs",
            "normalization", "asr", "retained_text", "translation_input", "filter_reason", "language_gate_reason")})
    for w in result["activity_windows"]:
        spans = [[max(0, a-48000), min(record["frames"], b-48000)]
                 for a, b in w["spans"] if b > 48000 and a < 48000+record["frames"]]
        if not spans:
            continue
        if w["vad_speech"]:
            for a, b in spans:
                vad[a:b] = True
        activity.append(dict(wav_spans=spans, **{k: w.get(k) for k in (
            "vad_speech", "vad_ratio", "rms_dbfs", "energy_threshold_dbfs", "energy_activity",
            "relative_tail_candidate", "near_gate_candidate")}))
    return dict(segments=segments, activity_windows=activity,
                captured_frames=int(captured.sum()), source_frames=record["frames"],
                vad_active_frames=int(vad.sum()), vad_active_uncaptured_frames=int((vad & ~captured).sum()),
                vad_active_budget_rejected_frames=int((vad & budget).sum()),
                caveat="VAD/energy activity is not human speech/word truth; no semantic error rate inferred")


def run(manifest_path, baseline, evidence, output):
    for protected in (manifest_path.parent, baseline, evidence, ROOT / "voxgo"):
        if output.resolve().is_relative_to(protected.resolve()):
            raise ValueError("Protect frozen inputs and runtime")
    manifest = json.loads(manifest_path.read_text("utf-8"))
    records = {r["id"]: r for r in manifest["records"] if r["split"] == "dev"}
    plan = json.loads((baseline / "plan.json").read_text("utf-8"))
    hashes, rows = {}, []
    for spec in plan["schedule"]:
        if spec["record_id"] not in records:
            continue
        path = baseline / spec["id"] / "assessment.json"
        hashes[str(path.resolve())] = hashlib.sha256(path.read_bytes()).hexdigest()
        assessment = json.loads(path.read_text("utf-8"))
        rows.append(dict(id=spec["record_id"], language=spec["source_language"], strategy=spec["strategy"],
                         run=baseline / spec["id"], assessment=assessment, cer=assessment["translated_metrics"]["proxy_cer"]))
    selected = {language: choose_recordings(rows, language) for language in ("zh", "en", "ja", "ko", "ru")}
    pcm = {rid: read_pcm(r) for rid, r in records.items()}
    conversions = {rid: source_conversion(r, pcm[rid]) for rid, r in records.items()}
    reviews, amplitude = [], []
    for row in rows:
        record = records[row["id"]]
        if row["id"] not in selected[row["language"]]:
            continue
        result_path = row["run"] / "result.json"
        hashes[str(result_path.resolve())] = hashlib.sha256(result_path.read_bytes()).hexdigest()
        result = json.loads(result_path.read_text("utf-8"))
        assessment = row["assessment"]
        reviews.append(dict(id=row["id"], language=row["language"], strategy=row["strategy"],
            reference=record["reference_text"], reference_status=record["reference_status"],
            raw=assessment["raw"], translation_input=assessment["translation_input"], retained=assessment["retained"],
            counts=assessment["counts"], cer=row["cer"], energy=energy(pcm[row["id"]]), conversion=conversions[row["id"]],
            edits=edit_review(record["reference_text"], assessment["translation_input"]),
            exact_pcm=segment_review(record, result, row["run"], pcm[row["id"]]),
            source_audio=record["audio"], wav_sha256=record["wav_sha256"], pcm_sha256=record["pcm_sha256"],
            effective_config=result["initial_effective_config"], human_semantic_status="pending"))
    for rid, record in records.items():
        amplitude.append(dict(id=rid, language=record["language"], **energy(pcm[rid]), conversion=conversions[rid],
            variants=[dict(strategy=r["strategy"], counts=r["assessment"]["counts"], translation_input_empty=not r["assessment"]["translation_input"])
                      for r in rows if r["id"] == rid]))
    sensitivity = []
    for row in rows:
        if row["language"] != "zh":
            continue
        ref = records[row["id"]]["reference_text"]
        hyp = row["assessment"]["translation_input"]
        converted = simplified_for_sensitivity(hyp)
        counts = None if converted is None else _word_errors(ref, converted, chars)
        sensitivity.append(dict(id=row["id"], raw_cer=row["cer"], simplified_hypothesis=converted,
            simplified_character_counts=counts, new_score_accepted=False,
            caveat="Sensitivity only; one-to-many traditional/simplified mapping is not semantic validation"))
    text = json.loads((evidence / "online-text-results.json").read_text("utf-8"))
    truncations = [r for r in text if r.get("finish_reason") == "length"]
    # All authored outputs stay available for reviewing recurring number/negation/
    # timing/role errors. No automatic verdict or invented semantic labels.
    authored = [r for r in text if r["phase"] == "authored_text"]
    output = create_output(output)
    write(output / "focused-asr-review.json", reviews)
    write(output / "source-amplitude-inventory.json", amplitude)
    write(output / "zh-format-sensitivity.json", sensitivity)
    write(output / "text-review.json", dict(authored=authored, truncated=truncations, human_status="pending"))
    for path, digest in hashes.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
            raise ValueError("Frozen input changed during review")
    write(output / "provenance.json", dict(base_head="5dcd75bf", script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(), source_wavs_checked=len(pcm), original_float_sources_checked=len(conversions),
        selected_recordings=selected, input_files_sha256=hashes, no_inference=True, real_api_requests=0,
        human_semantic_verdicts_created=0, prior_evidence_unchanged=True))
    lines = ["# Focused ASR review (saved evidence only)", "", "Human transcription, word/frame alignment and semantic review: pending.", ""]
    for row in reviews:
        lines += [f"## {row['id']} / {row['strategy']}", "", f"Reference (publisher, pending): {row['reference']}",
                  f"Raw: {row['raw']}", f"Translation input: {row['translation_input'] or '(empty)'}", "",
                  f"Counts: `{json.dumps(row['counts'])}`", "", "Segments (WAV frame intervals; exact PCM verified):", ""]
        for segment in row["exact_pcm"]["segments"]:
            lines.append(f"- {segment['segment_id']}: {[(s['wav_start_frame'],s['wav_end_frame']) for s in segment['sources']]}; raw={segment['asr']}; rejection={segment['filter_reason'] or segment['language_gate_reason']}")
        lines.append("")
    (output / "focused-asr-review.md").write_text("\n".join(lines), encoding="utf-8")
    return dict(selected_independent_recordings=sum(map(len, selected.values())), strategy_rows=len(reviews), source_wavs_checked=len(pcm), real_api_requests=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with offline_guard():
        print(json.dumps(run(args.manifest, args.baseline, args.evidence, args.output)))


if __name__ == "__main__":
    main()
