"""Turn a traced ASR A/B report into per-case evidence and bounded error categories."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


ACTIVITY_RE = re.compile(r"audio activity: rms=([-\d.]+).*?vad=(True|False).*?energy=(True|False).*?active=(True|False)")
KEY_MESSAGES = (
    "candidate accepted:", "candidate low confidence:", "candidate dropped:",
    "segment pending:", "segment pending timeout:", "segment merged:",
    "queue busy", "speech queue", "weak candidate dropped by asr budget",
    "candidate dropped before whisper:", "sent to whisper:",
    "filtered transcription:", "empty asr:", "[recognition]",
)


def classify_capture(full: dict, cut_extra: int) -> str:
    if cut_extra <= 0:
        return "no_capture_regression"
    events = full.get("captured_events", [])
    reasons = [event.get("reason", "") for event in events]
    if any("达到最长" in reason or "达到块数上限" in reason for reason in reasons):
        return "forced_duration_split"
    if len(events) >= 3 and sum(event["duration_seconds"] < 1.5 for event in events) >= 2:
        return "fragmented_short_segments"
    if full.get("snr_db") == 0.0 and any(
        event["vad_voice_blocks"] == 0 and event["energy_voice_blocks"] > 0 for event in events
    ):
        return "noise_energy_only_vad"
    return "segment_context_or_whisper"


def classify_pipeline(full: dict, pipeline_extra: int) -> str:
    if pipeline_extra <= 0:
        return "no_pipeline_regression"
    messages = [entry["message"] for entry in full.get("trace_events", [])]
    if any("dropped by asr budget" in message for message in messages):
        return "weak_candidate_budget_drop"
    if any("queue full" in message and "dropped" in message for message in messages):
        return "queue_capacity_drop"
    if any("queue busy weak candidate dropped" in message for message in messages):
        return "busy_weak_stale_drop"
    if any("candidate dropped before whisper" in message for message in messages):
        return "pre_asr_filter"
    if any("filtered transcription:" in message for message in messages):
        return "post_asr_filter"
    if any("segment merged:" in message for message in messages):
        return "candidate_merge"
    return "pipeline_order_or_other"


def activity_counts(full: dict) -> dict:
    events = full.get("captured_events", [])
    duration = 0.12 if full["preset"] == "fast" else 0.20
    blocks = []
    for entry in full.get("trace_events", []):
        match = ACTIVITY_RE.search(entry["message"])
        if match:
            blocks.append((float(match.group(1)), match.group(2) == "True",
                           match.group(3) == "True", match.group(4) == "True"))
    active_uncovered = 0
    for index, (_rms, _vad, _energy, active) in enumerate(blocks):
        midpoint = (index + 0.5) * duration
        if active and not any((event.get("source_start_seconds") or 0) <= midpoint <
                              (event.get("source_end_seconds") or 0) for event in events):
            active_uncovered += 1
    return {"blocks": len(blocks), "active": sum(block[3] for block in blocks),
            "active_outside_capture": active_uncovered}


def review(report: dict) -> tuple[list[dict], dict]:
    records = {}
    for row in report["records"]:
        key = (row["experiment_group"], row["id"])
        records.setdefault(key, {})[row["path"]] = row
    rows = []
    category_cases = Counter()
    category_extra_words = Counter()
    for selected in report["selection"]:
        group, case_id = selected["group"], selected["id"]
        paths = records[(group, case_id)]
        if set(paths) != {"whole", "capture_cut", "full_pipeline"}:
            raise ValueError(f"incomplete traced baseline: {group}/{case_id}")
        whole, cut, full = (paths[name] for name in ("whole", "capture_cut", "full_pipeline"))
        cut_extra = cut["normalized_errors"] - whole["normalized_errors"]
        pipeline_extra = full["normalized_errors"] - cut["normalized_errors"]
        capture_category = classify_capture(full, cut_extra)
        pipeline_category = classify_pipeline(full, pipeline_extra)
        for category, weight in ((capture_category, cut_extra), (pipeline_category, pipeline_extra)):
            if weight > 0:
                category_cases[category] += 1
                category_extra_words[category] += weight
        messages = [entry for entry in full.get("trace_events", [])
                    if any(marker in entry["message"] for marker in KEY_MESSAGES)]
        rows.append({
            "group": group, "snr_db": selected["snr_db"], "role": selected["role"],
            "id": case_id, "audio": selected["audio"], "reference": selected["reference"],
            "whole": whole["hypothesis"], "capture_cut": cut["hypothesis"],
            "full_pipeline": full["hypothesis"],
            "normalized_errors": {name: paths[name]["normalized_errors"] for name in paths},
            "deletions": {name: paths[name]["deletions"] for name in paths},
            "capture_extra_errors": cut_extra, "pipeline_extra_errors": pipeline_extra,
            "capture_category": capture_category, "pipeline_category": pipeline_category,
            "capture_events": full["captured_events"],
            "capture_whisper": cut["segment_diagnostics"],
            "pipeline_whisper": full["segment_diagnostics"],
            "pipeline_events": full.get("output_events", []),
            "queue_events": [event for event in full.get("queue_events", [])
                             if event.get("audio_sha256")],
            "pipeline_decisions": messages,
            "activity": activity_counts(full),
            "pipeline_stats": full.get("pipeline_stats", {}),
        })
    return rows, {"case_count": len(rows), "category_cases": dict(category_cases),
                  "positive_extra_words": dict(category_extra_words)}


def render_markdown(rows: list[dict], summary: dict) -> str:
    lines = ["# ASR 实时链路失败样本审阅", "", f"样本数：{summary['case_count']}。分类是观察到的关联层，不是严格的逐词因果归因。", ""]
    lines += ["| 类别 | 关联样本数 | 正向额外错词数 |", "| --- | ---: | ---: |"]
    for category, count in sorted(summary["category_cases"].items(), key=lambda item: -item[1]):
        lines.append(f"| {category} | {count} | {summary['positive_extra_words'][category]} |")
    for row in rows:
        lines.extend([
            "", f"## {row['group']} / {row['snr_db']} / {row['id']}", "",
            f"- 音频：`{row['audio']}`",
            f"- 选择原因：`{row['role']}`；capture 关联分类：`{row['capture_category']}`；Pipeline 关联分类：`{row['pipeline_category']}`",
            f"- 规范化错词数 whole/cut/full：{row['normalized_errors']['whole']}/{row['normalized_errors']['capture_cut']}/{row['normalized_errors']['full_pipeline']}；漏词数：{row['deletions']['whole']}/{row['deletions']['capture_cut']}/{row['deletions']['full_pipeline']}",
            f"- 逐块活动：{row['activity']}",
            f"- 标准答案：{row['reference']}",
            f"- whole：{row['whole']}",
            f"- capture_cut：{row['capture_cut']}",
            f"- full_pipeline：{row['full_pipeline']}",
            "", "| # | 源音频边界 | 时长 / 有声 | RMS / 峰值 / 门限 | VAD/能量块 | 切段原因 | 逐段 Whisper |",
            "| ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ])
        for index, event in enumerate(row["capture_events"]):
            text = row["capture_whisper"][index]["guarded_text"] if index < len(row["capture_whisper"]) else ""
            boundary = (f"{event['source_start_seconds']:.2f}–{event['source_end_seconds']:.2f}s"
                        if event["source_boundary_exact"] else "unknown")
            lines.append(f"| {index} | {boundary} | {event['duration_seconds']:.2f}/{event['voice_duration_seconds']:.2f}s | "
                         f"{event['rms_dbfs']:.1f}/{event['peak_rms_dbfs']:.1f}/{event['energy_threshold_dbfs']:.1f}dBFS | "
                         f"{event['vad_voice_blocks']}/{event['energy_voice_blocks']} | {event['reason']} | {text.replace('|', '/')} |")
        lines += ["", "队列实际入队/工作线程出队：", ""]
        for event in row["queue_events"]:
            lines.append(
                f"- {event['seconds_from_start']:.2f}s {event['action']} "
                f"sha={event['audio_sha256'][:12]} voice={event['voice_duration_seconds']:.2f}s "
                f"size={event['queue_size_after']} labels={','.join(event['labels'])}"
            )
        lines += ["", "最终输出事件：", ""]
        for event in row["pipeline_events"]:
            lines.append(f"- {event['seconds_from_start']:.2f}s {event['text']}")
        lines += ["", "Pipeline 关键决策（含丢弃和过滤原因）：", ""]
        for item in row["pipeline_decisions"]:
            lines.append(f"- {item['seconds_from_start']:.2f}s `{item['component']}`: {item['message']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows, summary = review(json.loads(args.report.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(rows, summary), encoding="utf-8")
    args.output.with_suffix(".json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
