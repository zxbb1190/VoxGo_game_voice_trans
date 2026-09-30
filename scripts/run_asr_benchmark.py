"""Run a labelled ASR corpus through whole-file and VoxGo capture-cut paths.

Usage: python -m scripts.run_asr_benchmark --manifest data/asr-benchmark/manifest.jsonl
"""

import argparse
import hashlib
import html
import json
import re
import statistics
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from loguru import logger

from voxgo.audio.benchmark import load_benchmark_audio
from voxgo.audio.capture import (
    AudioConfig,
    SystemAudioCapture,
    apply_audio_latency_preset,
    apply_english_realtime_latency_bias,
)
from voxgo.asr.runaway_repetition import analyze_repetition, is_runaway_repetition


TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?", re.IGNORECASE)
ANNOTATION_RE = re.compile(r"\[[^\]]+\]")
NUMBER_RE = re.compile(r"\b\d+\b")
SMALL_NUMBERS = ("zero", "one", "two", "three", "four", "five", "six", "seven",
                 "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
                 "fifteen", "sixteen", "seventeen", "eighteen", "nineteen")
TENS = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")
PRESETS = ("fast", "balanced", "accurate")
PROMPTS = ("off", "game_en")


@dataclass(frozen=True)
class Case:
    id: str
    category: str
    audio: Path
    reference: str
    source: str
    license: str = ""
    snr_db: float = None
    subset: str = ""
    clean_category: str = ""


