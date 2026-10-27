"""Paired legacy/new speech-strategy replay; public audio, fixed Hunyuan only.

No capture device, settings writes, production telemetry or runtime changes.
Default prepares an offline plan; --run-live explicitly enables real requests.
"""
import argparse
import asyncio
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.compare_public_asr_translation import (
    DEFAULT_PROFILE,DEFAULT_CREDENTIALS,ENDPOINT,MODEL,load_config,write_json,digest,utc_now,execute,
)
from scripts.validate_multilingual_live import BudgetClient,audio_run,pcm

SELECTED=(
 'fleurs-ja-test-2003-10281646305484957883',
 'fleurs-ja-holdout-1827-10746508960655553792',
 'fleurs-ko-test-1662-10115200572671025618',
 'fleurs-ko-holdout-1907-10231261934313595333',
 'fleurs-ru-test-1692-10024935581249406669',
 'fleurs-ru-holdout-1762-10098401296465388159',
)


def build_schedule():
    rows=[]
    for repeat in (1,2):
        languages=('ja','ko','ru') if repeat==1 else ('ru','ko','ja')
        strategies=('legacy','language_aware') if repeat==1 else ('language_aware','legacy')
        for language in languages:
            for strategy in strategies:
                rows.append(dict(id=f'r{repeat}-{language}-{strategy}',repeat=repeat,language=language,strategy=strategy))
    return rows


def build_manifest():
    original=Path('E:/my/my/VoxGo-0.5.3-Online-Acceptance-caed9130/materials/manifest.json')
    rows=json.loads(original.read_text(encoding='utf-8-sig'))
    for row in rows:row['audio']=str(original.parent.parent/row['audio'])
    rows+=json.loads((ROOT/'docs/testing/evidence/v0.5.3-speech-repair/holdout-provenance.json').read_text(encoding='utf8'))
    lookup={r['id']:r for r in rows}
    selected=[lookup[key] for key in SELECTED]
    for row in selected:
        if row['license']!='CC-BY-4.0' or row.get('real_game_audio') is not False:
            raise ValueError('Only the selected licensed public read speech is accepted')
        pcm(row)  # Verify exact SHA256, mono PCM16/16kHz before any API call.
    return selected


class Journal:
    def __init__(self,path):
        if path.exists():raise ValueError('Do not overwrite an experiment journal')
        self.path=path;self.count=0;self.blocked=False;self.statuses=[];self.lock=threading.Lock()
    def reserve(self,label):
        with self.lock:
            if self.blocked:raise RuntimeError('Provider/origin error; further HTTP blocked')
            if self.count>=40:raise RuntimeError('Unexpected per-replay request volume')
            self.count+=1
            self.append({'kind':'reserved_before_http','attempt':self.count,'stage':label,'utc':utc_now(),'model':MODEL})
    def append(self,row):
        with self.path.open('a',encoding='utf8') as stream:
            stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush();os.fsync(stream.fileno())


class ObservedClient(BudgetClient):
    async def _get_session(self):
        session=await super()._get_session()
        if not getattr(session,'_ab_checked',False):
            post=session.post;owner=self
            class ObservedRequest:
                def __init__(self,request):self.request=request
                async def __aenter__(self):
                    response=await self.request.__aenter__()
                    owner.budget.statuses.append(response.status)
                    if response.status in {301,302,303,307,308,401,403,404,429}:owner.budget.blocked=True
                    owner.budget.append({'kind':'http_response','status':response.status,'utc':utc_now()})
                    return response
                async def __aexit__(self,*args):return await self.request.__aexit__(*args)
            def guarded(url,*args,**kwargs):
                if url!=ENDPOINT or kwargs.get('json',{}).get('model')!=MODEL:
                    raise ValueError('Unexpected origin/model blocked')
                kwargs['allow_redirects']=False
                return ObservedRequest(post(url,*args,**kwargs))
            session.post=guarded;session._ab_checked=True
        return session


def protected_paths():
    return [DEFAULT_CREDENTIALS,DEFAULT_PROFILE/'user_settings.json',DEFAULT_PROFILE/'acceptance.config.json',DEFAULT_PROFILE/'telemetry_consent.json']


