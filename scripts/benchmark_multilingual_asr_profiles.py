"""Offline ASR-only policy comparison; no settings writes, translation or telemetry."""
import argparse
from dataclasses import asdict
import gc
import hashlib
import json
from pathlib import Path
import sys
import time
import unicodedata
import wave

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.modules['torch']=None
sys.modules['transformers']=None
from loguru import logger
logger.remove()
import numpy as np
from voxgo.audio.capture import AudioConfig, SystemAudioCapture, apply_audio_latency_preset
from voxgo.asr.whisper_engine import SpeechRecognizer, WhisperConfig
from voxgo.asr.language_profiles import effective_speech_config
from voxgo.config.loader import default_app_config, migrate_runtime_defaults, sync_language_flow, apply_language_runtime_policy

PROFILES={
 'legacy':{'model':'base','threads':1,'beam':1,'maximum':3.0,'pre_roll':300,'idle':350},
 'context':{'model':'base','threads':1,'beam':1,'maximum':4.5,'pre_roll':450,'idle':450},
 'context_beam':{'model':'base','threads':1,'beam':3,'maximum':4.5,'pre_roll':450,'idle':450},
 'context_small':{'model':'small','threads':2,'beam':1,'maximum':4.5,'pre_roll':450,'idle':450},
 'context_beam_two':{'model':'base','threads':2,'beam':3,'maximum':4.5,'pre_roll':450,'idle':450},
 'language_aware':{'resolver':'historical effective_speech_config with explicit research opt-in'},
}

def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFKC',text).casefold() if c.isalnum())

def errors(reference,hypothesis):
    ref,hyp=normalized(reference),normalized(hypothesis)
    previous=list(range(len(hyp)+1))
    for i,left in enumerate(ref,1):
        current=[i]
        for j,right in enumerate(hyp,1):
            current.append(min(previous[j]+1,current[-1]+1,previous[j-1]+(left!=right)))
        previous=current
    return {'reference_characters':len(ref),'errors':previous[-1],'cer':previous[-1]/max(1,len(ref))}

def capture(pcm,policy,audio_config=None):
    # Deliberately do not apply the EN-only timing bias to JA/KO/RU.
    config=audio_config or AudioConfig(latency_mode='fast',sample_rate=16000,channels=1)
    if audio_config is None:
        apply_audio_latency_preset(config)
        config.max_speech_seconds=policy['maximum']
        config.pre_roll_ms=policy['pre_roll'];config.speech_idle_timeout_ms=policy['idle']
    source=SystemAudioCapture(config);segments=[]
    source.set_speech_callback(segments.append)
    samples=np.frombuffer(pcm,dtype='<i2');block_size=1920
    try:
        for offset in range(0,len(samples),block_size):
            chunk=samples[offset:offset+block_size]
            if len(chunk)<block_size:chunk=np.pad(chunk,(0,block_size-len(chunk)))
            source._enqueue_audio_block(chunk.astype('<i2',copy=False).tobytes());source.process_audio()
        for _ in range(12):
            source._enqueue_audio_block(np.zeros(block_size,dtype='<i2').tobytes());source.process_audio()
        if source._speech_buffer:
            source._handle_idle_timeout(time.monotonic()+2)
    finally:source._audio.terminate()
    return segments

def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temporary.replace(path)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--models-directory',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--profiles',nargs='+',choices=tuple(PROFILES),default=list(PROFILES))
    parser.add_argument('--ids',nargs='*')
    args=parser.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    if args.ids:manifest=[r for r in manifest if r['id'] in args.ids]
    result={'profiles':{k:PROFILES[k] for k in args.profiles},'records':[],
      'scope':'offline production capture segmentation and recognizer, no asynchronous queues or live audio',
      'api_requests':0,'human_review':'pending'}
    for profile in args.profiles:
        policy=PROFILES[profile]
        fallback=PROFILES['legacy'] if profile=='language_aware' else policy
        config=WhisperConfig(model_size=fallback['model'],active_model_size=fallback['model'],
            model_dir=str(args.models_directory),local_files_only=True,device='cpu',compute_type='int8',
            auto_cpu_threads=False,cpu_threads=fallback['threads'],num_workers=1,beam_size=fallback['beam'],
            language='auto',prompt_profile='none',initial_prompt='',condition_on_previous_text=False)
        recognizer=SpeechRecognizer(config)
        for sample in manifest:
            if sample['language'] not in {'ja','ko','ru'}:raise ValueError('Unexpected language')
            audio=args.manifest.parent.parent/sample['audio']
            if hashlib.sha256(audio.read_bytes()).hexdigest()!=sample['sha256']:raise ValueError('Audio hash mismatch')
            with wave.open(str(audio),'rb') as stream:
                if (stream.getnchannels(),stream.getsampwidth(),stream.getframerate())!=(1,2,16000):raise ValueError('Unexpected WAV')
                pcm=stream.readframes(stream.getnframes())
            audio_config=None
            if profile=='language_aware':
                app=default_app_config()
                app.translation.source_lang=sample['language'];app.translation.target_lang='zh'
                migrate_runtime_defaults(app);sync_language_flow(app);apply_language_runtime_policy(app)
                app.whisper.multilingual_asr_strategy="language_aware"
                app=effective_speech_config(app, experimental=True)
                config=app.whisper;audio_config=app.audio
                config.local_files_only=True;config.model_dir=str(args.models_directory)
            config.source_language=sample['language']
            recognizer.request_config(config)
            recognizer._apply_pending_config();recognizer.initialize()
            paths=[('capture_cut',capture(pcm,policy,audio_config))]
            if profile in {'legacy','context_small'}:paths.insert(0,('whole',None))
            for path,segments in paths:
                items=[(pcm,sample['seconds'],'whole')] if segments is None else [(s.audio_data,s.duration_seconds,s.reason) for s in segments]
                outputs=[]
                for data,duration,reason in items:
                    start=time.perf_counter();cpu=time.process_time()
                    transcript=recognizer.transcribe_audio_bytes_with_language(data,16000)
                    outputs.append({'asr':asdict(transcript),'ms':round((time.perf_counter()-start)*1000,2),
                        'cpu_seconds':time.process_time()-cpu,'seconds':duration,'reason':reason})
                hypothesis=' '.join(r['asr']['text'] for r in outputs)
                row={'id':sample['id'],'language':sample['language'],'reference':sample['reference_text'],
                     'profile':profile,'path':path,'hypothesis':hypothesis,'segments':outputs,
                     'effective_whisper':{k:getattr(config,k) for k in ('active_model_size','beam_size','cpu_threads','language')},
                     **errors(sample['reference_text'],hypothesis)}
                result['records'].append(row);write(args.output,result)
                print(json.dumps({'profile':profile,'language':sample['language'],'path':path,'id':sample['id'],
                                  'cer':round(row['cer'],3),'segments':len(outputs)},ensure_ascii=False),flush=True)
        recognizer.cleanup();gc.collect()
    write(args.output,result)

if __name__=='__main__':main()
