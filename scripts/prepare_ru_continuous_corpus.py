"""Bounded public-data acquisition and frozen manifest preparation, never ASR.

No credentials, model downloads, user settings, or production services. All HTTP
body bytes (including failed partial downloads) share one <=100 MB ledger.
"""
from contextlib import closing
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import wave
from urllib.parse import urlsplit, urlunsplit
import urllib.request

ROOT=Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


class BudgetedFetch:
    def __init__(self, root, limit=100_000_000):
        if not 1 <= limit <= 100_000_000:
            raise ValueError("download budget must be <=100 MB")
        self.root=Path(root)
        self.root.mkdir(parents=True,exist_ok=True)
        self.path=self.root/"download-ledger.json"
        self.data=json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else dict(limit=limit,bytes=0,requests=[])
        if self.data["limit"]!=limit or self.data["bytes"]>limit:
            raise ValueError("incompatible download ledger")

    def save(self):
        temporary=self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        temporary.replace(self.path)

    def get(self, label, url, relative):
        parsed=urlsplit(url)
        if parsed.scheme!="https" or parsed.username or parsed.password:
            raise ValueError("public HTTPS data only")
        target=(self.root/relative).resolve()
        if not target.is_relative_to(self.root.resolve()) or target.exists():
            raise ValueError("unsafe path or existing download; no overwrite")
        target.parent.mkdir(parents=True,exist_ok=True)
        row=dict(label=label,url=urlunsplit((parsed.scheme,parsed.netloc,parsed.path,"","")),
                 request_url_sha256=sha(url.encode()),path=str(target),bytes=0,status="started")
        self.data["requests"].append(row);self.save()
        request=urllib.request.Request(url,headers={"User-Agent":"VoxGo-local-research/0.5.3","Accept-Encoding":"identity"})
        try:
            with closing(urllib.request.urlopen(request,timeout=40)) as response:
                length=response.headers.get("Content-Length")
                if length and int(length)>self.data["limit"]-self.data["bytes"]:
                    raise ValueError("Response exceeds remaining download budget")
                with target.open("xb") as out:
                    while True:
                        remaining=self.data["limit"]-self.data["bytes"]
                        if remaining<=0:
                            raise ValueError("Download budget exhausted; partial data not usable")
                        block=response.read(min(65536,remaining))
                        if not block:break
                        out.write(block);row["bytes"]+=len(block);self.data["bytes"]+=len(block);self.save()
                if length and row["bytes"]!=int(length):
                    raise ValueError("Incomplete HTTP body")
                row.update(status="complete",sha256=sha(target.read_bytes()))
                return target
        except Exception as exc:
            row.update(status="failed",error_type=type(exc).__name__)
            raise
        finally:self.save()


def cached(fetch,label,url,relative):
    path=fetch.root/relative
    if path.exists():
        records=[r for r in fetch.data["requests"] if r.get("path")==str(path.resolve()) and r.get("status")=="complete"]
        if not records or records[-1]["sha256"]!=sha(path.read_bytes()):
            raise ValueError("cached input is not a verified completed download")
        return path
    return fetch.get(label,url,relative)


def historical_registry(output_root):
    """Conservatively exclude every hash/id mentioned by prior test evidence."""
    hashes,ids,sources=set(),set(),[]
    roots=[ROOT/"docs/testing/evidence",ROOT/"build/multilingual-online",ROOT/"tests/assets",
           Path("E:/my/my/game_voice_translator/docs/testing")]
    def walk(value):
        if isinstance(value,dict):
            for key,item in value.items():
                if isinstance(item,str):
                    if re.fullmatch(r"[a-f0-9]{64}",item):hashes.add(item)
                    if key in {"id","sample_id","original_member"}:ids.add(item)
                walk(item)
        elif isinstance(value,list):
            for item in value:walk(item)
    for root in roots:
        for path in sorted(root.rglob("*.json")):
            if path.resolve().is_relative_to(output_root.resolve()) or path.stat().st_size>12_000_000:continue
            try:
                data=path.read_bytes();walk(json.loads(data.decode("utf-8-sig")))
                sources.append(dict(path=str(path),sha256=sha(data)))
            except (ValueError,UnicodeError):continue
    return dict(hashes=sorted(hashes),ids=sorted(ids),evidence_files=sources,
                scope="Prior manifests/results, not user/private audio directories; conservative hash exclusion, not a claim of verified speaker novelty")


