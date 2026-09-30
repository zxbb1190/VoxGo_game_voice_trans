"""Select natural-speech regressions and replay them through the live ASR chain.

This is an experiment harness. Variants override only the benchmark instance;
product presets and the application's SpeechPipeline defaults stay unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from loguru import logger

from scripts.run_asr_benchmark import load_manifest, run, summarize


GROUPS = {
    "libri_fast": ("natural-fast-isolated", "librispeech_manifest.jsonl", "base.en", "fast"),
    "libri_balanced": ("natural-balanced-isolated", "librispeech_manifest.jsonl", "small.en", "balanced"),
    "ami_fast": ("ami-fast-isolated", "ami_manifest.jsonl", "base.en", "fast"),
    "ami_balanced": ("ami-balanced-isolated", "ami_manifest.jsonl", "small.en", "balanced"),
}


def select_failures(report_root: Path, manifest_root: Path) -> list[dict]:
    selected = []
    for group, (report_dir, manifest_name, model, preset) in GROUPS.items():
        report = json.loads((report_root / report_dir / "report.json").read_text(encoding="utf-8"))
        if report["failures"]:
            raise ValueError(f"baseline report has failures: {report_dir}")
        by_case = defaultdict(dict)
        for row in report["records"]:
            by_case[(row["id"], row["snr_db"])][row["path"]] = row
        manifest = manifest_root / manifest_name
        cases = {case.id: case for case in load_manifest(manifest)}
        for snr in (None, 20.0, 0.0):
            candidates = []
            for (case_id, row_snr), paths in by_case.items():
                if row_snr != snr or set(paths) != {"whole", "capture_cut", "full_pipeline"}:
                    continue
                whole, cut, full = (paths[path] for path in ("whole", "capture_cut", "full_pipeline"))
                cut_delta = cut["normalized_errors"] - whole["normalized_errors"]
                full_delta = full["normalized_errors"] - whole["normalized_errors"]
                pipeline_delta = full["normalized_errors"] - cut["normalized_errors"]
                candidates.append((case_id, paths, cut_delta, full_delta, pipeline_delta))
            if not candidates:
                raise ValueError(f"missing equal-path stratum: {group}/{snr}")
            # One capture regression and one additional Pipeline loss per stratum.
            capture = max(candidates, key=lambda item: (
                min(item[2], item[3]), item[2] + item[3],
                -item[1]["whole"]["normalized_errors"], item[0]))
            others = [item for item in candidates if item[0] != capture[0]]
            pipeline = max(others, key=lambda item: (
                item[4], item[3], -item[1]["whole"]["normalized_errors"], item[0]))
            for role, item in (("capture_regression", capture), ("pipeline_extra", pipeline)):
                case_id, paths, cut_delta, full_delta, pipeline_delta = item
                case = cases[case_id]
                selected.append({
                    "group": group, "role": role, "id": case_id,
                    "model": model, "preset": preset, "snr_db": snr,
                    "manifest": str(manifest.resolve()), "audio": str(case.audio),
                    "reference": case.reference, "source": case.source,
                    "baseline": {path: {
                        "hypothesis": row["hypothesis"], "normalized_errors": row["normalized_errors"],
                        "deletions": row["deletions"], "inference_seconds": row["inference_seconds"],
                    } for path, row in paths.items()},
                    "capture_extra_errors": cut_delta,
                    "pipeline_extra_errors": pipeline_delta,
                    "full_extra_errors": full_delta,
                })
    return selected


def select_holdout(report_root: Path, manifest_root: Path,
                   failures: list[dict], per_stratum: int = 2) -> list[dict]:
    excluded = {(row["group"], row["id"]) for row in failures}
    selected = []
    for group, (report_dir, manifest_name, model, preset) in GROUPS.items():
        report = json.loads((report_root / report_dir / "report.json").read_text(encoding="utf-8"))
        if report["failures"]:
            raise ValueError(f"baseline report has failures: {report_dir}")
        by_case = defaultdict(dict)
        for row in report["records"]:
            by_case[(row["id"], row["snr_db"])][row["path"]] = row
        manifest = manifest_root / manifest_name
        cases = {case.id: case for case in load_manifest(manifest)}
        for snr in (None, 20.0, 0.0):
            candidates = [
                (case_id, paths) for (case_id, row_snr), paths in by_case.items()
                if row_snr == snr and (group, case_id) not in excluded
                and set(paths) == {"whole", "capture_cut", "full_pipeline"}
            ]
            candidates.sort(key=lambda item: hashlib.sha256(
                f"asr-chain-holdout-20260930/{group}/{item[0]}".encode()).hexdigest())
            if len(candidates) < per_stratum:
                raise ValueError(f"insufficient holdout cases: {group}/{snr}")
            for case_id, paths in candidates[:per_stratum]:
                case = cases[case_id]
                selected.append({
                    "group": group, "role": "holdout", "id": case_id,
                    "model": model, "preset": preset, "snr_db": snr,
                    "manifest": str(manifest.resolve()), "audio": str(case.audio),
                    "reference": case.reference, "source": case.source,
                    "baseline": {path: {
                        "hypothesis": row["hypothesis"], "normalized_errors": row["normalized_errors"],
                        "deletions": row["deletions"], "inference_seconds": row["inference_seconds"],
                    } for path, row in paths.items()},
                })
    return selected


def variant_settings(variant: str, preset: str) -> tuple[dict, dict, str | None, str | None, str | None, tuple]:
    if variant == "baseline":
        return {}, {}, None, None, None, ("whole", "capture_cut", "full_pipeline")
    if variant == "capture_plus_0p5":
        return {"max_speech_seconds": 3.0 if preset == "fast" else 4.5}, {}, None, None, None, (
            "whole", "capture_cut", "full_pipeline")
    if variant == "pending_plus_0p15":
        return {}, {"pending_timeout_seconds": 0.35 if preset == "fast" else 0.50}, None, None, None, (
            "full_pipeline",)
    if variant == "busy_stale_plus_0p5":
        return {}, {"busy_weak_stale_seconds": 1.80 if preset == "fast" else 2.10}, None, None, None, (
            "full_pipeline",)
    if variant == "weak_cooldown_zero":
        return {}, {"weak_cooldown_seconds": 0.0}, None, None, None, ("full_pipeline",)
    if variant == "filter_confident_short":
        return {}, {}, "confident_short", None, None, ("full_pipeline",)
    if variant == "preserve_weak_0p4":
        return {}, {}, None, "preserve_voice_0p4", None, ("full_pipeline",)
    if variant == "merge_voice_1p0":
        return {}, {}, None, None, "pending_voice_1p0", ("full_pipeline",)
    raise ValueError(variant)


def replay(selection: list[dict], variant: str, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    all_records, all_failures = [], []
    for group, (_report_dir, _manifest_name, model, preset) in GROUPS.items():
        chosen = [item for item in selection if item["group"] == group]
        if not chosen:
            continue
        manifest = Path(chosen[0]["manifest"])
        wanted = {item["id"] for item in chosen}
        cases = [case for case in load_manifest(manifest) if case.id in wanted]
        if len(cases) != len(wanted):
            raise ValueError(f"selected cases missing from {manifest}")
        (audio_overrides, policy_overrides, filter_override,
         budget_override, merge_override, paths) = variant_settings(variant, preset)
        records, failures = run(
            cases, [model], [preset], ["off"], "cpu", "int8", False,
            paths=paths, diagnostic_trace=True,
            audio_overrides=audio_overrides, policy_overrides=policy_overrides,
            filter_override=filter_override, budget_override=budget_override,
            merge_override=merge_override,
        )
        for row in records:
            row["experiment_group"] = group
            row["variant"] = variant
        all_records.extend(records)
        all_failures.extend(f"{group}: {failure}" for failure in failures)
        payload = {"variant": variant, "selection": selection,
                   "summary": summarize(all_records), "records": all_records,
                   "failures": all_failures}
        (output / "report.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{group}: {len(records)} records, {len(failures)} failures", flush=True)
    if all_failures:
        raise RuntimeError(f"{len(all_failures)} ASR failures; see {output / 'report.json'}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    select = sub.add_parser("select")
    select.add_argument("--report-root", type=Path, default=Path("diagnostics/asr-benchmark"))
    select.add_argument("--manifest-root", type=Path, default=Path("data/asr_benchmark"))
    select.add_argument("--output", type=Path, required=True)
    holdout = sub.add_parser("select-holdout")
    holdout.add_argument("--report-root", type=Path, default=Path("diagnostics/asr-benchmark"))
    holdout.add_argument("--manifest-root", type=Path, default=Path("data/asr_benchmark"))
    holdout.add_argument("--failure-selection", type=Path, required=True)
    holdout.add_argument("--output", type=Path, required=True)
    experiment = sub.add_parser("run")
    experiment.add_argument("--selection", type=Path, required=True)
    experiment.add_argument("--variant", required=True, choices=(
        "baseline", "capture_plus_0p5", "pending_plus_0p15",
        "busy_stale_plus_0p5", "weak_cooldown_zero", "filter_confident_short",
        "preserve_weak_0p4", "merge_voice_1p0"))
    experiment.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "select":
        rows = select_failures(args.report_root, args.manifest_root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"selected {len(rows)} paired natural-speech regressions: {args.output}")
    elif args.command == "select-holdout":
        rows = select_holdout(
            args.report_root, args.manifest_root,
            json.loads(args.failure_selection.read_text(encoding="utf-8")))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"selected {len(rows)} untouched natural-speech controls: {args.output}")
    else:
        # The per-case trace is saved in JSON; avoid streaming every VAD block
        # to the terminal during real-time replay.
        logger.remove()
        replay(json.loads(args.selection.read_text(encoding="utf-8")), args.variant, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