def load_manifest(path: Path, limit: int = 0) -> list:
    cases = []
    ids = set()
    with path.open("r", encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            case_id = str(row["id"]).strip()
            category = str(row["category"]).strip()
            reference = str(row["reference"]).strip()
            if not case_id or case_id in ids:
                raise ValueError(f"{path}:{line_number}: empty or duplicate id {case_id!r}")
            if category not in {"natural", "noise", "game"} or not reference:
                raise ValueError(f"{path}:{line_number}: invalid category or empty reference")
            audio = Path(row["audio"])
            if not audio.is_absolute():
                audio = path.parent / audio
            audio = audio.resolve()
            if not audio.is_file():
                raise FileNotFoundError(f"{path}:{line_number}: {audio}")
            cases.append(Case(case_id, category, audio, reference, str(row.get("source", "")),
                              str(row.get("license", "")), row.get("snr_db"),
                              str(row.get("subset", "")), str(row.get("clean_category", ""))))
            ids.add(case_id)
            if limit and len(cases) >= limit:
                break
    if not cases:
        raise ValueError(f"manifest has no cases: {path}")
    return cases


def _spoken_integer(value: int) -> str:
    if value < 20:
        return SMALL_NUMBERS[value]
    if value < 100:
        return TENS[value // 10] + (" " + SMALL_NUMBERS[value % 10] if value % 10 else "")
    if value < 1000:
        return SMALL_NUMBERS[value // 100] + " hundred" + (
            " " + _spoken_integer(value % 100) if value % 100 else "")
    return str(value)


def tokens(text: str) -> list:
    # Common Voice SPS references may contain non-lexical [noise] or
    # [disfluency] tags; they are not spoken words for WER scoring.
    normalized = ANNOTATION_RE.sub(" ", text).casefold().replace("’", "'").replace("'", "")
    normalized = NUMBER_RE.sub(lambda match: _spoken_integer(int(match.group())), normalized)
    return TOKEN_RE.findall(normalized)


def word_errors(reference: str, hypothesis: str) -> dict:
    """Levenshtein edit counts with a deterministic deletion-first tie break."""
    ref, hyp = tokens(reference), tokens(hypothesis)
    rows = [[(0, 0, 0, 0)] * (len(hyp) + 1) for _ in range(len(ref) + 1)]
    for i in range(1, len(ref) + 1):
        rows[i][0] = (i, 0, i, 0)
    for j in range(1, len(hyp) + 1):
        rows[0][j] = (j, 0, 0, j)
    for i, expected in enumerate(ref, 1):
        for j, actual in enumerate(hyp, 1):
            same = expected == actual
            match = rows[i - 1][j - 1]
            diagonal = (match[0] + (not same), match[1] + (not same), match[2], match[3])
            deleted = rows[i - 1][j]
            deletion = (deleted[0] + 1, deleted[1], deleted[2] + 1, deleted[3])
            inserted = rows[i][j - 1]
            insertion = (inserted[0] + 1, inserted[1], inserted[2], inserted[3] + 1)
            rows[i][j] = min((diagonal, deletion, insertion), key=lambda item: (item[0], item[1], item[3]))
    _, subs, deletes, inserts = rows[-1][-1]
    return {"reference_words": len(ref), "substitutions": subs,
            "deletions": deletes, "insertions": inserts,
            "errors": subs + deletes + inserts}


def capture_segments(samples: np.ndarray, preset: str) -> list:
    """Replay 16 kHz mono PCM through the live capture VAD, one configured block at a time."""
    config = AudioConfig(latency_mode=preset, sample_rate=16000, channels=1)
    apply_audio_latency_preset(config)
    apply_english_realtime_latency_bias(config, preset)
    capture = SystemAudioCapture(config)
    segments = []
    capture.set_speech_callback(segments.append)
    block_size = int(16000 * config.chunk_duration_ms / 1000)
    try:
        for start in range(0, len(samples), block_size):
            chunk = samples[start:start + block_size]
            if len(chunk) < block_size:
                chunk = np.pad(chunk, (0, block_size - len(chunk)))
            capture._enqueue_audio_block(chunk.astype("<i2", copy=False).tobytes())
            capture.process_audio()
        # A real capture stream receives silence after an utterance. Feed enough
        # silence to close the final segment without waiting on wall-clock time.
        silence_blocks = max(config.silence_limit_blocks + 1,
                             int(np.ceil(config.speech_idle_timeout_ms / config.chunk_duration_ms)) + 1)
        blank = np.zeros(block_size, dtype="<i2").tobytes()
        for _ in range(silence_blocks):
            capture._enqueue_audio_block(blank)
            capture.process_audio()
        # A low-energy tail can remain buffered after finite silence; simulate
        # the live idle timeout deterministically, rather than dropping speech.
        if capture._speech_buffer:
            capture._handle_idle_timeout(time.monotonic() + config.speech_idle_timeout_ms / 1000 + 0.01)
    finally:
        capture._audio.terminate()
    return segments


def score_record(case: Case, model: str, preset: str, prompt: str, path: str,
                 hypothesis: str, inference_seconds: float, segment_count: int,
                 device: str, compute_type: str, beam_size: int = 0,
                 model_fingerprint: str = "", cpu_threads: int = 0,
                 segment_diagnostics: list = None, raw_hypothesis: str = None,
                 runaway_guarded: bool = False) -> dict:
    counts = word_errors(case.reference, hypothesis)
    reference_words = counts["reference_words"]
    raw_text = hypothesis if raw_hypothesis is None else raw_hypothesis
    raw_words = tokens(raw_text)
    output_ratio = len(tokens(hypothesis)) / max(1, reference_words)
    raw_ratio = len(raw_words) / max(1, reference_words)
    abnormal_length = len(raw_words) > max(reference_words * 4, reference_words + 20)
    delivered_repetition = analyze_repetition(hypothesis)
    raw_repetition = analyze_repetition(raw_text)
    duration = sum(float(item.get("duration_seconds", 0) or 0)
                   for item in (segment_diagnostics or []))
    repetition_failure = is_runaway_repetition(hypothesis, duration_seconds=duration)
    raw_repetition_failure = is_runaway_repetition(raw_text, duration_seconds=duration)
    return {"id": case.id, "category": case.category, "subset": case.subset,
            "clean_category": case.clean_category, "audio": str(case.audio),
            "source": case.source, "license": case.license,
            "snr_db": case.snr_db, "model": model, "preset": preset,
            "prompt": prompt, "path": path, "reference": case.reference,
            "hypothesis": hypothesis, "inference_seconds": round(inference_seconds, 4),
            "segments": segment_count, "device": device, "compute_type": compute_type,
            "beam_size": beam_size, "model_fingerprint": model_fingerprint,
            "cpu_threads": cpu_threads,
            "hit": tokens(case.reference) == tokens(hypothesis), **counts,
            "output_words": len(tokens(hypothesis)), "raw_output_words": len(raw_words),
            "output_reference_length_ratio": output_ratio,
            "raw_output_reference_length_ratio": raw_ratio,
            "abnormal_length": abnormal_length,
            "repetition_failure": repetition_failure,
            "raw_repetition_failure": raw_repetition_failure,
            "repetition_word_count": delivered_repetition.word_count,
            "raw_repetition_word_count": raw_repetition.word_count,
            "repeated_ngram_words": delivered_repetition.repeated_ngram_words,
            "max_repeat_count": delivered_repetition.max_repeat_count,
            "max_repeat_span_words": delivered_repetition.max_repeat_span_words,
            "runaway_guarded": bool(runaway_guarded),
            "raw_hypothesis": raw_text,
            "segment_diagnostics": list(segment_diagnostics or [])}


def summarize(records: list) -> list:
    grouped = defaultdict(list)
    for row in records:
        key = (row["model"], row["preset"], row["prompt"], row["path"],
               row["category"], row["clean_category"], row["snr_db"],
               row["device"], row["compute_type"], row.get("cpu_threads", 0))
        grouped[(*key, "all")].append(row)
        if row["subset"]:
            grouped[(*key, row["subset"])].append(row)
    output = []
    for (model, preset, prompt, path, category, clean_category, snr_db, device,
         compute_type, cpu_threads, subset), rows in sorted(
            grouped.items(), key=lambda entry: tuple("" if value is None else str(value) for value in entry[0])):
        words = sum(row["reference_words"] for row in rows)
        errors = sum(row["errors"] for row in rows)
        deletions = sum(row["deletions"] for row in rows)
        output.append({"model": model, "preset": preset, "prompt": prompt,
                       "path": path, "category": category, "clean_category": clean_category,
                       "subset": subset, "snr_db": snr_db, "cases": len(rows),
                       "wer": errors / words if words else None,
                       "deletion_rate": deletions / words if words else None,
                       "exact_hit_rate": sum(row["hit"] for row in rows) / len(rows),
                       "mean_inference_seconds": statistics.mean(row["inference_seconds"] for row in rows),
                       "p50_inference_seconds": statistics.median(row["inference_seconds"] for row in rows),
                       "p95_inference_seconds": _percentile([row["inference_seconds"] for row in rows], 0.95),
                       "repetition_failure_count": sum(bool(row.get("repetition_failure")) for row in rows),
                       "repetition_failure_rate": sum(bool(row.get("repetition_failure")) for row in rows) / len(rows),
                       "raw_repetition_failure_count": sum(bool(row.get("raw_repetition_failure")) for row in rows),
                       "raw_repetition_failure_rate": sum(bool(row.get("raw_repetition_failure")) for row in rows) / len(rows),
                       "runaway_guarded_count": sum(bool(row.get("runaway_guarded")) for row in rows),
                       "abnormal_length_count": sum(bool(row.get("abnormal_length")) for row in rows),
                       "abnormal_length_rate": sum(bool(row.get("abnormal_length")) for row in rows) / len(rows),
                       "max_output_reference_length_ratio": max(
                           (float(row.get("raw_output_reference_length_ratio",
                                          row.get("output_reference_length_ratio", 0)) or 0)
                            for row in rows),
                           default=0.0),
                       "average_segment_count": statistics.mean(row.get("segments", 0) for row in rows),
                       "average_segment_duration_seconds": statistics.mean(
                           [float(segment.get("duration_seconds", 0) or 0)
                            for row in rows for segment in row.get("segment_diagnostics", [])]
                           or [0.0]),
                       "device": device, "compute_type": compute_type,
                       "cpu_threads": cpu_threads})
    return output


def _percentile(values: list, quantile: float) -> float:
    """Return a deterministic linearly interpolated percentile."""
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def _segment_diagnostic(chunk: bytes, result, index: int, start_seconds: float,
                        prompt: str, config, capture_segment=None,
                        inference_seconds: float = 0.0, prompt_text=None) -> dict:
    samples = np.frombuffer(chunk, dtype="<i2")
    duration = len(samples) / 16000.0
    rms_dbfs = None
    if len(samples):
        normalized = samples.astype(np.float32) / 32768.0
        rms_dbfs = float(20 * np.log10(max(float(np.sqrt(np.mean(normalized ** 2))), 1e-10)))
    raw_text = str(getattr(result, "raw_text", getattr(result, "text", "")) or "")
    guarded_text = str(getattr(result, "text", raw_text) or "")
    return {
        "index": index,
        "emitted_start_seconds": round(start_seconds, 4),
        "emitted_end_seconds": round(start_seconds + duration, 4),
        "timing_basis": "source_audio" if capture_segment is None else "emitted_audio_cumulative",
        "source_offset_available": capture_segment is None,
        "duration_seconds": round(duration, 4),
        "rms_dbfs": round(rms_dbfs, 3) if rms_dbfs is not None else None,
        "peak_rms_dbfs": getattr(capture_segment, "peak_rms_dbfs", None),
        "voice_duration_seconds": getattr(capture_segment, "voice_duration_seconds", None),
        "vad_speech_ratio": getattr(capture_segment, "vad_confidence", None),
        "energy_speech_ratio": (
            getattr(capture_segment, "energy_voice_blocks", 0) /
            max(1, getattr(capture_segment, "block_count", 0))
            if capture_segment is not None else None),
        "prompt": prompt,
        "prompt_text": prompt_text,
        "config": {name: getattr(config, name, None) for name in (
            "beam_size", "vad_filter", "condition_on_previous_text", "temperature",
            "compression_ratio_threshold", "no_speech_threshold", "log_prob_threshold",
            "prompt_profile")},
        "raw_text": raw_text,
        "guarded_text": guarded_text,
        "runaway_guarded": bool(getattr(result, "runaway_guarded", False)),
        "word_count": len(tokens(guarded_text)),
        "raw_word_count": len(tokens(raw_text)),
        "compression_ratio": getattr(result, "compression_ratio", None),
        "avg_logprob": getattr(result, "avg_logprob", None),
        "no_speech_prob": getattr(result, "no_speech_prob", None),
        "inference_seconds": round(inference_seconds, 4),
    }


def render_html(summary: list, records: list, failures: list, metadata: dict) -> str:
    def esc(value):
        return html.escape(str(value), quote=True)

    def pct(value):
        return "—" if value is None else f"{value:.1%}"

    table_rows = "\n".join(
        "<tr>" + "".join(f"<td>{esc(value)}</td>" for value in (
            row["model"], row["preset"], row["prompt"], row["path"], row["category"],
            row["subset"],
            "—" if row["snr_db"] is None else f'{row["snr_db"]:g} dB',
            row["cases"], pct(row["wer"]), pct(row["deletion_rate"]),
            pct(row["exact_hit_rate"]) if row["subset"] == "game" else "—",
            f'{row["mean_inference_seconds"]:.2f}s',
            f'{row["p50_inference_seconds"]:.2f}s', f'{row["p95_inference_seconds"]:.2f}s',
            f'{row["repetition_failure_count"]}/{row["cases"]} ({pct(row["repetition_failure_rate"])})',
            f'{row["raw_repetition_failure_count"]}/{row["cases"]} ({pct(row["raw_repetition_failure_rate"])})',
            f'{row["abnormal_length_count"]}/{row["cases"]} ({pct(row["abnormal_length_rate"])})',
            f'{row["max_output_reference_length_ratio"]:.2f}x raw',
            f'{row["average_segment_count"]:.2f}',
            f'{row["average_segment_duration_seconds"]:.2f}s',
            row["device"], row["compute_type"],
            row["cpu_threads"])) + "</tr>"
        for row in summary)
    worst = sorted(records, key=lambda row: (row["errors"] / max(1, row["reference_words"]), row["deletions"]), reverse=True)[:30]
    worst_rows = "\n".join(
        "<tr>" + "".join(f"<td>{esc(value)}</td>" for value in (
            row["id"], row["model"], row["preset"], row["prompt"], row["path"],
            row["category"], row["subset"], f'{row["errors"]}/{row["reference_words"]}',
            row["repetition_failure"], row.get("raw_repetition_failure", False), row["abnormal_length"],
            row.get("runaway_guarded", False),
            f'{row["output_reference_length_ratio"]:.2f}x / {row.get("raw_output_reference_length_ratio", 0):.2f}x',
            row["reference"], row["hypothesis"], row.get("raw_hypothesis", row["hypothesis"]))) + "</tr>" for row in worst)
    failure_rows = "".join(f"<li>{esc(item)}</li>" for item in failures)
    return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>VoxGo ASR Benchmark</title>
<style>body{{font:15px system-ui,sans-serif;max-width:1400px;margin:2rem auto;padding:0 1rem;color:#162235}}
table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{border:1px solid #d9e1e9;padding:.55rem;text-align:left;vertical-align:top}}
th{{background:#eff4fa;position:sticky;top:0}}tr:nth-child(even){{background:#f8fafc}}.wrap{{overflow:auto}}
code{{background:#f1f4f8;padding:.1rem .25rem}}</style><h1>VoxGo ASR Benchmark</h1>
<p>生成于 {esc(metadata['created_at'])}；样本 {esc(metadata['cases'])} 条。WER 与漏词率均按标准答案词数加权；游戏命中率是规范化后的整句完全匹配率。耗时只计识别调用，不含模型加载、音频解码、切段或翻译。</p>
<p>样本来源：{esc(', '.join(metadata.get('sources', [])) or '未标明')}。合成语音仅用于配置比较，不能代表真实口音或玩家环境。</p>
<p><code>whole</code> 是整段识别；<code>capture_cut</code> 是按当前 AudioConfig 块大小经过 SystemAudioCapture VAD/切段后逐段识别并拼接。后者不模拟 SpeechPipeline 的候选缓冲、异步队列与译文输出；每条音频独立重置噪声校准。仅比较相同数据与设备配置下的结果。</p>
<h2>汇总</h2><div class="wrap"><table><thead><tr><th>模型</th><th>模式</th><th>Prompt</th><th>路径</th><th>类别</th><th>子集</th><th>SNR</th><th>样本</th><th>WER</th><th>漏词率</th><th>游戏命中率</th><th>平均识别耗时</th><th>P50</th><th>P95</th><th>最终文本重复失败</th><th>原始重复失败</th><th>原始超长输出</th><th>最大原始输出比</th><th>平均片段数</th><th>平均片段时长</th><th>设备</th><th>计算类型</th><th>CPU 线程</th></tr></thead><tbody>{table_rows}</tbody></table></div>
<h2>最差案例（按单条 WER）</h2><div class="wrap"><table><thead><tr><th>ID</th><th>模型</th><th>模式</th><th>Prompt</th><th>路径</th><th>类别</th><th>子集</th><th>错词/总词</th><th>最终文本重复失败</th><th>原始重复失败</th><th>原始超长输出</th><th>运行时拦截</th><th>输出词数/参考词数（最终/原始）</th><th>标准答案</th><th>最终识别结果</th><th>原始识别结果</th></tr></thead><tbody>{worst_rows}</tbody></table></div>
<h2>失败或跳过</h2><ul>{failure_rows or '<li>无</li>'}</ul></html>'''


def record_key(row: dict) -> tuple:
    return (row["id"], row["model"], row["preset"], row["prompt"], row["path"])


def _hash_files(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(str(path.resolve()).encode("utf-8"))
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def _model_fingerprint(recognizer) -> str:
    model_path = getattr(recognizer, "_model_path", None)
    if not model_path:
        return ""
    root = Path(model_path)
    if not root.is_dir():
        return ""
    assets = sorted(path for path in root.rglob("*") if path.is_file() and
                    path.suffix.lower() in {".bin", ".json", ".txt", ".model"})
    return _hash_files(assets) if assets else ""


def run(cases: list, models: list, presets: list, prompts: list, device: str,
        compute_type: str, allow_download: bool, recognizer_class=None,
        config_class=None, beam_sizes=None, existing_records=None,
        on_progress=None) -> tuple:
    if recognizer_class is None or config_class is None or beam_sizes is None:
        # Keep scoring/report commands usable when the local ASR runtime cannot load.
        from voxgo.asr.whisper_engine import SpeechRecognizer, WhisperConfig
        from voxgo.config.loader import WHISPER_BEAM_SIZE_BY_LATENCY_MODE
        recognizer_class = SpeechRecognizer
        config_class = WhisperConfig
        beam_sizes = WHISPER_BEAM_SIZE_BY_LATENCY_MODE
    audio = {}
    cuts = {}
    records, failures = list(existing_records or []), []
    for case in cases:
        try:
            samples, rate = load_benchmark_audio(case.audio, 16000)
            if rate != 16000 or not len(samples):
                raise ValueError(f"invalid decoded audio: {case.audio}")
            audio[case.id] = samples
            for preset in presets:
                cuts[(case.id, preset)] = capture_segments(samples, preset)
        except Exception as exc:
            audio.pop(case.id, None)
            failures.append(f"{case.id}: audio preparation failed: {exc}")

    records = [row for row in records if row["id"] in audio]
    completed_rows = {record_key(row): row for row in records}
    for model in models:
        for preset in presets:
            fast = preset == "fast"
            runtime_device = "cpu" if fast else device
            runtime_compute_type = "int8" if fast else compute_type
            cpu_threads = 1 if fast else 2
            config = config_class(model_size=model, active_model_size=model,
                                  english_model_size=model, fast_english_model_size=model,
                                  device=runtime_device, compute_type=runtime_compute_type,
                                  auto_cpu_threads=False, cpu_threads=cpu_threads,
                                  num_workers=1, language="en", beam_size=beam_sizes[preset],
                                  local_files_only=not allow_download)
            recognizer = None
            try:
                recognizer = recognizer_class(config)
                if not allow_download and hasattr(recognizer, "_model_repo_id"):
                    repo_id = recognizer._model_repo_id()
                    if repo_id:
                        local_model = recognizer._modelscope_model_dir(repo_id)
                        if recognizer._snapshot_has_required_model_files(str(local_model)):
                            recognizer._model_path = str(local_model)
                        else:
                            try:
                                from huggingface_hub import snapshot_download

                                cached = snapshot_download(repo_id, cache_dir=str(recognizer._model_dir),
                                                           local_files_only=True)
                                if recognizer._snapshot_has_required_model_files(cached):
                                    recognizer._model_path = cached
                            except (ImportError, OSError, ValueError):
                                pass
                recognizer.initialize()
                if recognizer._loaded_model_size != model:
                    raise RuntimeError(f"requested {model}, loaded {recognizer._loaded_model_size}")
                model_fingerprint = _model_fingerprint(recognizer)
                stale = [row for row in records if row["model"] == model and row["preset"] == preset and (
                    (hasattr(recognizer, "_model_path") and
                     (not model_fingerprint or row.get("model_fingerprint") != model_fingerprint)) or
                    row["device"] != recognizer.runtime_device or
                    row["compute_type"] != recognizer.runtime_compute_type or
                    row.get("cpu_threads", cpu_threads) != cpu_threads)]
                if stale:
                    stale_ids = {id(row) for row in stale}
                    records = [row for row in records if id(row) not in stale_ids]
                    completed_rows = {record_key(row): row for row in records}
                for prompt in prompts:
                    config.prompt_profile = prompt if prompt != "off" else "none"
                    prompt_text = (recognizer._initial_prompt()
                                   if hasattr(recognizer, "_initial_prompt") else None)
                    for case in cases:
                        if case.id not in audio:
                            continue
                        samples = audio[case.id]
                        captured_segments = cuts[(case.id, preset)]
                        paths = (("whole", [samples.tobytes()], [None]),
                                 ("capture_cut", [seg.audio_data for seg in captured_segments],
                                  captured_segments))
                        for path, chunks, capture_metadata in paths:
                            key = (case.id, model, preset, prompt, path)
                            if key in completed_rows:
                                continue
                            pieces = []
                            raw_pieces = []
                            segment_diagnostics = []
                            guarded_any = False
                            elapsed = 0.0
                            try:
                                offset_seconds = 0.0
                                for index, (chunk, capture_segment) in enumerate(zip(chunks, capture_metadata)):
                                    started = time.perf_counter()
                                    result = recognizer.transcribe_audio_bytes_with_language(
                                        chunk, sample_rate=16000, language_override="en")
                                    segment_elapsed = time.perf_counter() - started
                                    elapsed += segment_elapsed
                                    text = str(getattr(result, "text", "") or "")
                                    raw_text = str(getattr(result, "raw_text", text) or "")
                                    pieces.append(text)
                                    raw_pieces.append(raw_text)
                                    guarded_any = guarded_any or bool(getattr(result, "runaway_guarded", False))
                                    diagnostic = _segment_diagnostic(
                                        chunk, result, index, offset_seconds, prompt, config,
                                        capture_segment=capture_segment,
                                        inference_seconds=segment_elapsed,
                                        prompt_text=prompt_text)
                                    if not hasattr(result, "raw_text"):
                                        diagnostic["raw_text"] = raw_text
                                    segment_diagnostics.append(diagnostic)
                                    offset_seconds += len(chunk) / (2 * 16000)
                                record = score_record(case, model, preset, prompt, path,
                                                      " ".join(pieces).strip(), elapsed, len(chunks),
                                                      recognizer.runtime_device, recognizer.runtime_compute_type,
                                                      config.beam_size, model_fingerprint, cpu_threads,
                                                      segment_diagnostics=segment_diagnostics,
                                                      raw_hypothesis=" ".join(raw_pieces).strip(),
                                                      runaway_guarded=guarded_any)
                                records.append(record)
                                completed_rows[key] = record
                                if on_progress:
                                    on_progress(records, failures)
                            except Exception as exc:
                                failures.append(f"{model}/{preset}/{prompt}/{case.id}/{path}: {exc}")
            except Exception as exc:
                records = [row for row in records if not (row["model"] == model and row["preset"] == preset)]
                completed_rows = {record_key(row): row for row in records}
                failures.append(f"{model}/{preset}: model unavailable: {exc}")
            finally:
                if recognizer is not None:
                    recognizer.cleanup()
    return records, failures


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("diagnostics/asr-benchmark"))
    parser.add_argument("--models", nargs="+", default=["base.en", "small.en"])
    parser.add_argument("--presets", nargs="+", choices=PRESETS, default=["fast", "balanced"])
    parser.add_argument("--prompts", nargs="+", choices=PROMPTS, default=list(PROMPTS))
    parser.add_argument("--device", choices=["cpu", "cuda", "auto"], default="auto")
    parser.add_argument("--compute-type", default="default")
    parser.add_argument("--allow-download", action="store_true", help="Allow missing Whisper models to download")
    parser.add_argument("--resume", action="store_true", help="Reuse matching successful records from the output report")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args(argv)
    if args.limit < 0:
        parser.error("--limit must be non-negative")
    logger.remove()
    logger.add(sys.stderr, level="WARNING")
    logger.disable("voxgo.audio.capture")
    cases = load_manifest(args.manifest, args.limit)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    metadata = {"created_at": datetime.now(timezone.utc).isoformat(),
                "cases": len(cases), "manifest": str(args.manifest.resolve()),
                "manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
                "sources": sorted({case.source for case in cases}),
                "models": args.models, "presets": args.presets, "prompts": args.prompts,
                "device_requested": args.device, "compute_type_requested": args.compute_type,
                "allow_download": args.allow_download,
                "benchmark_version": 4,
                "case_ids_sha256": hashlib.sha256("\0".join(case.id for case in cases).encode("utf-8")).hexdigest(),
                "audio_sha256": _hash_files([case.audio for case in cases]),
                "implementation_sha256": _hash_files([
                    Path(__file__), Path(__file__).resolve().parents[1] / "voxgo/asr/whisper_engine.py",
                    Path(__file__).resolve().parents[1] / "voxgo/asr/runaway_repetition.py",
                    Path(__file__).resolve().parents[1] / "voxgo/audio/capture.py",
                    Path(__file__).resolve().parents[1] / "voxgo/audio/benchmark.py",
                    Path(__file__).resolve().parents[1] / "voxgo/config/loader.py",
                ])}
    existing_records = []
    report_path = args.output_dir / "report.json"
    if args.resume and report_path.is_file():
        previous = json.loads(report_path.read_text(encoding="utf-8"))
        keys = ("manifest_sha256", "models", "presets", "prompts", "device_requested",
                "compute_type_requested", "allow_download", "benchmark_version", "cases",
                "case_ids_sha256", "audio_sha256", "implementation_sha256")
        if any(previous.get("metadata", {}).get(key) != metadata[key] for key in keys):
            parser.error("--resume report does not match the manifest or benchmark settings")
        existing_records = previous.get("records", [])
        print(f"Resuming {len(existing_records)} completed results", flush=True)

    def write_report(records: list, failures: list, html_report: bool = False) -> None:
        summary = summarize(records)
        report = {"metadata": metadata, "summary": summary, "records": records, "failures": failures}
        temporary = report_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(report_path)
        if html_report:
            (args.output_dir / "report.html").write_text(
                render_html(summary, records, failures, metadata), encoding="utf-8")

    def checkpoint(records: list, failures: list) -> None:
        if len(records) % 20 == 0:
            write_report(records, failures)
            print(f"Completed {len(records)} results", flush=True)

    try:
        records, failures = run(cases, args.models, args.presets, args.prompts,
                                args.device, args.compute_type, args.allow_download,
                                existing_records=existing_records, on_progress=checkpoint)
    except (ImportError, OSError) as exc:
        records, failures = existing_records, [f"ASR runtime unavailable: {exc}"]
    write_report(records, failures, html_report=True)
    print(f"ASR benchmark: {len(records)} results, {len(failures)} failures; {args.output_dir / 'report.html'}")
    return 0 if records and not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
