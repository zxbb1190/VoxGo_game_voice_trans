"""Explicit SiliconFlow comparison of licensed reference text and recorded ASR.

Tooling only: no GUI, audio capture, analytics, config writes, tuning or retries.
Default is offline planning. --run-live is required to read an existing key.
"""
import argparse
import asyncio
from dataclasses import fields, replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Match the frozen client's optional converter exclusions; no ASR is loaded.
sys.modules['torch'] = None
sys.modules['transformers'] = None
from loguru import logger
logger.remove()  # Never print provider errors, headers or credentials.
from voxgo.translation import GameTranslator, TranslationConfig, clean_translation_output
from voxgo.translation.prompt import translation_system_prompt

MODEL = 'tencent/Hunyuan-MT-7B'
ENDPOINT = 'https://api.siliconflow.cn/v1/chat/completions'
SUMMARY = ROOT / 'docs/testing/evidence/v0.5.3-online-user-smoke/session-summary.json'
DEFAULT_PROFILE = Path(r'E:\my\my\VoxGo-0.5.3-Online-Acceptance-caed9130/candidate')
DEFAULT_CREDENTIALS = Path(r'E:\my\my\game_voice_translator/user_settings.json')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value, secret=''):
    """Atomic tool artifact write; never write any credential field/value."""
    serialized = json.dumps(value, ensure_ascii=False, indent=2)
    if secret:
        serialized = serialized.replace(secret, '[REDACTED]')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    try:
        temporary.write_text(serialized + '\n', encoding='utf-8')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def build_plan(summary):
    if summary.get('source') != 'user_operated_windows_session_and_public_audio_log_windows':
        raise ValueError('Only the fixed public-audio session is accepted')
    rows, seen, references = [], {}, {}

    def add(arm, language, text, sample, play, segment=None):
        key = (arm, language, text)
        provenance = {'sample_id': sample, 'play_index': play, 'segment_index': segment}
        if key in seen:
            seen[key]['provenance'].append(provenance)
            return
        row = {'id': f'case-{len(rows)+1:02d}', 'arm': arm, 'source_lang': language,
               'target_lang': 'zh', 'text': text, 'provenance': [provenance],
               'human_review': 'pending'}
        rows.append(row)
        seen[key] = row

    for case in summary['cases']:
        language, sample = case['language'], case['sample_id']
        if language not in {'ja', 'ko', 'ru'} or case.get('real_game_audio') is not False:
            raise ValueError('Only JA/KO/RU public read speech is accepted')
        if case.get('license') != 'CC-BY-4.0' or not sample.startswith(f'fleurs-{language}-test-'):
            raise ValueError('Licensed public sample provenance is required')
        reference = case['reference']
        if sample in references and references[sample] != reference:
            raise ValueError('Conflicting standard transcripts')
        references[sample] = reference
        add('reference_full', language, reference, sample, case['play_index'])
        texts = [entry['text'] for entry in case['asr']]
        if not texts or any(not text.strip() or len(text) >= 80 for text in texts):
            raise ValueError('Missing or possibly log-truncated ASR text; do not infer a replay')
        for index, text in enumerate(texts, 1):
            add('actual_fragment', language, text, sample, case['play_index'], index)
        # Only join verbatim fragments with spaces. No restoration/correction of
        # characters, punctuation, place names or broken compounds is allowed.
        add('actual_joined', language, ' '.join(texts), sample, case['play_index'])
    schedule = [{'case_id': row['id'], 'repeat': 1} for row in rows]
    schedule += [{'case_id': row['id'], 'repeat': 2} for row in reversed(rows)]
    return {'model': MODEL, 'arms': ['reference_full', 'actual_fragment', 'actual_joined'],
            'inputs': rows, 'schedule': schedule, 'human_review': 'pending',
            'limitations': ['Same 3 recordings; not independent language acceptance or game material.',
                            'Two scheduled replicates are not adaptive retries.',
                            'Joined ASR is a context probe, not a proposed production segmentation change.']}


