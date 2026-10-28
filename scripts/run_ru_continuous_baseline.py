"""Frozen RU dev/negative baseline; reuse the existing observed production replay.

No locked/quarantine inference, no online provider or parameter search. One source
recording per fresh process makes frame ownership and recording metrics explicit.
"""
import argparse
import copy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import wave

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.offline_russian_capture_ab import create_output,local_base,offline_guard,write,run_child,fingerprint
from scripts.ru_benchmark_metrics import validate_manifest,evaluation_rows,assess,percentile


def strategy_config(models,strategy):
    if strategy not in {"legacy","language_aware"}:raise ValueError("Only existing production strategies")
    from voxgo.config.loader import default_app_config,migrate_runtime_defaults,sync_language_flow,apply_language_runtime_policy,sync_whisper_vad_limit
    from voxgo.asr.language_profiles import effective_speech_config
    config=copy.deepcopy(default_app_config())
    config.translation.source_lang,config.translation.target_lang="ru","zh"
    config.whisper.multilingual_asr_strategy=strategy
    migrate_runtime_defaults(config);sync_language_flow(config);apply_language_runtime_policy(config);sync_whisper_vad_limit(config)
    config=copy.deepcopy(effective_speech_config(config, experimental=True))
    config.whisper.model_dir=str(models.resolve());config.whisper.local_files_only=True
    if config.whisper.active_model_size!="base":raise ValueError("Expected existing RU base, no model substitution")
    return config


