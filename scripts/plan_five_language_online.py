"""Prepare an explicit online plan, never load credentials or send requests."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from voxgo.languages import ONLINE_DIRECTIONS

TEXTS={
 'zh':[
  '左边两个人，别开枪。',
  '先守住北门，等我数到三再一起撤退。如果队长还没回来，就不要启动电梯。',
  '治疗师不在二楼，他在地下一层。我们还有十五秒，不是五十秒。'],
 'en':[
  'Two on the left. Do not shoot.',
  'Hold the north gate. When I count to three, fall back together. If the captain has not returned, do not start the lift.',
  'The healer is not on the second floor; he is on basement level one. We have fifteen seconds, not fifty.'],
 'ja':[
  '左に二人。まだ撃たないで。',
  '北門を守って。三つ数えたら一緒に撤退しよう。隊長が戻っていなければ、エレベーターを動かさないで。',
  '回復役は二階ではなく、地下一階にいる。残りは五十秒ではなく十五秒だ。'],
 'ko':[
  '왼쪽에 두 명이야. 아직 쏘지 마.',
  '북문을 지켜. 내가 셋을 세면 같이 후퇴하자. 대장이 아직 돌아오지 않았으면 엘리베이터를 작동시키지 마.',
  '힐러는 2층이 아니라 지하 1층에 있어. 남은 시간은 50초가 아니라 15초야.'],
 'ru':[
  'Слева двое. Пока не стреляй.',
  'Держите северные ворота. Когда я досчитаю до трёх, отступаем вместе. Если командир ещё не вернулся, не включайте лифт.',
  'Целитель не на втором этаже, а на первом подземном. Осталось пятнадцать секунд, а не пятьдесят.'],
}


def build_plan(manifest,summary,selections,provider_metadata):
    if provider_metadata.get('provider')!='openai_compatible' or provider_metadata.get('model')!='tencent/Hunyuan-MT-7B' or provider_metadata.get('endpoint_host')!='api.siliconflow.cn':raise ValueError('Fixed authorized provider configuration missing')
    if len(ONLINE_DIRECTIONS)!=20:raise ValueError('All twenty code routes required before live tests')
    lookup={r['id']:r for r in manifest['records']};by_result={(r['id'],r['strategy']):r for r in summary['recordings']}
    text=[];audio=[];standard=[];boundaries=0
    for source,target in sorted(ONLINE_DIRECTIONS):
        for i,value in enumerate(TEXTS[source]):
            text.append(dict(id=f'text-{source}-{target}-{i+1}',source=source,target=target,text=value,
                category=['short_callout','continuous_conditional','critical_numbers_negation'][i],human_review='pending',origin='new AI-assisted authored material; not human gold'))
        ids=selections['records'][source]
        if len(ids)!=3 or len(set(ids))!=3:raise ValueError('Three distinct frozen recordings per direction required')
        for id in ids:
            record=lookup[id]
            if record['split']!='dev' or record['language']!=source:raise ValueError('Source/selection mismatch')
            strategy='formal' if source in {'en','zh'} else 'language_aware'
            count=by_result[id,strategy]['counts']['translation_ready'];boundaries+=count
            audio.append(dict(id=f'audio-{source}-{target}-{id}',source=source,target=target,record_id=id,strategy=strategy,offline_translation_boundaries=count,
                wav_sha256=record.get('wav_sha256'),pcm_sha256=record.get('pcm_sha256'),
                note='Current candidate configuration for testing, not a chosen release winner; zero boundaries is a planned failed subtitle case'))
            standard.append(dict(id=f'reference-{source}-{target}-{id}',source=source,target=target,record_id=id,text=record['reference_text'],reference_status=record['reference_status']))
    expected=len(text)+len(standard)+boundaries
    return dict(schema_version=1,authorized=False,real_api_requests_so_far=0,
        provider=dict(name='SiliconFlow',model='tencent/Hunyuan-MT-7B',endpoint_host='api.siliconflow.cn',timeout_seconds=provider_metadata.get('timeout_seconds'),
            max_tokens=provider_metadata.get('max_tokens'),temperature=provider_metadata.get('temperature'),context_messages=0,max_concurrent_requests=1),
        text_cases=text,standard_reference_calls=standard,audio_cases=audio,
        expected_calls=dict(authored_text=len(text),standard_reference=len(standard),streaming_asr=boundaries,total=expected),
        proposed_hard_call_limit=int(math.ceil(expected*1.15/10)*10),
        planned_voice_direction_attempts=len(audio),unique_voice_recordings=len({r['record_id'] for r in audio}),
        cost=dict(estimated_cny=0,input_cny_per_million=0,output_cny_per_million=0,source='https://siliconflow.cn/pricing',
            basis='Official current price lists input/output free; recheck before execution, not a billing invoice'),
        execution_rules=['Explicit user authorization required; this file is not authorization',
            'No retry or selective rerun; reserve and persist each HTTP attempt before sending',
            'Only existing key in memory; never copy settings/key into artifacts or change user provider',
            'Stop at authorized cap; mark uncompleted cases, do not merge segments to fit budget',
            'Stop whole batch on pricing change, authentication/payment error or rate limit; no provider fallback',
            'Per-request timeout uses existing config; per-record drain at most 60s then cancel and report unfinished',
            'Source reference and semantic checks remain pending human review; automatic script cues are not human target-language accuracy',
            'Native Qt paint/widget clocks are distinct from physical display and manually labelled voice-end latency'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['manifest','summary','selections','provider-metadata','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();load=lambda p:json.loads(p.read_text('utf-8'))
    plan=build_plan(load(a.manifest),load(a.summary),load(a.selections),load(a.provider_metadata))
    plan['input_sha256']={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in [('manifest',a.manifest),('asr_summary',a.summary),('selections',a.selections),('provider_metadata',a.provider_metadata)]}
    if a.output.exists():raise FileExistsError('Fresh online plan required')
    a.output.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(expected=plan['expected_calls'],proposed_cap=plan['proposed_hard_call_limit'],authorized=False,plan_sha256=hashlib.sha256(a.output.read_bytes()).hexdigest())))
