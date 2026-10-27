"""Summarize public paired replay evidence, without quality approval or API I/O."""
import argparse
import csv
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
from scripts.benchmark_multilingual_asr_profiles import errors


def quantiles(values):
    values=[v for v in values if v is not None]
    return {'n':len(values),**{f'p{p}':round(float(np.percentile(values,p)),2) for p in (50,95)}} if values else {'n':0,'p50':None,'p95':None}


def summarize(root):
    plan=json.loads((root/'plan.json').read_text(encoding='utf8'))
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf8'))
    references=json.loads((root/'reference/results.json').read_text(encoding='utf8'))
    golden={r['case_id']:r['display_translation'] for r in references['records']}
    groups={};review=[];runs=[]
    for scheduled in plan['schedule']:
        directory=root/scheduled['id']
        result=json.loads((directory/'audio.json').read_text(encoding='utf8'))[0]
        integrity=json.loads((directory/'integrity.json').read_text(encoding='utf8'))
        if not integrity['protected_files_unchanged']:raise ValueError('Protected settings changed')
        reference=' '.join(r['reference'] for r in result['whole_clip_asr'])
        raw=errors(reference,' '.join(r['text'] for r in result['stream_asr']))
        delivered=errors(reference,' '.join(r['text'] for r in result['api']))
        key=(scheduled['language'],scheduled['strategy'])
        groups.setdefault(key,[]).append((result,raw,delivered,integrity))
        runs.append({**scheduled,'drain_complete':result['drain_complete'],'http_attempts':integrity['http_attempts'],
            'http_statuses':integrity['statuses'],'raw_asr':raw,'delivered_asr':delivered})
        cursor=48000
        for baseline in result['whole_clip_asr']:
            sample=next(r for r in manifest if r['id']==baseline['id'])
            end=cursor+round(sample['seconds']*16000)
            def overlaps(row):
                return row.get('source_start_frame') is not None and row.get('source_end_frame') is not None and row['source_end_frame']>cursor and row['source_start_frame']<end
            asr=[r for r in result['stream_asr'] if overlaps(r)]
            outputs=[r for r in result['subtitles'] if overlaps(r)]
            texts={r['text'] for r in asr}
            api=[r for r in result['api'] if r['text'] in texts]
            review.append({'round':scheduled['repeat'],'language':scheduled['language'],'strategy':scheduled['strategy'],
                'audio_id':sample['id'],'audio':sample['audio'],'standard_transcript':sample['reference_text'],
                'standard_full_translation':golden.get(sample['id'],''),'whole_asr':baseline['asr']['text'],
                'stream_asr':' / '.join(r['text'] for r in asr),
                'sent_to_translation':' / '.join(r['text'] for r in api),
                'raw_translation':' / '.join(r['translated'] for r in api),
                'display_translation':' / '.join(r['translated'] for r in outputs),
                'last_frame_to_widget_ms':' / '.join(str(round(r['last_segment_pcm_frame_to_widget_ms'],2)) for r in outputs),
                'model_finish_reasons':' / '.join(str(r.get('finish_reason')) for r in api),
                'unmapped_asr_in_run':sum(r.get('source_start_frame') is None for r in result['stream_asr']),
                'scope':'public read speech; clip mapping by frame overlap, full transcript without word alignment',
                'human_verdict':'pending','human_severity':'pending'})
            cursor=end+32000
    summaries=[]
    for (language,strategy),rows in sorted(groups.items()):
        audio=[r[0] for r in rows];apis=[a for r in audio for a in r['api']];subtitles=[s for r in audio for s in r['subtitles']]
        def cer(index):return round(sum(r[index]['errors'] for r in rows)/sum(r[index]['reference_characters'] for r in rows),6)
        wall=sum(r['wall_seconds'] for r in audio)
        cpu=sum(r['cpu_one_core_percent']*r['wall_seconds']/100 for r in audio)
        summaries.append({'language':language,'strategy':strategy,'unique_clips':2,'clip_replays':4,
            'raw_asr_cer':cer(1),'delivered_asr_cer':cer(2),
            'asr_ms':quantiles([r['asr_ms'] for a in audio for r in a['stream_asr']]),
            'provider_http_ms':quantiles([r.get('provider_elapsed_ms') for r in apis]),
            'translation_invocation_ms':quantiles([r['elapsed_ms'] for r in apis]),
            'approx_client_queue_ms':quantiles([max(0,r['elapsed_ms']-r['provider_elapsed_ms']) for r in apis if r.get('provider_elapsed_ms') is not None]),
            'last_frame_to_widget_ms':quantiles([r.get('last_segment_pcm_frame_to_widget_ms') for r in subtitles]),
            'first_frame_to_widget_ms':quantiles([r.get('first_segment_pcm_frame_to_widget_ms') for r in subtitles]),
            'cpu_one_core_mean_percent':round(100*cpu/wall,2),'cpu_seconds':round(cpu,2),
            'peak_rss_mib':round(max(r['peak_rss_bytes'] for r in audio)/2**20,2),
            'asr_text_identical_between_repeats':[[a['text'] for a in r['stream_asr']] for r in audio][0]==[[a['text'] for a in r['stream_asr']] for r in audio][1],
            'http_attempts':sum(r[3]['http_attempts'] for r in rows),'api_failures':sum(bool(r['failure_reason']) for r in apis),
            'confirmed_http_200':sum(s==200 for r in rows for s in r[3]['statuses']),
            'unfinished_translation_invocations':sum(r[3]['http_attempts'] for r in rows)-len(apis),
            'truncated_api_outputs':sum(r.get('finish_reason')=='length' for r in apis),
            'stats':{k:sum(r['stats'].get(k,0) for r in audio) for k in {k for r in audio for k in r['stats']}},
            'effective_whisper':audio[0]['whisper'],'effective_audio':audio[0]['effective_audio']})
    result={'unique_clips':6,'clip_replays':24,'runs':runs,'groups':summaries,
        'all_drained':all(r['drain_complete'] for r in runs),'reference_http_attempts':references['http_attempts'],
        'confirmed_http_200':sum(r['http_status']==200 for r in references['records'])+sum(s==200 for r in runs for s in r['http_statuses']),
        'completed_api_failures':sum(r['api_failures'] for r in summaries),
        'unfinished_translation_invocations':sum(r['unfinished_translation_invocations'] for r in summaries),
        'audio_http_attempts':sum(r['http_attempts'] for r in runs),'human_review':'pending','key_meaning_accuracy':None,
        'real_game_acceptance':'incomplete','release_approved':False}
    (root/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    with (root/'human-review.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(review[0]));writer.writeheader();writer.writerows(review)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);args=parser.parse_args()
    result=summarize(args.root)
    print(json.dumps({'http_attempts':result['reference_http_attempts']+result['audio_http_attempts'],'all_drained':result['all_drained']}))
