"""Compare EN/ZH runtime settings against actual Git baseline, without I/O APIs."""
import argparse
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def snapshot(root):
    sys.path.insert(0,str(root))
    from dataclasses import asdict
    from loguru import logger
    logger.remove()
    from voxgo.config.loader import default_app_config,migrate_runtime_defaults,sync_language_flow,apply_language_runtime_policy,sync_whisper_vad_limit
    from voxgo.asr.pipeline import SpeechPipeline
    from voxgo.runtime.events import EventBus
    rows=[]
    for source,target in [('en','zh'),('zh','en')]:
        for mode in ('fast','balanced','accurate','custom'):
            for impact in ('low','ultra_low','normal'):
                for pure in (False,True):
                    config=default_app_config()
                    config.translation.source_lang=source;config.translation.target_lang=target
                    config.audio.latency_mode=mode;config.whisper.asr_impact_mode=impact
                    config.whisper.pure_english_environment=pure
                    migrate_runtime_defaults(config,preserve_existing_audio_tuning=False)
                    sync_language_flow(config);apply_language_runtime_policy(config);sync_whisper_vad_limit(config)
                    pipeline=SpeechPipeline(lambda:config,lambda:None,EventBus(),{},lambda:True,lambda:False,lambda:'fixture',{},lambda *a:None)
                    whisper=asdict(config.whisper)
                    # These fields are routing/preferences, not legacy decoding settings.
                    whisper.pop('source_language',None);whisper.pop('multilingual_asr_strategy',None)
                    rows.append(dict(pair=[source,target],mode=mode,impact=impact,pure=pure,
                        audio=asdict(config.audio),whisper=whisper,policy=asdict(pipeline._mode_policy(config))))
    print(json.dumps(rows,sort_keys=True,ensure_ascii=False))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot-root',type=Path)
    parser.add_argument('--base-ref',default='afc33a67')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.snapshot_root: snapshot(args.snapshot_root);return
    archive=subprocess.check_output(['git','archive','--format=tar',args.base_ref,'voxgo'],cwd=ROOT)
    with tempfile.TemporaryDirectory() as directory:
        baseline=Path(directory)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            for member in tar:
                target=(baseline/member.name).resolve()
                if not target.is_relative_to(baseline.resolve()) or member.issym() or member.islnk():
                    raise ValueError('Unsafe archive member')
                tar.extract(member,baseline)
        def run(path):
            return json.loads(subprocess.check_output([sys.executable,'-X','utf8',str(Path(__file__).resolve()),'--snapshot-root',str(path)],cwd=ROOT))
        old,current=run(baseline),run(ROOT)
    failures=[r['pair']+[r['mode'],r['impact'],r['pure']] for r,s in zip(old,current) if r!=s]
    result={'baseline':args.base_ref,'cases':len(current),'equal':len(old)==len(current) and not failures,'differences':failures,
            'source':'actual baseline/current config loader and SpeechPipeline; no network, telemetry or user settings',
            'compared':['audio settings','decoding settings','model selection','pipeline scheduling policy']}
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False))
    if not result['equal']:raise SystemExit(1)


if __name__=='__main__':main()
