"""Publication gates and local site synchronization; all inputs are fixtures."""
import json
from pathlib import Path
import re
import tempfile
import unittest

from scripts import build_localized_website as website
from scripts import build_website_changelog as changelog
from scripts import release_metadata as metadata

ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataTests(unittest.TestCase):
    def fixture(self, folder):
        root = Path(folder)
        for relative in ('docs/update.json', 'docs/index.html', 'docs/en/index.html',
                         'docs/sitemap.xml', 'docs/releases/v0.6.0.md', 'README.md', 'README_EN.md'):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / relative).read_bytes())
            if relative in ('docs/index.html', 'docs/en/index.html'):
                page = path.read_text('utf-8')
                page = re.sub(r'(gitcode\.com/zxbb1190/VoxGo/releases/download/)v\d+\.\d+\.\d+/VoxGo-v\d+\.\d+\.\d+', r'\g<1>v0.5.2/VoxGo-v0.5.2', page)
                page = re.sub(r'(China mirror \(Lite v)\d+\.\d+\.\d+', r'\g<1>0.5.2', page)
                page = re.sub(r'(国内镜像下载（Lite v)\d+\.\d+\.\d+', r'\g<1>0.5.2', page)
                path.write_text(page, encoding='utf-8')
        packages = root / 'release'
        packages.mkdir()
        for edition in metadata.EDITIONS:
            (packages / metadata.package_name('0.6.0', edition)).write_bytes(edition.encode())
        notes, hashes = metadata.render_notes(root, '0.6.0', packages)
        release = {'tag_name': 'v0.6.0', 'published_at': '2026-10-30T04:00:00Z',
                   'draft': False, 'prerelease': False, 'body': notes, 'assets': []}
        for edition in metadata.EDITIONS:
            name = metadata.package_name('0.6.0', edition)
            release['assets'].append({'name': name, 'state': 'uploaded', 'size': len(edition),
                                     'digest': 'sha256:' + hashes[edition],
                                     'browser_download_url': metadata.REPO + '/releases/download/v0.6.0/' + name})
        return root, notes, hashes, release

    def test_notes_keep_bilingual_features_beta_limits_and_all_artifact_hashes(self):
        with tempfile.TemporaryDirectory() as folder:
            root, notes, hashes, release = self.fixture(folder)
            zh, en = changelog.release_notes(notes)
            self.assertGreaterEqual(len(zh), 10)
            self.assertEqual(len(zh), len(en))
            self.assertIn('### Known limitations (Beta)', notes)
            self.assertIn('统一跟随原有隐私开关', notes)
            self.assertNotIn('Unreleased', notes)
            self.assertNotIn('git push', notes)
            for edition, digest in hashes.items():
                self.assertIn(metadata.package_name('0.6.0', edition), notes)
                self.assertIn(digest, notes)

    def test_reject_missing_wrong_or_unpublished_assets_before_writing(self):
        for scenario in ('missing', 'digest', 'url', 'draft', 'tag'):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as folder:
                root, _, hashes, release = self.fixture(folder)
                before = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
                if scenario == 'missing': release['assets'].pop()
                if scenario == 'digest': release['assets'][0]['digest'] = 'sha256:' + '0' * 64
                if scenario == 'url': release['assets'][0]['browser_download_url'] = 'https://example.com/wrong.zip'
                if scenario == 'draft': release['draft'] = True
                if scenario == 'tag': release['tag_name'] = 'v0.5.2'
                with self.assertRaises(ValueError): metadata.sync_site(root, '0.6.0', release, hashes)
                self.assertEqual(before, {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_published_site_keeps_old_mirror_until_verified(self):
        with tempfile.TemporaryDirectory() as folder:
            root, _, hashes, release = self.fixture(folder)
            metadata.sync_site(root, '0.6.0', release, hashes)
            result = json.loads((root / 'docs/update.json').read_text('utf-8'))
            self.assertEqual(result['latest'], '0.6.0')
            self.assertEqual(result['sha256_full'], hashes['full'])
            self.assertIn('Beta', '\n'.join(result['notes_en']))
            for relative in ('docs/index.html', 'docs/en/index.html'):
                page = (root / relative).read_text('utf-8')
                self.assertNotIn('<p class="release-status">', page)
                self.assertNotIn('<p class="release-draft">', page)
                self.assertIn('gitcode.com/zxbb1190/VoxGo/releases/download/v0.5.2/', page)
                self.assertIn(metadata.REPO + '/releases/download/v0.6.0/', page)
            for relative in ('README.md', 'README_EN.md'):
                readme = (root / relative).read_text('utf-8')
                self.assertIn('hub.xerj.org/contributors/zxbb1190', readme)
                self.assertNotIn('v0.6.0 candidate', readme)
                self.assertNotIn('v0.6.0 候选', readme)

    def test_verified_mirror_and_real_notes_generate_all_three_locales(self):
        with tempfile.TemporaryDirectory() as folder:
            root, _, hashes, release = self.fixture(folder)
            metadata.sync_site(root, '0.6.0', release, hashes, mirror_verified=True)
            for locale, relative in (('zh', 'docs/index.html'), ('en', 'docs/en/index.html')):
                path = root / relative
                page = path.read_text('utf-8')
                start = page.index(changelog.HOME_START) + len(changelog.HOME_START)
                end = page.index(changelog.HOME_END)
                path.write_text(page[:start] + '\n' + changelog.home_block([release], locale) + '\n' + page[end:], 'utf-8')
            website.build(root=root)
            self.assertEqual(website.build(root=root, check=True), [])
            for locale in website.GENERATED:
                page = (root / f'docs/{locale}/index.html').read_text('utf-8')
                self.assertIn('gitcode.com/zxbb1190/VoxGo/releases/download/v0.6.0/', page)
                self.assertNotIn('class="release-draft"', page)
                self.assertIn('/changelog/v0.6.0/', page)


if __name__ == '__main__':
    unittest.main()