def convert_audio(original,output,*,max_seconds=None):
    import numpy as np
    import soundfile as sf
    import soxr
    samples,rate=sf.read(str(original),dtype="float32",always_2d=True)
    if not np.isfinite(samples).all() or samples.shape[1]>2:
        raise ValueError("Unsupported/non-finite audio")
    source_frames=len(samples)
    end=source_frames if max_seconds is None else min(source_frames,int(max_seconds*rate))
    mono=samples[:end].mean(axis=1)
    if rate!=16000:mono=soxr.resample(mono,rate,16000,quality="HQ")
    pcm=np.rint(np.clip(mono,-1.,32767/32768)*32768).astype("<i2").tobytes()
    if not pcm or not np.any(np.frombuffer(pcm,dtype="<i2")):
        raise ValueError("Empty/all-zero input is not a new independent recording")
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():raise FileExistsError(output)
    with wave.open(str(output),"wb") as wav:
        wav.setparams((1,2,16000,0,"NONE","not compressed"));wav.writeframes(pcm)
    return dict(wav_sha256=sha(output.read_bytes()),pcm_sha256=sha(pcm),sample_rate=16000,frames=len(pcm)//2,
        seconds=len(pcm)/32000,original_sample_rate=rate,original_frames=source_frames,selected_original_frames=[0,end],
        conversion="mono mean; soxr HQ resample if needed; PCM16 round/clip; no gain or denoise; never concatenate recordings")