def load_config(profile, credential_path):
    base = json.loads((profile / 'acceptance.config.json').read_text(encoding='utf-8-sig'))
    saved = json.loads((profile / 'user_settings.json').read_text(encoding='utf-8-sig'))
    consent = json.loads((profile / 'telemetry_consent.json').read_text(encoding='utf-8-sig'))
    if any(value.get('telemetry_consent') != 'denied' for value in (base['app'], saved['app'], consent)):
        raise ValueError('The isolated candidate Full consent must remain denied')
    effective = {**base['translation'], **saved['translation']}
    if (effective.get('provider') != 'openai_compatible' or effective.get('model') != MODEL
            or effective.get('context_messages') != 0):
        raise ValueError('The actual session model/provider/zero-context setting is required')
    credentials = json.loads(credential_path.read_text(encoding='utf-8-sig'))['translation']
    if (credentials.get('provider') != 'openai_compatible' or credentials.get('model') != MODEL
            or credentials.get('endpoint') not in {ENDPOINT, ENDPOINT+'/', 'https://api.siliconflow.cn/v1', 'https://api.siliconflow.cn/v1/'}
            or not credentials.get('api_key', '').strip()
            or credentials['api_key'].startswith(('YOUR_', 'REPLACE_'))):
        raise ValueError('Existing exact SiliconFlow/Hunyuan configuration unavailable; stop')
    config = TranslationConfig(**{field.name: effective[field.name] for field in fields(TranslationConfig) if field.name in effective})
    config.endpoint = ENDPOINT
    config.api_key = credentials['api_key'].strip()
    return config


class AttemptJournal:
    def __init__(self, path):
        self.path = path
        self.count = 0
        if path.exists() and path.stat().st_size:
            raise ValueError('Existing call journal must not be overwritten or replayed')

    def append(self, row):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
            stream.flush()
            os.fsync(stream.fileno())

    def reserve(self, case_id, repeat, payload):
        self.append({'kind': 'reserved_before_http', 'attempt': self.count+1, 'case_id': case_id,
                     'repeat': repeat, 'utc': utc_now(), 'model': MODEL,
                     'payload_sha256': digest(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode())})
        self.count += 1


class CountedTranslator(GameTranslator):
    def __init__(self, config, journal):
        super().__init__(config)
        self.journal = journal
        self.case_id = ''
        self.repeat = 0
        self.http_status = None

    async def _get_session(self):
        session = await super()._get_session()
        if not getattr(session, '_comparison_wrapped', False):
            original_post = session.post
            owner = self

            class RecordedRequest:
                def __init__(self, context): self.context = context
                async def __aenter__(self):
                    response = await self.context.__aenter__()
                    owner.http_status = response.status
                    return response
                async def __aexit__(self, *args): return await self.context.__aexit__(*args)

            def counted(url, *args, **kwargs):
                payload = kwargs.get('json', {})
                if url != ENDPOINT or payload.get('model') != MODEL:
                    raise ValueError('Unexpected origin/model blocked before HTTP')
                owner.journal.reserve(owner.case_id, owner.repeat, payload)
                kwargs['allow_redirects'] = False
                return RecordedRequest(original_post(url, *args, **kwargs))
            session.post = counted
            session._comparison_wrapped = True
        return session


