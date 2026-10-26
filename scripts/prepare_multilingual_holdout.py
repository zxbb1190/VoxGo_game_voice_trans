"""Prepare unseen FLEURS read speech; not real game or bilingual acceptance."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request
import wave

import numpy as np
import soundfile as sf

REVISION = '70bb2e84b976b7e960aa89f1c648e09c59f894dd'
BASE = f'https://huggingface.co/datasets/google/fleurs/resolve/{REVISION}'


def prepare(language, locale, root, excluded, count):
    metadata = urllib.request.urlopen(f'{BASE}/data/{locale}/test.tsv', timeout=45).read(4_000_000)
    (root / f'{locale}-test.tsv').write_bytes(metadata)
    rows = csv.reader(io.StringIO(metadata.decode('utf-8')), delimiter='\t', quoting=csv.QUOTE_NONE)
    eligible = {r[1]: r for r in rows if 4 <= int(r[5])/16000 <= 10 and r[1] not in excluded}
    records = []
    url = f'{BASE}/data/{locale}/audio/test.tar.gz'
    with urllib.request.urlopen(url, timeout=60) as response, tarfile.open(fileobj=response, mode='r|gz') as archive:
        for index, member in enumerate(archive):
            if index > 1500: raise ValueError('Bounded archive scan exhausted')
            name = Path(member.name).name
            if not member.isfile() or name not in eligible: continue
            if not 44 <= member.size <= 1_000_000: raise ValueError('Unexpected member size')
            original = archive.extractfile(member).read()
            samples, rate = sf.read(io.BytesIO(original), dtype='float32')
            if rate != 16000 or samples.ndim != 1: raise ValueError('Unexpected audio format')
            rms = float(np.sqrt(np.mean(samples**2)))
            if rms < .002: continue
            path = root / f'{language}-{name}'
            with wave.open(str(path), 'wb') as stream:
                stream.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
                stream.writeframes((np.clip(samples, -1, 1)*32767).astype('<i2').tobytes())
            row = eligible[name]
            records.append(dict(id=f'fleurs-{language}-holdout-{row[0]}-{name[:-4]}', language=language,
                audio=str(path.resolve()), reference_text=row[2], seconds=len(samples)/rate,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                original_audio_sha256=hashlib.sha256(original).hexdigest(), original_member=member.name,
                revision=REVISION, source=f'google/fleurs {locale}/test', archive_url=url,
                metadata_sha256=hashlib.sha256(metadata).hexdigest(), full_archive_sha256=None,
                license='CC-BY-4.0', license_source=f'{BASE}/README.md',
                attribution='FLEURS, Alexis Conneau et al., Google, 2022; dataset contributors',
                conversion='float WAV to mono PCM16 16kHz; clip [-1,1], scale 32767',
                real_game_audio=False, human_quality_review='pending', split='holdout'))
            if len(records) == count: break
    if len(records) != count: raise ValueError('Incomplete holdout')
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exclude-manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--count-per-language', type=int, default=3, choices=range(1,11))
    parser.add_argument('--languages', nargs='+', choices=('ja','ko','ru'), default=['ja','ko','ru'])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    previous = json.loads(args.exclude_manifest.read_text(encoding='utf-8-sig'))
    excluded = {Path(r['original_member']).name for r in previous}
    records = []
    for language, locale in [('ja','ja_jp'),('ko','ko_kr'),('ru','ru_ru')]:
        if language not in args.languages: continue
        records += prepare(language, locale, args.output, excluded, args.count_per_language)
        (args.output/'manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(f'Prepared {language}: {args.count_per_language} unseen read-speech clips', flush=True)


if __name__ == '__main__': main()
