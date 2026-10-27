"""New five-language offline baseline using the existing observed runtime chain.

No providers, GUI, private settings, model download, retries or parameter search.
CJK has character/unit errors, not fabricated word-segmented WER.
"""
import argparse
import copy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.offline_russian_capture_ab import run_child,offline_guard,create_output,write,local_model,fingerprint
from scripts.run_ru_continuous_baseline import input_stream,require_frozen
from scripts.ru_benchmark_metrics import validate_manifest,percentile
from scripts.review_ru_continuous_baseline import reviewed_assessment
from scripts.run_asr_benchmark import _word_errors

LANGUAGES=('zh','en','ja','ko','ru')


def resolved_config(language,strategy,models):
    from voxgo.config.loader import default_app_config,migrate_runtime_defaults,sync_language_flow,apply_language_runtime_policy,sync_whisper_vad_limit
    from voxgo.asr.language_profiles import effective_speech_config
    if language not in LANGUAGES or strategy not in {'formal','legacy','language_aware'}:raise ValueError('Unknown source/strategy')
    if (language in {'en','zh'}) != (strategy=='formal'):raise ValueError('EN/ZH formal only; JA/KO/RU existing two strategies only')
    c=copy.deepcopy(default_app_config());c.translation.source_lang=language;c.translation.target_lang='en' if language=='zh' else 'zh'
    if strategy!='formal':c.whisper.multilingual_asr_strategy=strategy
    migrate_runtime_defaults(c);sync_language_flow(c);apply_language_runtime_policy(c);sync_whisper_vad_limit(c)
    c=copy.deepcopy(effective_speech_config(c));c.whisper.model_dir=str(models.resolve());c.whisper.local_files_only=True
    local_model(models,c.whisper.active_model_size)
    return c


def make_schedule(records):
    specs=[];negative_index=0
    for index,r in enumerate(records):
        language=r['language']
        if r['split']=='negative':
            language=LANGUAGES[negative_index%len(LANGUAGES)];negative_index+=1
        if r['split'] not in {'dev','negative'}:continue
        strategies=['formal'] if language in {'zh','en'} else ['legacy','language_aware']
        if index%2:strategies=list(reversed(strategies))
        specs += [dict(id=r['id']+'--'+language+'--'+s,record_id=r['id'],source_language=language,strategy=s,cadence_ms=100) for s in strategies]
    return specs


def cjk_units(text):
    import unicodedata
    text=unicodedata.normalize('NFKC',text).casefold()
    return re.findall(r'[\u3400-\u9fff\u3040-\u30ff]|[^\W_\u3400-\u9fff\u3040-\u30ff]+',text,re.UNICODE)


def language_assessment(result,record,events,spec):
    a=reviewed_assessment(result,record,events)
    a['source_language']=spec['source_language']
    for stage,hyp in [('raw_metrics',a['raw']),('retained_metrics',a['retained']),('translated_metrics',a['translation_input'])]:
        m=a[stage]
        if spec['source_language'] in {'zh','ja'}:
            # No installed word segmenter and no manually word-segmented gold.
            m['proxy_wer']=None;m['accepted_wer']=None;m['word_counts']=None
            m['tokenization']='Han/kana character units plus other Unicode runs; UER, not word WER'
            counts=_word_errors(record['reference_text'],hyp,cjk_units) if record['reference_text'] and a['alignment']['valid'] else None
            m['unit_counts']=counts;m['proxy_unit_error_rate']=counts['errors']/max(1,counts['reference_words']) if counts else None
        else:m['tokenization']='Unicode lexical tokens (Korean eojeol, not morphemes)'
    # RU lexical cues are only valid in RU; no false multilingual semantic gold.
    if spec['source_language']!='ru':a['lexical_suspicions']=None
    a['manual_semantic_accuracy']=None
    a['detected_mismatch_segments']=[x for x in a['languages'] if x['language']!=spec['source_language']]
    puts={e['item_id']:e['elapsed_ms'] for e in events if e['kind']=='queue_put'}
    a['performance']['queue_event_wait_all_ms']=[max(0,e['elapsed_ms']-puts[e['item_id']]) for e in events if e['kind']=='queue_get' and e.get('item_id') in puts]
    return a