async def execute(plan, config, output, input_hashes):
    journal = AttemptJournal(output / 'attempts.jsonl')
    client = CountedTranslator(config, journal)
    lookup = {row['id']: row for row in plan['inputs']}
    data = {'started_utc': utc_now(), 'status': 'running', 'requested_model': MODEL,
            'endpoint': ENDPOINT, 'input_hashes': input_hashes, 'parameters': {
                key: getattr(config, key) for key in ('max_tokens', 'temperature', 'context_messages',
                'timeout_seconds', 'max_concurrent_requests', 'enable_local_phrase_cache')},
            'system_prompt_sha256': {lang: digest(translation_system_prompt(lang, 'zh').encode()) for lang in ('ja', 'ko', 'ru')},
            'planned_http_attempts': len(plan['schedule']), 'http_attempts': 0,
            'records': [], 'human_review': 'pending', 'release_approved': False}
    write_json(output/'results.json', data, config.api_key)
    try:
        for scheduled in plan['schedule']:
            case = lookup[scheduled['case_id']]
            client.case_id, client.repeat = case['id'], scheduled['repeat']
            client.http_status = None
            before = journal.count
            started = time.perf_counter()
            result = await client.translate_result_with_config(case['text'], case['source_lang'],
                replace(config, source_lang=case['source_lang'], target_lang=case['target_lang']))
            elapsed_ms = round((time.perf_counter()-started)*1000, 2)
            raw = '' if result is None else result.translated
            response = {} if result is None else (result.raw or {})
            row = {'case_id': case['id'], 'repeat': scheduled['repeat'], 'arm': case['arm'],
                   'source_lang': case['source_lang'], 'target_lang': case['target_lang'], 'input': case['text'],
                   'raw_translation': raw, 'display_translation': clean_translation_output(raw),
                   'http_status': client.http_status, 'http_attempted': journal.count > before,
                   'failure_reason': '' if result is None else result.failure_reason,
                   'finish_reason': (response.get('choices') or [{}])[0].get('finish_reason'),
                   'response_model': response.get('model'), 'usage': response.get('usage'),
                   'elapsed_ms': elapsed_ms, 'human_review': 'pending'}
            data['records'].append(row)
            data['http_attempts'] = journal.count
            journal.append({'kind': 'case_completed', 'case_id': case['id'], 'repeat': scheduled['repeat'],
                            'utc': utc_now(), 'http_status': client.http_status, 'elapsed_ms': elapsed_ms,
                            'failure_reason': row['failure_reason']})
            write_json(output/'results.json', data, config.api_key)
            print(f"Completed {len(data['records'])}/{len(plan['schedule'])}: {case['id']} repeat={scheduled['repeat']} status={client.http_status}", flush=True)
            if client.http_status in {301, 302, 303, 307, 308, 401, 403, 404, 429}:
                data['status'] = 'stopped_on_service_or_origin_error'
                break
        else:
            data['status'] = 'complete'
    finally:
        await client.close()
        data['http_attempts'] = journal.count
        data['ended_utc'] = utc_now()
        unchanged = {label: digest(Path(value['path']).read_bytes()) == value['sha256'] for label,value in input_hashes.items()}
        data['input_files_unchanged'] = unchanged
        write_json(output/'results.json', data, config.api_key)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-live', action='store_true')
    parser.add_argument('--candidate-profile', type=Path, default=DEFAULT_PROFILE)
    parser.add_argument('--credential-settings', type=Path, default=DEFAULT_CREDENTIALS)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    summary = json.loads(SUMMARY.read_text(encoding='utf-8-sig'))
    plan = build_plan(summary)
    if (args.output/'results.json').exists() or (args.output/'attempts.jsonl').exists():
        raise ValueError('Use a fresh output directory; previous experiments are preserved')
    write_json(args.output/'plan.json', plan)
    print(json.dumps({'inputs': len(plan['inputs']), 'scheduled_attempts': len(plan['schedule']),
                      'model': MODEL, 'mode': 'live' if args.run_live else 'offline_plan'}), flush=True)
    if not args.run_live:
        return
    inputs = {'credentials': args.credential_settings,
              'candidate_settings': args.candidate_profile/'user_settings.json',
              'candidate_baseline': args.candidate_profile/'acceptance.config.json',
              'public_summary': SUMMARY}
    hashes = {key:{'path':str(path),'sha256':digest(path.read_bytes())} for key,path in inputs.items()}
    config = load_config(args.candidate_profile, args.credential_settings)
    lock = args.output/'running.lock'
    with lock.open('x', encoding='utf-8') as stream: stream.write(str(os.getpid()))
    try:
        data = asyncio.run(execute(plan, config, args.output, hashes))
        print(json.dumps({'status':data['status'],'http_attempts':data['http_attempts'],
                          'input_files_unchanged':data['input_files_unchanged']}), flush=True)
    finally:
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # No exception/provider payload can expose a real key to the console.
        print(f'Comparison stopped ({type(error).__name__}); inspect sanitized local artifacts.', file=sys.stderr)
        sys.exit(1)