def child(args):
    directory=args.output/args.child
    directory.mkdir(exist_ok=False)
    selected=next(r for r in build_schedule() if r['id']==args.child)
    config=load_config(DEFAULT_PROFILE,DEFAULT_CREDENTIALS)
    config.enable_local_phrase_cache=False
    journal=Journal(directory/'attempts.jsonl')
    before={str(p):digest(p.read_bytes()) for p in protected_paths()}
    try:
        audio_run(config,journal,args.output/'manifest.json',directory/'audio.json',
            sources=(selected['language'],),speech_strategy=selected['strategy'],client_factory=ObservedClient)
    finally:
        # Defensive redaction of the tool output; credentials never belong in an artifact.
        path=directory/'audio.json'
        if path.exists():
            path.write_text(path.read_text(encoding='utf8').replace(config.api_key,'[REDACTED]'),encoding='utf8')
        write_json(directory/'integrity.json',{'http_attempts':journal.count,'statuses':journal.statuses,
            'service_blocked':journal.blocked,'protected_files_unchanged':all(digest(Path(p).read_bytes())==v for p,v in before.items())})
    if journal.blocked:raise SystemExit(3)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-live',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--child',choices=[r['id'] for r in build_schedule()])
    args=parser.parse_args()
    if args.child:
        if not args.run_live:raise ValueError('Live child requires explicit run flag')
        child(args);return
    args.output.mkdir(parents=True,exist_ok=False)
    manifest=build_manifest();schedule=build_schedule()
    write_json(args.output/'manifest.json',manifest)
    write_json(args.output/'plan.json',{'schedule':schedule,'baseline':'current code compatibility strategy, not a 0.5.2 binary',
        'unique_clips':6,'clip_replays':24,'order':'AB then BA, fresh subprocess per language/strategy',
        'domain':'public human read speech; known regression samples, not new holdout or game speech',
        'model':MODEL,'human_review':'pending','release_approved':False})
    if not args.run_live:print('Offline plan ready; no API requests');return
    before={str(p):digest(p.read_bytes()) for p in protected_paths()}
    config=load_config(DEFAULT_PROFILE,DEFAULT_CREDENTIALS);config.enable_local_phrase_cache=False
    status={'status':'running','completed':[],'http_attempts':0,'started_utc':utc_now()}
    write_json(args.output/'status.json',status)
    try:
        references={'inputs':[dict(id=r['id'],arm='reference_full',source_lang=r['language'],target_lang='zh',text=r['reference_text']) for r in manifest],
                    'schedule':[dict(case_id=r['id'],repeat=1) for r in manifest]}
        ref_dir=args.output/'reference';ref_dir.mkdir()
        ref=asyncio.run(execute(references,config,ref_dir,{}))
        if ref['status']!='complete' or not any(r['http_status']==200 for r in ref['records']):
            raise RuntimeError('Reference provider unavailable; no substitution')
        for row in schedule:
            print('Starting '+row['id'],flush=True)
            result=subprocess.run([sys.executable,'-X','utf8',str(Path(__file__).resolve()),'--run-live','--output',str(args.output.resolve()),'--child',row['id']],cwd=ROOT,capture_output=True,timeout=160)
            if result.returncode:
                raise RuntimeError('Replay stopped; sanitized child records retained')
            replay=json.loads((args.output/row['id']/'audio.json').read_text(encoding='utf8'))[0]
            if not replay['drain_complete']:status.setdefault('incomplete_drains',[]).append(row['id'])
            status['completed'].append(row['id'])
            status['http_attempts']=sum(1 for p in args.output.rglob('attempts.jsonl') for line in p.read_text(encoding='utf8').splitlines() if json.loads(line).get('kind')=='reserved_before_http')
            write_json(args.output/'status.json',status)
            print(f"Completed {len(status['completed'])}/12; HTTP attempts so far {status['http_attempts']}",flush=True)
        status['status']='complete_with_incomplete_drains' if status.get('incomplete_drains') else 'complete'
    finally:
        status['http_attempts']=sum(1 for p in args.output.rglob('attempts.jsonl') for line in p.read_text(encoding='utf8').splitlines() if json.loads(line).get('kind')=='reserved_before_http')
        status['protected_files_unchanged']=all(digest(Path(p).read_bytes())==v for p,v in before.items())
        status['ended_utc']=utc_now()
        if status['status']=='running':status['status']='stopped_incomplete'
        write_json(args.output/'status.json',status)


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(f'Comparison stopped ({type(error).__name__}); inspect sanitized records.',file=sys.stderr)
        sys.exit(1)
