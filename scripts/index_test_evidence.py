"""Index tracked historical evidence without moving or rewriting any snapshot."""
import argparse
from collections import defaultdict
import hashlib
import io
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = Path('docs/testing/evidence')
INDEX = EVIDENCE / 'README.md'


def render_index():
    output = subprocess.check_output(
        ['git', 'ls-files', '--stage', '-z', '--', EVIDENCE.as_posix()], cwd=ROOT)
    groups = defaultdict(list)
    for entry in output.decode('utf-8').split('\0'):
        if not entry:
            continue
        metadata, name = entry.split('\t', 1)
        _, object_id, stage = metadata.split()
        if stage != '0':
            raise ValueError(f'Unmerged evidence: {name}')
        if name == INDEX.as_posix():
            continue
        relative = Path(name).relative_to(EVIDENCE)
        if len(relative.parts) < 2:
            continue
        groups[relative.parts[0]].append((Path(name), object_id))
    object_ids = sorted({oid for paths in groups.values() for _, oid in paths})
    # Hash Git's stored bytes, not checkout CRLF conversion. This makes the
    # catalog identical on a fresh runner, Windows, and Linux.
    batch = subprocess.check_output(
        ['git', 'cat-file', '--batch'], input=('\n'.join(object_ids) + '\n').encode(), cwd=ROOT)
    stream, blobs = io.BytesIO(batch), {}
    for expected in object_ids:
        object_id, kind, size = stream.readline().decode().split()
        if object_id != expected or kind != 'blob':
            raise ValueError('Evidence is not a Git blob')
        blobs[object_id] = stream.read(int(size))
        if stream.read(1) != b'\n':
            raise ValueError('Incomplete Git blob response')
    rows, total_files, total_bytes = [], 0, 0
    for name, paths in sorted(groups.items()):
        digest, size = hashlib.sha256(), 0
        for path, object_id in sorted(paths, key=lambda item: item[0].as_posix()):
            data = blobs[object_id]
            size += len(data)
            # Hash each path and byte digest; no logs or private contents are
            # copied into the human-readable catalog.
            digest.update(path.relative_to(EVIDENCE / name).as_posix().encode('utf-8') + b'\0')
            digest.update(hashlib.sha256(data).digest())
        rows.append(f'| [{name}]({name}/) | {len(paths)} | {size:,} | `{digest.hexdigest()}` |')
        total_files += len(paths)
        total_bytes += size
    return '\n'.join([
        '# Historical acceptance evidence', '',
        'These are immutable records of specific past runs, not active source code or proof of current release status.',
        'Use [the testing guide](../README.md) for current commands and [the release procedure](../../release_process.md) for releases.', '',
        'Keep original paths and bytes: reports, provenance, hashes and external links may reference them.',
        'Store routine CI logs and coverage in Actions artifacts (14-day retention), not new evidence snapshots.',
        'Add a historical batch only for an explicit release or acceptance record; exclude keys and user configuration.', '',
        f'Tracked batches: **{len(groups)}**; files: **{total_files:,}**; bytes: **{total_bytes:,}**.', '',
        'Regenerate with `python scripts/index_test_evidence.py --write`; verify with `--check`.',
        'Sizes and tree hashes cover Git blob bytes and sorted relative paths, independent of checkout line endings.',
        'Stage new evidence files before regenerating; the index intentionally ignores untracked local output.', '',
        '| Batch | Files | Bytes | SHA-256 tree digest |',
        '|---|---:|---:|---|', *rows, '',
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    rendered = render_index()
    target = ROOT / INDEX
    if args.write:
        target.write_text(rendered, encoding='utf-8', newline='\n')
        print(f'Updated {INDEX.as_posix()}')
    elif not target.exists() or target.read_text(encoding='utf-8') != rendered:
        parser.exit(1, 'Evidence index differs; run scripts/index_test_evidence.py --write\n')
    else:
        print('Historical evidence index and byte digests match')


if __name__ == '__main__':
    main()
