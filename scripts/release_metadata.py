"""Prepare release notes and synchronize the site only after a real release exists."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.build_website_changelog import github_json, release_notes

REPO = 'https://github.com/zxbb1190/VoxGo_game_voice_trans'
EDITIONS = ('lite', 'full', 'full-cuda', 'cuda-runtime')


def package_name(version, edition):
    return f'VoxGo-v{version}-{edition}.zip'


def render_notes(root, version, packages):
    draft = (root / f'docs/releases/v{version}.md').read_text('utf-8-sig')
    start = draft.index('## 更新内容\n')
    end = draft.index('## 构建与发布', start)
    body = draft[start:end].strip()
    body = body.replace('## 更新内容\n', '### 更新内容\n').replace("## What's new\n", "### What's new\n")
    # Known-limitations sections remain separate from both feature lists.
    release_notes(body)
    hashes, downloads = {}, []
    for edition in EDITIONS:
        path = packages / package_name(version, edition)
        digest = hashlib.sha256()
        with path.open('rb') as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                digest.update(chunk)
        hashes[edition] = digest.hexdigest()
        downloads.append(f'- `{path.name}`: {path.stat().st_size / 1048576:.2f} MiB\n  - SHA256: `{digest.hexdigest()}`')
    return f'## VoxGo {version}\n\n{body}\n\n### Downloads\n\n' + '\n'.join(downloads) + '\n', hashes


def sync_site(root, version, release, hashes, mirror_verified=False):
    """Validate every artifact before changing public URLs or update metadata."""
    tag = f'v{version}'
    if release.get('tag_name') != tag or release.get('draft') or release.get('prerelease') or not release.get('published_at'):
        raise ValueError('Expected the published stable release for the requested version')
    zh, en = release_notes(release.get('body', ''))
    assets = {asset['name']: asset for asset in release.get('assets', [])}
    values = {}
    for edition in EDITIONS:
        name = package_name(version, edition)
        asset = assets.get(name, {})
        url = f'{REPO}/releases/download/{tag}/{name}'
        digest = hashes.get(edition, '')
        if not re.fullmatch('[a-f0-9]{64}', digest):
            raise ValueError(f'Missing SHA256 for {edition}')
        if asset.get('state') != 'uploaded' or asset.get('size', 0) <= 0 or asset.get('browser_download_url') != url:
            raise ValueError(f'Missing or invalid published asset: {name}')
        if asset.get('digest') and asset['digest'] != 'sha256:' + digest:
            raise ValueError(f'Published digest mismatch: {name}')
        suffix = edition.replace('-', '_')
        values['cuda_runtime_url' if edition == 'cuda-runtime' else f'download_{suffix}_url'] = url
        values[f'sha256_{suffix}'] = digest

    manifest_path = root / 'docs/update.json'
    manifest = json.loads(manifest_path.read_text('utf-8-sig'))
    manifest.update(values, latest=version, channel='stable', title=f'VoxGo v{version}',
                    notes=en, notes_zh=zh, notes_en=en, mandatory=False,
                    release_url=f'{REPO}/releases/tag/{tag}')
    writes = {manifest_path: json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'}
    mirror_url = f'https://gitcode.com/zxbb1190/VoxGo/releases/download/{tag}/{package_name(version, "lite")}'
    for relative in ('docs/index.html', 'docs/en/index.html'):
        path = root / relative
        page = path.read_text('utf-8')
        mirrors = re.findall(r'https://gitcode\.com/[^"<> ]+', page)
        saved = list(dict.fromkeys(mirrors))
        for index, url in enumerate(saved):
            page = page.replace(url, f'__VOXGO_MIRROR_{index}__')
        page = re.sub(r'VoxGo-v\d+\.\d+\.\d+', f'VoxGo-v{version}', page)
        page = re.sub(r'releases/download/v\d+\.\d+\.\d+', f'releases/download/{tag}', page)
        page = re.sub(r'VoxGo v\d+\.\d+\.\d+', f'VoxGo v{version}', page)
        for index, url in enumerate(saved):
            page = page.replace(f'__VOXGO_MIRROR_{index}__', mirror_url if mirror_verified else url)
        mirror_version = version if mirror_verified else (re.search(r'/download/v(\d+\.\d+\.\d+)/', saved[0]).group(1) if saved else '')
        page = re.sub(r'国内镜像下载（Lite[^）]*）', f'国内镜像下载（Lite v{mirror_version}）', page)
        page = re.sub(r'China mirror \(Lite[^)]*\)', f'China mirror (Lite v{mirror_version})', page)
        page = re.sub(r'\s*<p class="release-(?:status|draft)">.*?</p>', '', page, flags=re.S)
        writes[path] = page

    for relative in ('README.md', 'README_EN.md'):
        path = root / relative
        text = path.read_text('utf-8')
        text = text.replace('## 多语言支持 — v0.6.0（待发布）', '## 多语言支持 — v0.6.0')
        text = text.replace('## Language Support — v0.6.0 (unreleased)', '## Language Support — v0.6.0')
        text = re.sub(r'^以下说明针对 v0\.6\.0 候选，.*$',
                      'VoxGo v0.6.0 支持下列语言与翻译方向。参见[更新日志](docs/releases/v0.6.0.md)；安装包见 [GitHub Releases](https://github.com/zxbb1190/VoxGo_game_voice_trans/releases/latest)。', text, flags=re.M)
        text = re.sub(r'^This describes the v0\.6\.0 candidate,.*$',
                      'VoxGo v0.6.0 supports the languages and directions below. See the [release notes](docs/releases/v0.6.0.md) and [GitHub Releases](https://github.com/zxbb1190/VoxGo_game_voice_trans/releases/latest) for packages.', text, flags=re.M)
        text = re.sub(r'^- .*v0\.5\.2.*v0\.6\.0.*\n', '', text, flags=re.M)
        text = text.replace('v0.6.0 候选', 'v0.6.0').replace('v0.6.0 待发布', 'v0.6.0').replace('the v0.6.0 candidate', 'v0.6.0').replace('v0.6.0 candidate', 'v0.6.0')
        text = text.replace('候选可选', '可选').replace('candidate codes', 'codes')
        writes[path] = text
    notes_path = root / f'docs/releases/{tag}.md'
    notes = notes_path.read_text('utf-8')
    notes = re.sub(r'^Unreleased multilingual Beta draft.*$',
                   f'Released {release["published_at"][:10]}. 日语、韩语、俄语为 Beta 实验性语言；Japanese, Korean and Russian are experimental Beta languages.', notes, flags=re.M)
    writes[notes_path] = notes
    for path, text in writes.items():
        path.write_text(text, encoding='utf-8', newline='\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('notes', 'site'))
    parser.add_argument('--version', required=True)
    parser.add_argument('--packages', type=Path, default=ROOT / 'release')
    parser.add_argument('--output', type=Path, default=ROOT / 'release-notes.md')
    parser.add_argument('--github-env', type=Path)
    parser.add_argument('--mirror-verified', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'\d+\.\d+\.\d+', args.version):
        parser.error('Version must be major.minor.patch')
    if args.action == 'notes':
        body, hashes = render_notes(ROOT, args.version, args.packages)
        args.output.write_text(body, encoding='utf-8', newline='\n')
        if args.github_env:
            with args.github_env.open('a', encoding='utf-8', newline='\n') as target:
                for edition, digest in hashes.items():
                    target.write(edition.upper().replace('-', '_') + '_SHA256=' + digest + '\n')
    else:
        release = github_json(f'/releases/tags/v{args.version}')
        hashes = {edition: os.environ.get(edition.upper().replace('-', '_') + '_SHA256', '') for edition in EDITIONS}
        sync_site(ROOT, args.version, release, hashes, args.mirror_verified)


if __name__ == '__main__':
    main()
