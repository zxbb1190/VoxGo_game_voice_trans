"""Bounded new public human speech, never inference or private recordings."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import ssl
import tarfile
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.prepare_ru_continuous_corpus import BudgetedFetch,cached,historical_registry,convert_audio

REVISION='70bb2e84b976b7e960aa89f1c648e09c59f894dd'
BASE=f'https://huggingface.co/datasets/google/fleurs/resolve/{REVISION}'
LOCALES={'zh':'cmn_hans_cn','en':'en_us','ja':'ja_jp','ko':'ko_kr','ru':'ru_ru'}


def sha(data):return hashlib.sha256(data).hexdigest()


class BoundedArchiveReader:
    """Count received compressed bytes, including unselected archive members."""
    def __init__(self,response,fetch,row):self.response,self.fetch,self.row=response,fetch,row
    def read(self,size=-1):
        remaining=self.fetch.data['limit']-self.fetch.data['bytes']
        if remaining<=0:raise ValueError('Global public download limit reached')
        data=self.response.read(min(65536 if size<0 else size,remaining))
        self.row['bytes']+=len(data);self.fetch.data['bytes']+=len(data);self.fetch.save()
        return data


class CorpusFetch(BudgetedFetch):
    def save(self):
        # Antivirus can briefly hold an atomically replaced ledger on Windows.
        for attempt in range(6):
            try:return super().save()
            except PermissionError:
                if attempt==5:raise
                time.sleep(.02*(attempt+1))


def exclusion_names(registry):
    # Prior actual manifests/results, not the complete unused metadata tables.
    return {Path(value).name for value in registry['ids'] if value.lower().endswith('.wav')}


def prepare(output):
    output=Path(output).resolve()
    if (output/'manifest.json').exists():raise FileExistsError('Frozen dataset already exists')
    import certifi
    urllib.request.install_opener(urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where()))))
    # Recover a fully written, more recent ledger after an interrupted rename.
    ledger,temporary=output/'download-ledger.json',output/'download-ledger.tmp'
    if ledger.exists() and temporary.exists():
        old,new=json.loads(ledger.read_text('utf-8')),json.loads(temporary.read_text('utf-8'))
        if new['limit']!=old['limit'] or new['bytes']<old['bytes']:raise ValueError('Ambiguous ledger recovery')
        ledger.write_bytes(temporary.read_bytes())
    fetch=CorpusFetch(output);history=historical_registry(output)
    (output/'historical-registry.json').write_text(json.dumps(history,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    progress=output/'acquisition-progress.json'
    records=json.loads(progress.read_text('utf-8')) if progress.exists() else []
    excluded=exclusion_names(history);used=set(history['hashes'])
    for r in records:
        if sha(Path(r['original_file']).read_bytes())!=r['original_sha256'] or sha(Path(r['audio']).read_bytes())!=r['wav_sha256']:raise ValueError('Unfrozen acquisition file changed')
        used.update((r['original_sha256'],r['pcm_sha256'],r['wav_sha256']))
    card=cached(fetch,'fleurs-license',BASE+'/README.md','sources/fleurs-card.md')
    if 'cc-by-4.0' not in card.read_text('utf-8').lower():raise ValueError('FLEURS license not confirmed')
    def persist():
        (output/'acquisition-progress.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for language,locale in LOCALES.items():
        count=sum(r['language']==language for r in records)
        if count==12:continue
        metadata=cached(fetch,'fleurs-'+locale,BASE+f'/data/{locale}/test.tsv',f'sources/{locale}-test.tsv')
        rows=list(csv.reader(io.StringIO(metadata.read_text('utf-8')),delimiter='\t',quoting=csv.QUOTE_NONE))
        eligible={r[1]:r for r in rows if r[1] not in excluded and 4<=int(r[5])/16000<=12}
        url=BASE+f'/data/{locale}/audio/test.tar.gz'
        ledger=dict(label='fleurs-'+language+'-partial-archive',url=url,bytes=0,status='started')
        fetch.data['requests'].append(ledger);fetch.save()
        try:
            # Explicit verified CA bundle also covers redirected CDN hosts on
            # this Windows Python build; never disable certificate validation.
            import certifi
            with urllib.request.urlopen(url,timeout=60,context=ssl.create_default_context(cafile=certifi.where())) as response:
                reader=BoundedArchiveReader(response,fetch,ledger)
                with tarfile.open(fileobj=reader,mode='r|gz') as archive:
                    for index,member in enumerate(archive):
                        if index>1500:raise ValueError('Bounded archive search exhausted')
                        name=Path(member.name).name
                        if not member.isfile() or name not in eligible:continue
                        if not 44<=member.size<=1_500_000:raise ValueError('Unexpected audio member size')
                        original=archive.extractfile(member).read();original_hash=sha(original)
                        if original_hash in used:continue
                        source=output/'original'/(language+'-'+name);source.parent.mkdir(parents=True,exist_ok=True)
                        if source.exists():raise FileExistsError(source)
                        source.write_bytes(original)
                        audio=output/'audio'/(language+'-'+name);meta=convert_audio(source,audio)
                        if meta['pcm_sha256'] in used or meta['wav_sha256'] in used:raise ValueError('Historical/duplicate PCM; stop')
                        used.update((original_hash,meta['pcm_sha256'],meta['wav_sha256']))
                        r=eligible[name]
                        records.append(dict(id=f'beta-{language}-{r[0]}-{name[:-4]}',language=language,split='dev',
                            audio=str(audio),original_file=str(source),original_sha256=original_hash,**meta,
                            source_dataset='google/fleurs',source_revision=REVISION,source_member=member.name,source_recording_id=locale+':'+member.name,
                            source_group='fleurs:'+locale+':unknown-speakers',speaker_id=None,speaker_group='fleurs:'+locale+':unknown-speakers',
                            speaker_isolation_status='unavailable; independent files, not verified independent speakers',gender_metadata=r[6] if len(r)>6 else None,
                            source_url=url,license='CC-BY-4.0',license_source=BASE+'/README.md',
                            attribution='FLEURS; Alexis Conneau et al., Google (2022); source contributors',
                            reference_text=r[2],reference_status='pending_human_review',reference_alignment='whole_source_file_only',
                            reference_audio_coverage='unverified',semantic_annotation_status='pending',
                            semantic_labels=dict(entities=[],numbers=[],negation=[],relations=[],tail=[]),
                            scene=['public_human_read_speech','not_game','single_source_file'],historical_match=False,human_quality_review='pending'))
                        count+=1;persist()
                        if count==12:break
            ledger['status']='selected_members_complete';ledger['full_archive_downloaded']=False
        except Exception as exc:
            ledger.update(status='failed',error_type=type(exc).__name__);raise
        finally:fetch.save()
        if count!=12:raise ValueError(f'Only {count} new {language} recordings available')
        print(f'Prepared {language}: {count} new full-source recordings',flush=True)
    noise_license=cached(fetch,'musan-noise-license','https://huggingface.co/datasets/corypaik/musan/raw/76f9882cfa4475efe11508ac9aa32722f84ca5b7/licenses/noise/free-sound/LICENSE','sources/noise-license.txt')
    if 'Public Domain' not in noise_license.read_text('utf-8'):raise ValueError('Noise license missing')
    noise=cached(fetch,'negative-candidates','https://datasets-server.huggingface.co/rows?dataset=corypaik%2Fmusan&config=noise&split=train&offset=12&length=30','sources/negative-candidates.json')
    count=sum(r['split']=='negative' for r in records)
    for entry in json.loads(noise.read_text('utf-8'))['rows']:
        row=entry['row'];id=Path(row['path']).stem
        if row['source']!='free-sound' or id in history['ids']:continue
        original=cached(fetch,id,row['audio'][0]['src'],'original/'+id+'.audio')
        if sha(original.read_bytes()) in used:continue
        audio=output/'audio'/(id+'.wav');meta=convert_audio(original,audio,max_seconds=8)
        if meta['pcm_sha256'] in used or meta['wav_sha256'] in used:raise ValueError('Historical noise PCM')
        used.update((meta['pcm_sha256'],meta['wav_sha256']))
        records.append(dict(id=id,language=None,split='negative',audio=str(audio),original_file=str(original),original_sha256=sha(original.read_bytes()),**meta,
            source_dataset='corypaik/musan',source_revision='76f9882cfa4475efe11508ac9aa32722f84ca5b7',source_member=row['path'],
            source_recording_id='musan:'+row['path'],source_group='musan:'+row['path'],speaker_id=None,speaker_group=None,
            source_url='https://huggingface.co/datasets/corypaik/musan',license='Public-Domain-source-declaration',
            license_source='https://huggingface.co/datasets/corypaik/musan/blob/76f9882cfa4475efe11508ac9aa32722f84ca5b7/licenses/noise/free-sound/LICENSE',
            attribution='MUSAN: David Snyder, Guoguo Chen, Daniel Povey (2015); FreeSound source contributors',
            reference_text='',reference_status='pending_absence_review',reference_alignment='no speech reference',semantic_annotation_status='pending',
            scene=['publisher_label_noise','not_game','first_8s_max'],historical_match=False,human_quality_review='pending'))
        count+=1;persist()
        if count==25:break
    manifest=dict(schema_version=1,dataset_id='voxgo-five-language-beta-20261027-v1',frozen_before_asr=True,
        records=records,history_registry_sha256=sha((output/'historical-registry.json').read_bytes()),
        download_bytes=fetch.data['bytes'],download_limit_bytes=fetch.data['limit'],
        actual_counts={**{l:sum(r['language']==l for r in records) for l in LOCALES},'negative':count},
        limitations=['Public read speech, not licensed real-game acceptance','Speaker IDs unavailable; no verified speaker diversity',
            'References/semantic labels all pending human review','Noise absence pending; music/overlap/fast/game callouts not certified'])
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(counts=manifest['actual_counts'],download_bytes=fetch.data['bytes']),ensure_ascii=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--download',action='store_true');a=p.parse_args()
    if not a.download:p.error('Explicit public-data --download required')
    prepare(a.output)