def summarize(output,plan):
    rows=[json.loads((output/s['id']/'assessment.json').read_text('utf-8')) for s in plan]
    groups=[]
    for language in LANGUAGES:
        for strategy in ['formal','legacy','language_aware']:
            for split in ['dev','negative']:
                rs=[r for r in rows if r['source_language']==language and r['strategy']==strategy and r['split']==split]
                if not rs:continue
                metrics={}
                for stage in ['raw_metrics','retained_metrics','translated_metrics']:
                    ms=[r[stage] for r in rs if r[stage]['proxy_cer'] is not None]
                    chars=sum(m['character_counts']['reference_characters'] for m in ms)
                    errors=sum(m['character_counts']['errors'] for m in ms)
                    words=sum((m.get('word_counts') or {}).get('reference_words',0) for m in ms)
                    werrors=sum((m.get('word_counts') or {}).get('errors',0) for m in ms)
                    metrics[stage]=dict(proxy_cer=errors/chars if chars else None,proxy_wer=werrors/words if words else None,reference_characters=chars,reference_words=words,accepted_cer=None,accepted_wer=None)
                times=[v for r in rs for v in r['performance']['asr_all_completed_ms']];waits=[v for r in rs for v in r['performance']['queue_event_wait_all_ms']]
                seconds=sum(r['seconds'] for r in rs);cpu=sum(r['performance']['replay_cpu_seconds'] for r in rs)
                groups.append(dict(language=language,strategy=strategy,split=split,recordings=len(rs),audio_seconds=seconds,metrics=metrics,
                    counts={k:sum(r['counts'][k] for r in rs) for k in rs[0]['counts']},asr_p50_ms=percentile(times,.5),asr_p95_ms=percentile(times,.95),
                    cpu_seconds_per_audio_minute=cpu/(seconds/60),peak_sampled_rss_mib=max(r['performance']['peak_sampled_rss_bytes'] for r in rs)/2**20,
                    queue_wait_p95_ms=percentile(waits,.95),detected_mismatch_segments=sum(len(r['detected_mismatch_segments']) for r in rs),
                    negative_raw_nonempty_recordings=sum(r['negative_raw_nonempty'] for r in rs),negative_translation_nonempty_recordings=sum(r['negative_translation_nonempty'] for r in rs)))
    write(output/'summary.json',dict(groups=groups,recordings=rows,api_requests=0,human_quality='pending',release_approved=False,
        scope='offline paced-file simulation, no native GUI/game/online evidence; pending source references'))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--models-directory',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--child',type=Path)
    args=p.parse_args()
    with offline_guard() as safety:
        manifest=json.loads(args.manifest.read_text('utf-8'));require_frozen(manifest)
        registry_path=args.manifest.parent/'historical-registry.json';history=json.loads(registry_path.read_text('utf-8'))
        if hashlib.sha256(registry_path.read_bytes()).hexdigest()!=manifest['history_registry_sha256']:raise ValueError('History registry changed')
        validate_manifest(manifest,historical_hashes=history['hashes'])
        if args.child:
            spec=json.loads(args.child.read_text('utf-8'));record=next(r for r in manifest['records'] if r['id']==spec['record_id'])
            c=resolved_config(spec['source_language'],spec['strategy'],args.models_directory)
            run_child(SimpleNamespace(child=args.child,manifest=args.manifest,models_directory=args.models_directory,output=args.output,drain_seconds=30),
                replay_input=input_stream(record),app_config=c,whole_clip_warmup=False,summarize_recordings=lambda r:[],measurement_scope='new five-language offline full-source baseline; no GUI/game/translation')
            result=json.loads((args.output/'result.json').read_text('utf-8'));events=[json.loads(x) for x in (args.output/'events.jsonl').read_text('utf-8').splitlines()]
            write(args.output/'assessment.json',language_assessment(result,record,events,spec))
            write(args.output/'offline-safety.json',{k:v for k,v in safety.items() if k!='active'});return
        if any(args.output.resolve().is_relative_to(x.resolve()) for x in [args.manifest.parent,ROOT/'voxgo',args.models_directory]):raise ValueError('Protect corpus/runtime/models')
        output=create_output(args.output);plan=make_schedule(manifest['records'])
        initial=fingerprint();mh=hashlib.sha256(args.manifest.read_bytes()).hexdigest()
        models={}
        for source in LANGUAGES:
            for strategy in (['formal'] if source in {'en','zh'} else ['legacy','language_aware']):
                c=resolved_config(source,strategy,args.models_directory);name=c.whisper.active_model_size
                if name not in models:models[name]=local_model(args.models_directory,name)[1]
        write(output/'plan.json',dict(schedule=plan,manifest_sha256=mh,models=models,fingerprint=initial,entrypoint_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            config_snapshots={l+':'+s:dict(audio=asdict(resolved_config(l,s,args.models_directory).audio),whisper=asdict(resolved_config(l,s,args.models_directory).whisper)) for l in LANGUAGES for s in (['formal'] if l in {'en','zh'} else ['legacy','language_aware'])}))
        status=dict(status='running',completed=[],api_requests=0)
        try:
            for index,spec in enumerate(plan):
                spec_path=output/(spec['id']+'.json');write(spec_path,spec)
                print(f"{index+1}/{len(plan)} {spec['id']}",flush=True)
                with (output/(spec['id']+'.log')).open('x',encoding='utf-8') as log:
                    run=subprocess.run([sys.executable,'-B','-X','utf8',str(Path(__file__).resolve()),'--manifest',str(args.manifest.resolve()),'--models-directory',str(args.models_directory.resolve()),'--output',str((output/spec['id']).resolve()),'--child',str(spec_path.resolve())],stdout=log,stderr=log,cwd=ROOT,timeout=300)
                if run.returncode:raise RuntimeError('Child failed; no selective retry: '+spec['id'])
                status['completed'].append(spec['id']);write(output/'status.json',status)
            summarize(output,plan);status['status']='complete'
        finally:
            status.update(manifest_unchanged=hashlib.sha256(args.manifest.read_bytes()).hexdigest()==mh,runtime_and_observer_unchanged=initial['files']==fingerprint()['files'],
                models_unchanged=all(local_model(args.models_directory,n)[1]==f for n,f in models.items()),safety={k:v for k,v in safety.items() if k!='active'})
            if status['status']=='running':status['status']='incomplete'
            write(output/'status.json',status)


if __name__=='__main__':main()
