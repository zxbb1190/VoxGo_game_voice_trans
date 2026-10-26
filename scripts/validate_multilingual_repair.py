"""Explicit fixed-provider repair verification; authored/public inputs only.

No settings writes, telemetry, retries, service substitution or GUI audio capture.
The audio path is paced PCM -> actual pipeline -> offscreen Qt, not a real game.
"""
import argparse
import asyncio
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.compare_public_asr_translation import (
    DEFAULT_PROFILE, DEFAULT_CREDENTIALS, MODEL, digest, execute, load_config, write_json,
)
from voxgo.languages import ONLINE_DIRECTIONS


def text_plan():
    corpus = ROOT/'tests/assets/multilingual_online/repair-directions.json'
    data = json.loads(corpus.read_text(encoding='utf-8'))
    rows = data['cases']
    if data['provenance'] != 'newly_authored_nonprivate_game_phrases': raise ValueError('Unexpected source')
    if {(r['source_lang'],r['target_lang']) for r in rows} != ONLINE_DIRECTIONS: raise ValueError('Incomplete coverage')
    if len({r['id'] for r in rows}) != len(rows): raise ValueError('Duplicate IDs')
    return {'inputs': rows, 'schedule': [{'case_id': r['id'], 'repeat': 1} for r in rows],
            'human_review': 'pending', 'release_approved': False}, corpus


class AudioAttempts:
    def __init__(self, path): self.path, self.count = path, 0
    def reserve(self, label):
        # This is a deterministic experiment bound, not a restored user budget.
        if self.count >= 60: raise RuntimeError('Unexpected replay request volume; stop')
        self.count += 1
        with self.path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'attempt':self.count,'stage':label,'model':MODEL})+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-live', action='store_true')
    parser.add_argument('--stage', choices=('text','audio'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--audio-manifest', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    plan, corpus = text_plan()
    write_json(args.output/'plan.json', plan)
    if not args.run_live: return
    settings = DEFAULT_CREDENTIALS
    input_paths = {'credentials': settings, 'candidate_settings': DEFAULT_PROFILE/'user_settings.json',
                   'candidate_baseline': DEFAULT_PROFILE/'acceptance.config.json', 'corpus':corpus}
    hashes = {key:{'path':str(path),'sha256':digest(path.read_bytes())} for key,path in input_paths.items()}
    config = load_config(DEFAULT_PROFILE, settings)
    if args.stage == 'text':
        result = asyncio.run(execute(plan, config, args.output, hashes))
        print(json.dumps({'http_attempts':result['http_attempts'],'status':result['status']}), flush=True)
    else:
        if not args.audio_manifest: raise ValueError('Explicit licensed audio manifest required')
        from scripts.validate_multilingual_live import audio_run
        budget = AudioAttempts(args.output/'attempts.jsonl')
        try:
            audio_run(config, budget, args.audio_manifest, args.output/'audio-results.json')
        finally:
            write_json(args.output/'integrity.json', {'http_attempts':budget.count,
                'input_files_unchanged':{k:digest(Path(v['path']).read_bytes())==v['sha256'] for k,v in hashes.items()},
                'human_review':'pending','real_game_acceptance':'incomplete','release_approved':False})
        print(json.dumps({'http_attempts':budget.count}), flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as error:
        print(f'Validation stopped ({type(error).__name__}); inspect sanitized artifacts.', file=sys.stderr)
        sys.exit(1)
