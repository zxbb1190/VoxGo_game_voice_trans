"""Offline crossing of actual RU segment PCM and old/new recognizer configs.

Uses only observed exact frame ranges; no recutting, text repair or API calls.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.compare_speech_strategies import pcm
from voxgo.config.loader import default_app_config,migrate_runtime_defaults,sync_language_flow,apply_language_runtime_policy
from voxgo.asr.language_profiles import effective_speech_config
from voxgo.asr.whisper_engine import SpeechRecognizer,should_drop_transcription_result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);args=parser.parse_args()
    workload=json.loads((args.root/'manifest.json').read_text(encoding='utf8'))
    clips=[r for r in workload if r['language']=='ru']
    data=b'\0'*(32000*3)+b''.join(pcm(r)+b'\0'*(32000*2) for r in clips)+b'\0'*32000
    clip_start=48000;clip_end=clip_start+len(pcm(clips[0]))//2
    records=[]
    for segmentation,strategy in [('legacy','language_aware'),('language_aware','legacy')]:
        observed=json.loads((args.root/f'r1-ru-{segmentation}/audio.json').read_text(encoding='utf8'))[0]
        config=default_app_config();config.translation.source_lang='ru';config.translation.target_lang='zh'
        config.whisper.multilingual_asr_strategy=strategy
        migrate_runtime_defaults(config);sync_language_flow(config);apply_language_runtime_policy(config)
        config=effective_speech_config(config, experimental=True);config.whisper.local_files_only=True
        recognizer=SpeechRecognizer(config.whisper);recognizer.initialize()
        try:
            for row in observed['stream_asr']:
                start,end=row['source_start_frame'],row['source_end_frame']
                if start is None or end is None:raise ValueError('Cannot infer an unobserved frame range')
                if start>=clip_end or end<=clip_start:continue
                segment=data[start*2:end*2]
                result=recognizer.transcribe_audio_bytes_with_language(segment,16000)
                records.append({'capture_strategy':segmentation,'recognizer_strategy':strategy,
                    'cpu_threads':config.whisper.cpu_threads,'beam_size':config.whisper.beam_size,
                    'source_start_frame':start,'source_end_frame':end,'pcm_sha256':hashlib.sha256(segment).hexdigest(),
                    'asr':asdict(result),'filter_reason':should_drop_transcription_result(result,'ru',config=config.whisper)})
        finally:recognizer.cleanup()
    output={'api_requests':0,'sample':clips[0]['id'],'reference':clips[0]['reference_text'],
        'scope':'exact observed capture inputs with crossed recognizer configs; neither formal parameter changes nor language forcing',
        'records':records,'human_review':'pending'}
    (args.root/'russian-cross-replay.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for row in records:print(row['capture_strategy'],row['recognizer_strategy'],row['asr']['text'],row['asr']['language'],row['filter_reason'])


if __name__=='__main__':main()
