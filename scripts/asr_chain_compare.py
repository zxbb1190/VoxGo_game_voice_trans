"""Compare traced, equal-case ASR chain A/B runs against their own baseline."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def summarize_rows(rows: list[dict]) -> dict:
    normalized_words = sum(row["normalized_reference_words"] for row in rows)
    reference_words = sum(row["reference_words"] for row in rows)
    result = {
        "cases": len(rows),
        "normalized_wer": sum(row["normalized_errors"] for row in rows) / normalized_words,
        "deletion_rate": sum(row["deletions"] for row in rows) / reference_words,
        "normalized_errors": sum(row["normalized_errors"] for row in rows),
        "deletions": sum(row["deletions"] for row in rows),
        "asr_calls": sum(row["segments"] for row in rows),
        "asr_mean_seconds": statistics.mean(row["inference_seconds"] for row in rows),
        "asr_p95_seconds": percentile([row["inference_seconds"] for row in rows], 0.95),
        "queue_drops": sum(row.get("pipeline_stats", {}).get("dropped_speech", 0) for row in rows),
        "filtered": sum(row.get("pipeline_stats", {}).get("filtered_speech", 0) for row in rows),
        "final_repetition_failures": sum(bool(row["repetition_failure"]) for row in rows),
        "raw_repetition_failures": sum(bool(row["raw_repetition_failure"]) for row in rows),
        "runaway_guarded": sum(bool(row["runaway_guarded"]) for row in rows),
    }
    if all("wall_seconds_total" in row for row in rows):
        result.update({
            "wall_mean_seconds": statistics.mean(row["wall_seconds_total"] for row in rows),
            "wall_p95_seconds": percentile([row["wall_seconds_total"] for row in rows], 0.95),
            "cpu_mean_seconds": statistics.mean(row["process_cpu_seconds"] for row in rows),
        })
    return result


def compare(baseline: dict, variant: dict) -> dict:
    if baseline["failures"] or variant["failures"]:
        raise ValueError("comparison requires zero-failure reports")
    selected = {(row["group"], row["id"]) for row in baseline["selection"]}
    if selected != {(row["group"], row["id"]) for row in variant["selection"]}:
        raise ValueError("baseline and variant must use identical selected cases")
    base_rows = {(row["experiment_group"], row["id"], row["path"]): row
                 for row in baseline["records"]}
    variant_rows = {(row["experiment_group"], row["id"], row["path"]): row
                    for row in variant["records"]}
    if len(base_rows) != len(baseline["records"]) or len(variant_rows) != len(variant["records"]):
        raise ValueError("comparison requires unique group/case/path rows")
    variant_paths = {key[2] for key in variant_rows}
    if not variant_paths:
        raise ValueError("comparison requires identical cases for each compared path")
    expected_keys = {key for key in base_rows if key[2] in variant_paths}
    if set(variant_rows) != expected_keys:
        raise ValueError("comparison requires identical cases for each compared path")
    groups = defaultdict(list)
    for key, row in variant_rows.items():
        if key not in base_rows:
            raise ValueError(f"variant case absent from baseline: {key}")
        groups[(key[0], key[2])].append(key)
    output = {}
    for (group, path), keys in sorted(groups.items()):
        before = summarize_rows([base_rows[key] for key in keys])
        after = summarize_rows([variant_rows[key] for key in keys])
        output[f"{group}/{path}"] = {"before": before, "after": after,
                                      "wer_delta_pp": 100 * (after["normalized_wer"] - before["normalized_wer"]),
                                      "deletion_delta_pp": 100 * (after["deletion_rate"] - before["deletion_rate"])}
    return {"variant": variant["variant"], "case_count": len(selected), "groups": output}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--variants", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    reports = [compare(baseline, json.loads(path.read_text(encoding="utf-8")))
               for path in args.variants]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    for report in reports:
        print(report["variant"])
        for name, group in report["groups"].items():
            before, after = group["before"], group["after"]
            print(f"  {name}: WER {before['normalized_wer']*100:.2f}% -> {after['normalized_wer']*100:.2f}%; "
                  f"deletion {before['deletion_rate']*100:.2f}% -> {after['deletion_rate']*100:.2f}%; "
                  f"drops {before['queue_drops']} -> {after['queue_drops']}; "
                  f"ASR {before['asr_mean_seconds']:.2f}s -> {after['asr_mean_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
