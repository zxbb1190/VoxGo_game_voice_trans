"""Zero-request summary and A/B review forms; never invent human acceptance."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.ru_benchmark_metrics import percentile
from scripts.offline_russian_capture_ab import create_output,write,offline_guard


def script_cue(text,target):
    patterns={'en':r'[A-Za-z]','zh':r'[\u3400-\u9fff]','ja':r'[\u3040-\u30ff]','ko':r'[\uac00-\ud7af]','ru':r'[\u0400-\u04ff]'}
    found=bool(re.search(patterns[target],text or ''))
    if target=='ja' and not found and re.search(patterns['zh'],text or ''):
        return 'ambiguous_han_only_japanese'
    return 'expected_script_present_not_human_confirmation' if found else 'suspected_target_script_missing'


def request_metrics(rows,ledger):
    seen=[r['attempt_id'] for r in rows if r.get('attempt_id') is not None]
    if len(seen)!=len(set(seen)):raise ValueError('Duplicate attempt results; do not select a preferred result')
    attempts={r['attempt_id']:r for r in rows if r.get('attempt_id') is not None}
    ids=[r['id'] for r in ledger];completed=[attempts[id] for id in ids if id in attempts]
    timings=[r['elapsed_ms'] for r in completed if 'elapsed_ms' in r]
    waits=[r['queue_wait_ms'] for r in completed if r.get('queue_wait_ms') is not None]
    # This includes failures. It is queue-subtracted client time, not pure
    # server processing or independently measured network transit time.
    http_estimates=[max(0,r['elapsed_ms']-(r.get('queue_wait_ms') or 0)) for r in completed if 'elapsed_ms' in r]
    body_complete=sum(r.get('http_status')==200 and r.get('complete_json_response',False) for r in completed)
    return dict(attempted=len(ids),http_200_headers=sum(r.get('http_status')==200 for r in ledger),http_200_complete_json=body_complete,
        api_nonempty_success=sum(r.get('api_nonempty_success',False) for r in completed),
        timeouts=sum(r.get('failure_reason')=='timeout' or r.get('exception_type')=='TimeoutError' for r in completed),
        unfinished=sum(id not in attempts or attempts[id].get('state')=='unfinished_or_exception' for id in ids),
        truncated=sum(r.get('truncated',False) for r in completed),
        http_complete_success_rate=body_complete/len(ids) if ids else None,
        client_p50_ms=percentile(timings,.5),client_p95_ms=percentile(timings,.95),
        api_queue_p95_ms=percentile(waits,.95),queue_subtracted_http_estimate_p50_ms=percentile(http_estimates,.5),queue_subtracted_http_estimate_p95_ms=percentile(http_estimates,.95),
        target_script_suspicions=sum(script_cue(r.get('translated',''),r['target'])=='suspected_target_script_missing' for r in completed if r.get('api_nonempty_success')),
        human_correct_target_language_count=None,human_intelligibility_rate=None)


def summarize(plan,manifest,root):
    load=lambda p:json.loads(Path(p).read_text('utf-8'))
    ledger=load(root/'attempt-ledger.json')['attempts'];status=load(root/'status.json')
    if status['status']=='running':raise ValueError('Wait for final status; do not silently summarize an ongoing batch')
    text=load(root/'text-results.json') if (root/'text-results.json').exists() else []
    lookup={r['id']:r for r in manifest['records']};pairs=[];voice=[];all_api=list(text)
    for case in plan['audio_cases']:
        record=lookup[case['record_id']];path=root/(case['id']+'-online.json')
        raw=root/case['id']/'result.json'
        data=load(path) if path.exists() else None;r=load(raw) if raw.exists() else None
        api=data['api'] if data else [];all_api+=api
        subtitles=data['subtitles'] if data else []
        good={s['trace_id']:s for s in subtitles if s['copyable'] and s['translated'] and not s['translated'].startswith(('[翻译','[未翻译]'))}
        api_good={a['trace_id']:a for a in api if a.get('api_nonempty_success')}
        events=[json.loads(x) for x in (raw.parent/'events.jsonl').read_text('utf-8').splitlines()] if r else []
        trace_to_segment={e['event']['trace_id']:e['segment_id'] for e in events if e['kind']=='translation_boundary'}
        segment_rows=[]
        for s in (r['segments'] if r else []):
            ids=[t for t,id in trace_to_segment.items() if id==s['segment_id']]
            segment_rows.append(dict(segment_id=s['segment_id'],pcm_sha256=s['pcm_sha256'],spans=s['spans'],original_wav_intersections=s['sources'],
                submit_reason=s['reason'],status=s['status'],drop_reason=s.get('filter_reason') or s.get('language_gate_reason'),
                raw_asr=s.get('asr',{}).get('raw_text'),asr_language=s.get('asr',{}).get('language'),asr_language_probability=s.get('asr',{}).get('language_probability'),
                retained=s.get('retained_text',''),translation_input=s.get('translation_input',''),
                api=[a for a in api if a['trace_id'] in ids],subtitles=[x for x in subtitles if x['trace_id'] in ids]))
        reference=[a for a in text if a['phase']=='standard_reference' and a['case_id']==f"reference-{case['source']}-{case['target']}-{case['record_id']}"]
        pairs.append(dict(case=case,source_audio=record['audio'],source_license=record['license'],source_url=record['source_url'],reference=record['reference_text'],reference_status=record['reference_status'],
            standard_original_translation=reference,actual_segments=segment_rows,
            alignment_limit='A is whole-source reference, B is actual stream fragments. Context differs; no gold word/frame alignment. Do not attribute every A/B difference exclusively to Whisper.',
            human=dict(status='pending',reviewer=None,asr_key_meaning_retained=None,translation_understandable=None,critical_semantic_errors=None,voice_end_frame=None,severity=None)))
        segments=r['segments'] if r else []
        voice.append(dict(case_id=case['id'],source=case['source'],target=case['target'],record_id=case['record_id'],executed=bool(data),
            captured=sum(s['captured'] for s in segments),asr_completed=sum('asr' in s for s in segments),
            asr_normalized_nonempty=sum(bool(s.get('asr',{}).get('text')) for s in segments),
            retained=sum(bool(s.get('retained_text')) for s in segments),translation_boundaries=sum(bool(s.get('translation_input')) for s in segments),
            pre_asr_drops=sum(s['status']=='dropped' and 'asr' not in s for s in segments),post_asr_drops=sum(s['status']=='dropped' and 'asr' in s for s in segments),
            language_gate_drops=sum(s['status']=='language_gate_dropped' for s in segments),
            api_rows=api,subtitle_nonempty_count=len(good),complete_nonempty_subtitle_count=sum(id in api_good and not api_good[id].get('truncated') for id in good),
            native_platform=data.get('platform') if data else None,drain_complete=data.get('translation_drain_complete',False) if data else False,
            pcm_to_widget_ms=[s['last_pcm_frame_to_widget_ms'] for s in good.values() if s.get('last_pcm_frame_to_widget_ms') is not None],
            file_end_to_last_subtitle_ms=max((s['source_wav_end_to_widget_ms'] for s in good.values() if s.get('source_wav_end_to_widget_ms') is not None),default=None),
            human_voice_end_latency_ms=None,manual_intelligible_subtitles=None))
    matrix=[]
    for source,target in sorted({(c['source'],c['target']) for c in plan['audio_cases']}):
        rs=[v for v in voice if (v['source'],v['target'])==(source,target)]
        ls=[r for r in ledger if (r['source'],r['target'])==(source,target)]
        ars=[r for r in all_api if (r['source'],r['target'])==(source,target)]
        pcms=[v for r in rs for v in r['pcm_to_widget_ms']]
        matrix.append(dict(source=source,target=target,route='direct online; one request per admitted input; no client pivot',
            authored_text=request_metrics([r for r in ars if r['phase']=='authored_text'],[r for r in ls if r['phase']=='authored_text']),
            standard_reference=request_metrics([r for r in ars if r['phase']=='standard_reference'],[r for r in ls if r['phase']=='standard_reference']),
            streaming_api=request_metrics([r for r in ars if r['phase']=='streaming_asr'],[r for r in ls if r['phase']=='streaming_asr']),
            planned_voice_cases=len(rs),executed_voice_cases=sum(r['executed'] for r in rs),
            cases_with_translation_input=sum(r['translation_boundaries']>0 for r in rs),cases_with_nonempty_subtitle=sum(r['subtitle_nonempty_count']>0 for r in rs),
            nonempty_subtitle_segments=sum(r['subtitle_nonempty_count'] for r in rs),
            pcm_end_to_widget_p50_ms=percentile(pcms,.5),pcm_end_to_widget_p95_ms=percentile(pcms,.95),
            human_voice_end_to_subtitle_p50_ms=None,human_voice_end_to_subtitle_p95_ms=None,human_understandability=None,release_status='not_accepted'))
    pcms=[v for r in voice for v in r['pcm_to_widget_ms']]
    result=dict(status=status,api=request_metrics(all_api,ledger),matrix=matrix,voice_cases=voice,
        planned_voice_cases=len(voice),executed_voice_cases=sum(r['executed'] for r in voice),
        cases_with_translation_input=sum(r['translation_boundaries']>0 for r in voice),cases_with_nonempty_subtitle=sum(r['subtitle_nonempty_count']>0 for r in voice),
        nonempty_subtitle_segments=sum(r['subtitle_nonempty_count'] for r in voice),pcm_end_to_widget_p50_ms=percentile(pcms,.5),pcm_end_to_widget_p95_ms=percentile(pcms,.95),
        human_voice_end_to_subtitle_latency=None,human_intelligibility=None,real_game_fps=None,
        unique_voice_recordings=len({r['record_id'] for r in voice}),release_approved=False)
    return result,pairs


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['plan','manifest','results','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    with offline_guard():
        output=create_output(a.output)
        summary,pairs=summarize(json.loads(a.plan.read_text('utf-8')),json.loads(a.manifest.read_text('utf-8')),a.results)
        write(output/'summary.json',summary);write(output/'paired-human-review.json',pairs)
        print(json.dumps({k:v for k,v in summary.items() if k not in ['matrix','voice_cases']},ensure_ascii=False,indent=2))