def input_stream(record):
    if record["split"] not in {"dev","negative"}:raise ValueError("Locked/quarantine inference forbidden")
    with wave.open(record["audio"],"rb") as wav:pcm=wav.readframes(wav.getnframes())
    if hashlib.sha256(pcm).hexdigest()!=record["pcm_sha256"]:raise ValueError("PCM changed")
    clip=copy.deepcopy(record)
    clip.update(sha256=record["wav_sha256"],stream_start_frame=48000,stream_end_frame=48000+len(pcm)//2)
    raw=b"\0"*(48000*2)+pcm+b"\0"*(48000*2)
    return [clip],raw+b"\0"*((-len(raw))%3840),len(raw)//2


def schedule(records):
    out=[]
    for index,row in enumerate(records):
        strategies=["legacy","language_aware"] if index%2==0 else ["language_aware","legacy"]
        for strategy in strategies:
            out.append(dict(id=row["id"]+"--"+strategy,record_id=row["id"],strategy=strategy,cadence_ms=100))
    return out


def require_frozen(manifest):
    if manifest.get("schema_version")!=1 or manifest.get("frozen_before_asr") is not True:
        raise ValueError("A versioned, frozen manifest is required before inference")


def child(args,safety):
    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    spec=json.loads(args.child.read_text(encoding="utf-8"))
    record=next(r for r in evaluation_rows(manifest) if r["id"]==spec["record_id"])
    config=strategy_config(args.models_directory,spec["strategy"])
    options=SimpleNamespace(child=args.child,output=args.output,manifest=args.manifest,models_directory=args.models_directory,drain_seconds=30.)
    run_child(options,replay_input=input_stream(record),app_config=config,summarize_recordings=lambda r:[],whole_clip_warmup=False,
              measurement_scope="single full-source public recording; production Capture/Pipeline/Whisper/filter; no GUI/game/API; pending references")
    result=json.loads((args.output/"result.json").read_text(encoding="utf-8"))
    events=[json.loads(l) for l in (args.output/"events.jsonl").read_text(encoding="utf-8").splitlines()]
    write(args.output/"assessment.json",assess(result,record,events))
    write(args.output/"offline-safety.json",dict(api_requests=0,**{k:v for k,v in safety.items() if k!="active"}))


def summarize(output,plan):
    rows=[json.loads((output/p["id"]/"assessment.json").read_text(encoding="utf-8")) for p in plan]
    groups=[]
    for split in ("dev","negative"):
        for strategy in ("legacy","language_aware"):
            group=[r for r in rows if r["split"]==split and r["strategy"]==strategy]
            if not group:continue
            times=[t for r in group for t in r["performance"]["asr_all_completed_ms"]]
            waits=[t for r in group for t in r["performance"]["queue_wait_all_ms"]]
            cpu=sum(r["performance"]["replay_cpu_seconds"] for r in group);seconds=sum(r["seconds"] for r in group)
            def pooled(which):
                valid=[r[which] for r in group if r[which]["proxy_cer"] is not None]
                chars=sum(m["character_counts"]["errors"] for m in valid);den=sum(m["character_counts"]["reference_characters"] for m in valid)
                words=sum(m["word_counts"]["errors"] for m in valid);wden=sum(m["word_counts"]["reference_words"] for m in valid)
                return dict(proxy_cer=chars/den if den else None,proxy_wer=words/wden if wden else None,
                            reference_characters=den,reference_words=wden,accepted_cer=None,accepted_wer=None)
            groups.append(dict(split=split,strategy=strategy,recordings=len(group),audio_seconds=seconds,
                counts={k:sum(r["counts"][k] for r in group) for k in group[0]["counts"]},
                raw_metrics=pooled("raw_metrics"),retained_metrics=pooled("retained_metrics"),translated_metrics=pooled("translated_metrics"),
                asr_p50_ms=percentile(times,.5),asr_p95_ms=percentile(times,.95),cpu_seconds=cpu,cpu_seconds_per_audio_minute=cpu/(seconds/60),
                peak_sampled_rss_mib=max(r["performance"]["peak_sampled_rss_bytes"] for r in group)/2**20,queue_wait_p95_ms=percentile(waits,.95),
                publisher_noise_raw_nonempty_recordings=sum(r["negative_raw_nonempty"] for r in group),
                publisher_noise_translation_nonempty_recordings=sum(r["negative_translation_nonempty"] for r in group)))
    summary=dict(groups=groups,recordings=rows,api_requests=0,human_semantic_accuracy=None,
                 locked_holdout_evaluated=0,quarantine_evaluated=0,reference_status="all pending; edit distances are provisional proxies",release_approved=False)
    write(output/"summary.json",summary)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--models-directory",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--child",type=Path,help=argparse.SUPPRESS)
    args=parser.parse_args()
    with offline_guard() as safety:
        manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
        require_frozen(manifest)
        registry=json.loads((args.manifest.parent/"historical-registry.json").read_text(encoding="utf-8"))
        if hashlib.sha256((args.manifest.parent/"historical-registry.json").read_bytes()).hexdigest()!=manifest["history_registry_sha256"]:
            raise ValueError("History registry changed")
        validate_manifest(manifest,historical_hashes=registry["hashes"])
        if args.child:
            child(args,safety);return
        if any(args.output.resolve().is_relative_to(p.resolve()) for p in [args.manifest.parent,ROOT/"voxgo",args.models_directory]):
            parser.error("Output must be outside corpus/runtime")
        _,model=local_base(args.models_directory)
        records=evaluation_rows(manifest);plan=schedule(records)
        output=create_output(args.output)
        initial=fingerprint();manifest_hash=hashlib.sha256(args.manifest.read_bytes()).hexdigest()
        protected={r["audio"]:r["wav_sha256"] for r in manifest["records"]}
        write(output/"plan.json",dict(schedule=plan,manifest_sha256=manifest_hash,model_files=model,fingerprint=initial,
            entrypoint_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            metrics_sha256=hashlib.sha256((ROOT/"scripts/ru_benchmark_metrics.py").read_bytes()).hexdigest(),
            unique_dev=len([r for r in records if r["split"]=="dev"]),unique_negative=len([r for r in records if r["split"]=="negative"]),
            locked_holdout_evaluated=0,quarantine_evaluated=0,no_repeats=True))
        status=dict(status="running",completed=[],api_requests=0)
        try:
            for spec in plan:
                spec_path=output/(spec["id"]+".json");write(spec_path,spec)
                print(f"Starting {len(status['completed'])+1}/{len(plan)} {spec['id']}",flush=True)
                with (output/(spec["id"]+".log")).open("x",encoding="utf-8") as log:
                    completed=subprocess.run([sys.executable,"-B","-X","utf8",str(Path(__file__).resolve()),
                        "--manifest",str(args.manifest.resolve()),"--models-directory",str(args.models_directory.resolve()),
                        "--output",str((output/spec["id"]).resolve()),"--child",str(spec_path.resolve())],cwd=ROOT,stdout=log,stderr=log,timeout=300)
                if completed.returncode:raise RuntimeError("Child failed; stop without selective retry: "+spec["id"])
                status["completed"].append(spec["id"]);write(output/"status.json",status)
            summarize(output,plan);status["status"]="complete"
        finally:
            status.update(manifest_unchanged=hashlib.sha256(args.manifest.read_bytes()).hexdigest()==manifest_hash,
                all_audio_including_quarantine_unchanged=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in protected.items()),
                sources_unchanged=initial["files"]==fingerprint()["files"],models_unchanged=model==local_base(args.models_directory)[1],
                safety={k:v for k,v in safety.items() if k!="active"})
            if status["status"]=="running":status["status"]="stopped_incomplete"
            write(output/"status.json",status)


if __name__=="__main__":main()
