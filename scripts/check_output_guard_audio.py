"""Offline real-model regression; cached models required, never downloaded.

Everyday CI replays captured decoder outputs in test_output_guard_regressions.
This command performs fresh inference and the formal post-ASR pipeline using
the same audio. It does not test physical capture, live VAD or model accuracy.
"""
import argparse
import asyncio
from collections import defaultdict
from dataclasses import asdict
import hashlib
import importlib.metadata
import ipaddress
import json
from pathlib import Path
import re
import socket
import sys
import time
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voxgo.asr.pipeline import SpeechPipeline
from voxgo.asr.whisper_engine import SpeechRecognizer, WhisperConfig
from voxgo.audio.benchmark import load_benchmark_audio
from voxgo.audio.capture import AudioConfig, SpeechSegment, calculate_rms_dbfs
from voxgo.config.schema import AppConfig, DebugConfig
from voxgo.runtime.events import EventBus, TranscriptReady
from voxgo.runtime.work_items import LatencyTrace, SpeechWorkItem
from voxgo.translation.base import TranslationConfig, TranslationRequest
from voxgo.translation.local import LocalTranslationProvider, shutdown_local_translation


class ObservedRecognizer(SpeechRecognizer):
    """Observe a fresh result without replacing the model or changing inference."""
    def transcribe_audio_bytes_with_language(self, *args, **kwargs):
        self.last_result = super().transcribe_audio_bytes_with_language(*args, **kwargs)
        return self.last_result


def checked_audio(relative_path, digest):
    path = ROOT / relative_path
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError(f'Audio fixture changed: {relative_path}')
    return load_benchmark_audio(path)


def run(output, model_dir):
    fixture = json.loads((ROOT / 'tests/assets/output_guard/captured.json').read_text(encoding='utf-8'))
    audio, rate = checked_audio(fixture['audio'], fixture['audio_sha256'])
    cases = []
    for row in fixture['cases']:
        pcm = (audio[int(row['start'] * rate):int(row['end'] * rate)].astype(np.float32)
               * row['gain']).astype(np.int16)
        cases.append((row['id'], pcm, rate, row['expected_blocked'], row.get('expected_text'), False))
    for row in fixture['callouts']:
        pcm, sr = checked_audio(row['audio'], row['sha256'])
        cases.append((row['id'], pcm, sr, False, row['reference'], True))
        # An explicit low-volume synthetic positive complements the real quiet
        # game excerpt; preserve its provenance rather than calling it human.
        gain = min(1.0, 10 ** ((-48.0 - calculate_rms_dbfs(pcm)) / 20))
        quiet = (pcm.astype(np.float32) * gain).astype(np.int16)
        cases.append((row['id'] + '_quiet', quiet, sr, False, row['reference'], True))

    config = AppConfig(audio=AudioConfig(latency_mode='fast'),
                       whisper=WhisperConfig(**fixture['model'], local_files_only=True,
                                             model_dir=str(model_dir)),
                       translation=TranslationConfig(provider='local', enable_local_phrase_cache=False),
                       debug=DebugConfig())
    recognizer = ObservedRecognizer(config.whisper)
    report = {'kind': 'fresh local model inference + production post-ASR pipeline',
              'physical_capture': False, 'live_vad': False, 'online_api': False,
              'versions': {name: importlib.metadata.version(name)
                           for name in ('faster-whisper', 'ctranslate2', 'av')},
              'model': fixture['model'], 'cases': []}
    try:
        recognizer.initialize()
        for name, pcm, sr, blocked, expected, synthetic in cases:
            bus, stats, events = EventBus(), defaultdict(int), []
            bus.subscribe(TranscriptReady, events.append)
            pipeline = SpeechPipeline(lambda: config, lambda: recognizer, bus, stats,
                                      lambda: True, lambda: False, lambda: name, {}, lambda *args: None)
            rms = calculate_rms_dbfs(pcm)
            seconds = len(pcm) / sr
            segment = SpeechSegment(audio_data=pcm.tobytes(), sample_rate=sr,
                duration_seconds=seconds, voice_duration_seconds=seconds, block_count=1,
                voice_blocks=1, peak_rms_dbfs=rms, energy_threshold_dbfs=-40,
                noise_floor_dbfs=None,
                reason='output_guard_audio_regression', vad_voice_blocks=1,
                energy_voice_blocks=1, vad_confidence=1, activity_source='benchmark')
            now = time.time()
            started = time.perf_counter()
            pipeline._process(SpeechWorkItem(segment=segment, trace=LatencyTrace(name, now, now),
                source_lang='en', target_lang='zh', whisper_language='auto',
                low_confidence=rms < -39, candidate_labels=('candidate', 'low_confidence') if rms < -39 else ('candidate',)))
            result = recognizer.last_result
            actual = ' '.join(event.text for event in events)
            if blocked:
                passed = result.runaway_guarded and not events and stats['filtered_speech'] == 1
            else:
                tokens = lambda value: set(re.findall(r'[a-z]+', value.lower()))
                passed = bool(events) and not result.runaway_guarded and (
                    tokens(expected) <= tokens(actual) if synthetic else actual == expected)
            report['cases'].append(dict(id=name, synthetic=synthetic, rms_dbfs=rms,
                expected_blocked=blocked, published=actual, asr=asdict(result), stats=dict(stats),
                inference_and_filter_ms=round((time.perf_counter() - started) * 1000, 2),
                passed=passed and stats['errors'] == 0))
        # Bypass ASR intentionally to test the second independent protection:
        # run the old invalid ASR text through the actual local translator.
        async def translation_check():
            provider = LocalTranslationProvider(config.translation)
            result = await provider.translate(TranslationRequest(
                fixture['cases'][0]['asr']['raw_text'], 'en', 'zh'))
            return dict(result=asdict(result), passed=bool(result.failure_reason)
                        and result.translated.startswith('[翻译失败]') and '⁇' not in result.translated)
        report['local_translation_guard'] = asyncio.run(translation_check())
        report['passed'] = (all(case['passed'] for case in report['cases'])
                            and report['local_translation_guard']['passed'])
    finally:
        recognizer.cleanup()
        report['local_translation_stopped'] = shutdown_local_translation()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': report['passed'], 'cases': len(report['cases']), 'output': str(output)}))
    return 0 if report['passed'] and report['local_translation_stopped'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model-dir', type=Path, default=ROOT / '.models')
    args = parser.parse_args()
    # Async event loops may use local socket pairs. External network is denied.
    def offline_connect(original):
        def connect(sock, address):
            if isinstance(address, tuple) and not ipaddress.ip_address(address[0]).is_loopback:
                raise OSError('Offline audio regression')
            return original(sock, address)
        return connect

    with patch.object(socket.socket, 'connect', offline_connect(socket.socket.connect)), \
         patch.object(socket.socket, 'connect_ex', offline_connect(socket.socket.connect_ex)):
        raise SystemExit(run(args.output, args.model_dir))