def build_corpus(root,*,download=False):
    root=Path(root).resolve()
    if (root/"manifest.json").exists():raise FileExistsError("Frozen corpus manifest already exists")
    if not download:raise ValueError("Explicit --download required for public data acquisition")
    fetch=BudgetedFetch(root)
    registry=historical_registry(root)
    (root/"historical-registry.json").write_text(json.dumps(registry,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    known=set(registry["hashes"]);new_hashes=set()
    minds_revision="40ce77cb32a384e4d50a568e1ec39ac804019d33"
    musan_revision="76f9882cfa4475efe11508ac9aa32722f84ca5b7"
    minds_card=cached(fetch,"minds-card-pinned",f"https://huggingface.co/datasets/PolyAI/minds14/raw/{minds_revision}/README.md","sources/minds-pinned-card.md")
    noise_license=cached(fetch,"noise-license-pinned",f"https://huggingface.co/datasets/corypaik/musan/raw/{musan_revision}/licenses/noise/free-sound/LICENSE","sources/noise-pinned-license.txt")
    if "cc-by-4.0" not in minds_card.read_text(encoding="utf-8") or "Public Domain" not in noise_license.read_text(encoding="utf-8"):
        raise ValueError("Expected public data licenses not confirmed")
    all_rows=[]
    for offset in range(0,539,100):
        path=cached(fetch,f"minds-page-{offset}",f"https://datasets-server.huggingface.co/rows?dataset=PolyAI%2Fminds14&config=ru-RU&split=train&offset={offset}&length={min(100,539-offset)}",f"sources/minds-page-{offset}.json")
        all_rows+=json.loads(path.read_text(encoding="utf-8"))["rows"]
    # Select BEFORE any model run: spread across intents, prefer longer texts.
    eligible=[r for r in all_rows if len(r["row"]["transcription"].split())>=18]
    buckets={}
    for row in eligible:buckets.setdefault(row["row"]["intent_class"],[]).append(row)
    selected=[]
    while len(selected)<24 and any(buckets.values()):
        for intent in sorted(buckets):
            if buckets[intent] and len(selected)<24:selected.append(buckets[intent].pop(0))
    if len(selected)<24:raise ValueError("Fewer than 24 eligible independent source files; retain acquisition evidence")
    rows=[]
    def add(record,asset_url):
        original=cached(fetch,record["id"],asset_url,"original/"+record["id"]+".audio")
        data=convert_audio(original,root/"audio"/(record["id"]+".wav"),max_seconds=12 if record["split"]=="negative" else None)
        if data["wav_sha256"] in known or data["pcm_sha256"] in known or data["pcm_sha256"] in new_hashes:
            raise ValueError("Historical/duplicate recording hash; do not relabel as unseen")
        new_hashes.add(data["pcm_sha256"])
        record.update(data,audio=str(root/"audio"/(record["id"]+".wav")),original_file=str(original),
                      original_sha256=sha(original.read_bytes()),historical_match=False)
        rows.append(record)
        (root/"acquisition-progress.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for number,entry in enumerate(selected):
        row=entry["row"];reserved=number>=16
        add(dict(id=f"minds14-ru-{entry['row_idx']:04d}",language="ru",split="quarantine" if reserved else "dev",
            intended_split="locked_holdout" if reserved else "dev",lock_eligible=False,
            speaker_id=None,speaker_group="minds14:unknown-all",source_recording_id="minds14:"+row["path"],
            source_group="minds14:unknown-session-all",speaker_isolation_status="unavailable; quarantine cannot be accepted as locked holdout",
            source_dataset="PolyAI/minds14",source_revision=minds_revision,source_member=row["path"],source_row=entry["row_idx"],
            source_url=f"https://huggingface.co/datasets/PolyAI/minds14/tree/{minds_revision}",license="CC-BY-4.0",
            license_source=f"https://huggingface.co/datasets/PolyAI/minds14/blob/{minds_revision}/README.md",
            attribution="Daniela Gerz et al.; PolyAI; MInDS-14 (2021), source contributors",
            reference_text=row["transcription"],reference_status="pending_human_review",reference_origin="publisher supplied; mixed expert/crowd/machine annotation per dataset card",
            reference_audio_coverage="unverified",reference_alignment="whole_source_file_only",semantic_annotation_status="pending",
            semantic_labels=dict(entities=[],numbers=[],negation=[],relations=[],tail=[]),
            scene=["crowdsourced_e_banking_query","continuous_single_source_file","narrowband_8khz","not_game"],
            multi_sentence_status="pending",human_quality_review="pending"),row["audio"][0]["src"])
    noise_path=cached(fetch,"musan-noise-rows","https://datasets-server.huggingface.co/rows?dataset=corypaik%2Fmusan&config=noise&split=train&offset=0&length=12","sources/musan-noise-rows.txt")
    negatives=json.loads(noise_path.read_text(encoding="utf-8"))["rows"]
    for entry in negatives:
        row=entry["row"]
        if row["source"]!="free-sound" or row["label"]!=2:raise ValueError("Only the explicit public-domain noise subset is selected")
        add(dict(id=Path(row["path"]).stem,language=None,split="negative",intended_split="negative",lock_eligible=False,
            speaker_id=None,speaker_group=None,source_recording_id="musan:"+row["path"],source_group="musan:"+row["path"],
            source_dataset="corypaik/musan",source_revision=musan_revision,source_member=row["path"],source_row=entry["row_idx"],
            source_url=f"https://huggingface.co/datasets/corypaik/musan/tree/{musan_revision}",license="Public-Domain-source-declaration",
            license_source=f"https://huggingface.co/datasets/corypaik/musan/blob/{musan_revision}/licenses/noise/free-sound/LICENSE",
            attribution="MUSAN: David Snyder, Guoguo Chen, Daniel Povey (2015); FreeSound contributors; original PD declaration preserved",
            reference_text="",reference_status="pending_absence_review",reference_alignment="no speech reference",
            semantic_annotation_status="pending",semantic_labels=dict(entities=[],numbers=[],negation=[],relations=[],tail=[]),
            scene=["publisher_label_noise","environmental_audio","not_game","first_12s_max"],human_quality_review="pending"),row["audio"][0]["src"])
    # Recheck repository revisions after metadata/audio acquisition, no silent moving-main claim.
    for dataset,revision in [("PolyAI/minds14",minds_revision),("corypaik/musan",musan_revision)]:
        p=fetch.get("revision-check",f"https://huggingface.co/api/datasets/{dataset}","sources/final-"+dataset.replace("/","-")+".json")
        if json.loads(p.read_text(encoding="utf-8"))["sha"]!=revision:raise ValueError("Source revision changed during acquisition")
    manifest=dict(schema_version=1,dataset_id="voxgo-ru-continuous-20261027-v1",frozen_before_asr=True,
        development_policy="No strategy tuning this round. Unknown speakers form one conservative group.",
        holdout_status="0 validated locked items; 8 quarantine candidates only; speaker/session separation unresolved",
        expected_goals=dict(dev=16,locked_holdout=8,negative=12),actual_counts=dict(dev=16,locked_holdout=0,quarantine=8,negative=len(negatives)),
        download_bytes=fetch.data["bytes"],download_limit_bytes=fetch.data["limit"],
        history_registry_sha256=sha((root/"historical-registry.json").read_bytes()),
        limitations=["Speaker/session metadata unavailable: no validated locked holdout or independent-speaker count",
            "Banking narrowband public speech, not game or broad Russian conversational coverage",
            "All references and semantic labels pending current human verification; no accepted semantic accuracy"],records=rows)
    (root/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(counts=manifest["actual_counts"],download_bytes=fetch.data["bytes"],seconds_by_split={s:round(sum(r["seconds"] for r in rows if r["split"]==s),2) for s in ["dev","quarantine","negative"]}),ensure_ascii=False),flush=True)
    return manifest


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--download",action="store_true")
    args=parser.parse_args()
    build_corpus(args.output,download=args.download)
