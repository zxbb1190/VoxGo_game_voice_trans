"""Static-site localization, release synchronization and SEO contracts; offline."""
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from scripts import build_localized_website as website
from scripts import build_website_changelog as changelog

ROOT = Path(__file__).resolve().parents[1]


class Tags(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.tags = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def select(self, tag, **attrs):
        return [values for name, values in self.tags if name == tag and all(values.get(k) == v for k, v in attrs.items())]


class WebsiteLocalizationTests(unittest.TestCase):
    def make_root(self, folder):
        root = Path(folder)
        for rel in ('docs/index.html', 'docs/en/index.html', 'docs/sitemap.xml'):
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((ROOT / rel).read_text('utf-8'), encoding='utf-8')
        return root

    def test_committed_generated_pages_are_current_without_writing(self):
        self.assertEqual(website.build(root=ROOT, check=True), [])

    def test_five_pages_have_self_canonical_and_identical_reciprocal_hreflang(self):
        expected = {**{code: website.SITE + path for code, path in website.HOME_PATHS.items()}, 'x-default': website.SITE + '/'}
        descriptions, titles = set(), set()
        for locale, path in website.HOME_PATHS.items():
            source = (ROOT / 'docs' / path.lstrip('/') / 'index.html').read_text('utf-8')
            tags = Tags(source)
            self.assertEqual(tags.select('html')[0]['lang'], locale)
            self.assertEqual(tags.select('link', rel='canonical'), [{'rel': 'canonical', 'href': website.SITE + path}])
            self.assertEqual({item['hreflang']: item['href'] for item in tags.select('link', rel='alternate')}, expected)
            self.assertEqual(tags.select('meta', property='og:url')[0]['content'], website.SITE + path)
            description = tags.select('meta', name='description')[0]['content']
            self.assertEqual(description, tags.select('meta', property='og:description')[0]['content'])
            self.assertEqual(description, tags.select('meta', name='twitter:description')[0]['content'])
            self.assertIn('Beta', description)
            self.assertLessEqual(len(tags.select('meta', name='keywords')[0]['content'].split(',')), 12)
            self.assertEqual(len(tags.select('meta', property='og:locale:alternate')), 4)
            descriptions.add(description)
            titles.add(tags.select('meta', property='og:title')[0]['content'])
            current = tags.select('a', **{'aria-current': 'page'})
            self.assertEqual(len(current), 1)
            self.assertEqual(current[0]['href'], path)
            self.assertEqual({item['hreflang'] for item in tags.select('a') if 'hreflang' in item}, set(website.HOME_PATHS))
        self.assertEqual(len(descriptions), 5)
        self.assertEqual(len(titles), 5)

    def test_generation_is_idempotent_and_preserves_published_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            website.build(root)
            self.assertEqual(website.build(root, check=True), [])
            english = Tags((root / 'docs/en/index.html').read_text('utf-8'))
            urls = [a['href'] for a in english.select('a') if '/releases/' in a.get('href', '')]
            for locale in website.GENERATED:
                tags = Tags((root / f'docs/{locale}/index.html').read_text('utf-8'))
                self.assertEqual([a['href'] for a in tags.select('a') if '/releases/' in a.get('href', '')], urls)

    def test_mirror_version_does_not_advance_with_github_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            path = root / 'docs/en/index.html'
            source = re.sub(
                r'(github\.com/zxbb1190/VoxGo_game_voice_trans/releases/download/)v\d+\.\d+\.\d+/VoxGo-v\d+\.\d+\.\d+',
                r'\g<1>v0.6.1/VoxGo-v0.6.1', path.read_text('utf-8'))
            source = re.sub(
                r'(gitcode\.com/zxbb1190/VoxGo/releases/download/)v\d+\.\d+\.\d+/VoxGo-v\d+\.\d+\.\d+',
                r'\g<1>v0.5.2/VoxGo-v0.5.2', source)
            source = re.sub(r'(China mirror \(Lite v)\d+\.\d+\.\d+', r'\g<1>0.5.2', source)
            path.write_text(source, encoding='utf-8')
            website.build(root)
            messages = website.load_messages()
            for locale in website.GENERATED:
                localized = (root / f'docs/{locale}/index.html').read_text('utf-8')
                self.assertIn('github.com/zxbb1190/VoxGo_game_voice_trans/releases/download/v0.6.1/', localized)
                self.assertIn('gitcode.com/zxbb1190/VoxGo/releases/download/v0.5.2/', localized)
                self.assertIn(website.translate('China mirror (Lite v0.5.2)', locale, messages), localized)
                self.assertNotIn('gitcode.com/zxbb1190/VoxGo/releases/download/v0.6.1/', localized)

    def test_dynamic_version_and_release_date_are_not_hardcoded(self):
        messages = website.load_messages()
        for locale in website.GENERATED:
            self.assertIn('v0.6.1', website.translate('China mirror (Lite v0.6.1)', locale, messages))
            self.assertIn('2026-11-01', website.translate('2026-11-01 / LATEST RELEASE', locale, messages))
            text = website.translate('Public downloads remain v0.6.0 until v0.6.1 is released.', locale, messages)
            self.assertIn('v0.6.0', text)
            self.assertIn('v0.6.1', text)

    def test_missing_translation_fails_before_any_page_is_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            english = root / 'docs/en/index.html'
            english.write_text(english.read_text('utf-8').replace('Start with Lite.', 'A brand new untranslated sentence.'), encoding='utf-8')
            before = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            with self.assertRaisesRegex(ValueError, 'Missing ja website translation'):
                website.build(root)
            self.assertEqual(before, {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_catalog_rejects_missing_locale_and_lost_version_fields(self):
        for data in ([['Version v0.6.0', 'バージョンv0.6.0', '버전 v0.6.0']],
                     [['Version v0.6.0', 'バージョン', '버전 v0.6.0', 'Версия v0.6.0']]):
            with self.subTest(data=data), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'messages.json'
                path.write_text(json.dumps(data), encoding='utf-8')
                with self.assertRaises(ValueError):
                    website.load_messages(path)

    def test_illustrative_subtitle_pairs_and_localized_image_alts_are_preserved(self):
        for locale in website.GENERATED:
            source = (ROOT / f'docs/{locale}/index.html').read_text('utf-8')
            self.assertIn('He is one shot behind the box.', source)
            self.assertIn('他在箱子后面，大残。', source)
            self.assertNotIn('alt="VoxGo Logo"', source)
            self.assertNotIn("Your game shouldn't stop at a language barrier.", source)
            self.assertIn('397760e037f20a1dcf00fef3c18818bb', source)
            self.assertIn('/assets/js/scroll-story.js', source)

    def test_sitemap_and_changelog_generator_keep_all_five_homepages(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            releases = [{'tag_name': 'v0.5.2', 'published_at': '2026-10-06T00:00:00Z'}]
            with patch.object(changelog, 'DOCS', docs):
                changelog.write_sitemap(releases)
            sitemap = (docs / 'sitemap.xml').read_text('utf-8')
            self.assertEqual(website.sitemap_with_languages(sitemap), sitemap)
            ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            urls = {e.text for e in ET.fromstring(sitemap).findall('s:url/s:loc', ns)}
            self.assertTrue({website.SITE + path for path in website.HOME_PATHS.values()} <= urls)
            self.assertNotIn('https://voxgo.cn/changelog/v0.6.0/', urls)
            self.assertIn('<lastmod>2026-10-06</lastmod>', sitemap)

    def test_future_release_workflow_generates_and_stages_localized_pages(self):
        workflow = (ROOT / '.github/workflows/publish-release.yml').read_text('utf-8')
        self.assertLess(workflow.index('python scripts/build_localized_website.py --write'),
                        workflow.index('git add $manifestPath'))
        self.assertIn('python scripts/build_localized_website.py --check', workflow)
        for locale in website.GENERATED:
            self.assertIn(f'docs/{locale}/index.html', workflow)


if __name__ == '__main__':
    unittest.main()
