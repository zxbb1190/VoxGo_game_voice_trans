"""Build static JA/KO/RU homepages from the English page, without network calls.

ZH/EN remain edited pages. Shared navigation/SEO and strict source-key catalogs
keep the three generated pages in sync. --check never writes files.
"""
from __future__ import annotations

import argparse
from datetime import date
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from string import Formatter
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://voxgo.cn'
CATALOG = ROOT / 'scripts/website_locales/messages.json'
META_PATH = ROOT / 'scripts/website_locales/metadata.json'
HOME_PATHS = {'zh-CN': '/', 'en': '/en/', 'ja': '/ja/', 'ko': '/ko/', 'ru': '/ru/'}
AUTONYMS = {'zh-CN': '简体中文', 'en': 'English', 'ja': '日本語', 'ko': '한국어', 'ru': 'Русский'}
GENERATED = ('ja', 'ko', 'ru')
SHARED_TEXT = {'VoxGo', 'GitHub', 'Discord', 'KOOK', 'API', 'ASR', 'Whisper', 'WHISPER ASR',
               'VoxGo Lite', 'Full', 'Full-CUDA / GPU', 'Beta'}
EXAMPLE_CLASSES = {'original', 'translated', 'phone-card', 'story-example', 'scene-transcript',
                   'scene-subtitle', 'experience-overlay', 'hero-languages', 'site-language-switcher'}
VOID_TAGS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
TOKEN = re.compile(r'\b(?:v?\d+\.\d+\.\d+|\d{4}-\d{2}-\d{2})\b')


def message_template(text):
    values = list(dict.fromkeys(TOKEN.findall(text)))
    template = text
    for i, value in enumerate(values):
        template = template.replace(value, '{' + str(i) + '}')
    return template, values


def load_messages(path=CATALOG):
    messages = {}
    for source, *translations in json.loads(Path(path).read_text('utf-8')):
        if len(translations) != 3 or not all(translations):
            raise ValueError('JA/KO/RU translations required: ' + source)
        key, values = message_template(source)
        if key in messages:
            raise ValueError('Duplicate message: ' + key)
        rendered = []
        for translation in translations:
            for i, value in enumerate(values):
                translation = translation.replace(value, '{' + str(i) + '}')
            fields = {field for _, field, _, _ in Formatter().parse(translation) if field is not None}
            if fields != {str(i) for i in range(len(values))}:
                raise ValueError('Version/date fields differ: ' + source)
            rendered.append(translation)
        messages[key] = rendered
    return messages


def translate(text, locale, messages):
    normalized = ' '.join(text.split())
    if not normalized:
        return text
    if normalized in SHARED_TEXT or re.fullmatch(r'(?:VOXGO|VoxGo) v?\d+\.\d+\.\d+', normalized):
        return text
    if not re.search(r'[A-Za-z]', normalized):
        return text
    key, values = message_template(normalized)
    if key not in messages:
        raise ValueError(f'Missing {locale} website translation: {normalized}')
    result = messages[key][GENERATED.index(locale)].format(*values)
    leading = text[:len(text)-len(text.lstrip())]
    trailing = text[len(text.rstrip()):]
    return leading + result + trailing


class LocalizedPage(HTMLParser):
    def __init__(self, locale, messages):
        super().__init__(convert_charrefs=True)
        self.locale, self.messages = locale, messages
        self.parts, self.stack = [], []

    def skipped(self):
        return any(tag in {'head', 'script', 'style'} or set(attrs.get('class', '').split()) & EXAMPLE_CLASSES
                   for tag, attrs in self.stack)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        in_skip = self.skipped() or 'site-language-switcher' in attributes.get('class', '').split()
        if not in_skip:
            for key in ('alt', 'title', 'aria-label'):
                if attributes.get(key):
                    attributes[key] = translate(attributes[key], self.locale, self.messages)
        if attributes == dict(attrs):
            self.parts.append(self.get_starttag_text())
        else:
            self.parts.append('<' + tag + ''.join(' ' + key + ('="' + html.escape(value, quote=True) + '"' if value is not None else '')
                                                for key, value in attributes.items())
                              + (' />' if self.get_starttag_text().endswith('/>') else '>'))
        if tag not in VOID_TAGS:
            self.stack.append((tag, attributes))

    def handle_startendtag(self, tag, attrs):
        depth = len(self.stack)
        self.handle_starttag(tag, attrs)
        self.stack = self.stack[:depth]

    def handle_endtag(self, tag):
        self.parts.append('</' + tag + '>')
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                self.stack = self.stack[:i]
                break

    def handle_data(self, data):
        if any(tag in {'script', 'style'} for tag, _ in self.stack):
            self.parts.append(data)
        else:
            self.parts.append(html.escape(data if self.skipped() else translate(data, self.locale, self.messages), quote=False))

    def handle_comment(self, data):
        self.parts.append('<!--' + data + '-->')

    def handle_decl(self, decl):
        self.parts.append('<!' + decl + '>')


def language_menu(locale, metadata):
    links = ''.join(f'<a href="{path}" lang="{code}" hreflang="{code}"'
                    + (' aria-current="page"' if code == locale else '')
                    + f'>{AUTONYMS[code]}</a>' for code, path in HOME_PATHS.items())
    return ('<details class="site-language-switcher"><summary aria-label="' + html.escape(metadata['language_label'])
            + '"><span aria-hidden="true">◎</span> ' + AUTONYMS[locale]
            + '</summary><div class="site-language-menu">' + links + '</div></details>')


def configure_page(source, locale, metadata):
    source = re.sub(r'<html lang="[^"]+">', f'<html lang="{locale}">', source, count=1)
    for pattern, replacement in (
        (r'<title>.*?</title>', '<title>' + html.escape(metadata['title']) + '</title>'),
        (r'<meta name="description"\s+content="[^"]*"\s*/?>', '<meta name="description" content="' + html.escape(metadata['description'], quote=True) + '" />'),
        (r'<meta name="keywords"\s+content="[^"]*"\s*/?>', '<meta name="keywords" content="' + html.escape(metadata['keywords'], quote=True) + '" />'),
        (r'<link rel="canonical" href="[^"]+"\s*/?>', '<link rel="canonical" href="' + SITE + HOME_PATHS[locale] + '" />'),
        (r'<meta property="og:title" content="[^"]*"\s*/?>', '<meta property="og:title" content="' + html.escape(metadata['title'], quote=True) + '" />'),
        (r'<meta property="og:description"\s+content="[^"]*"\s*/?>', '<meta property="og:description" content="' + html.escape(metadata['description'], quote=True) + '" />'),
        (r'<meta property="og:url" content="[^"]*"\s*/?>', '<meta property="og:url" content="' + SITE + HOME_PATHS[locale] + '" />'),
    ):
        source, count = re.subn(pattern, lambda _: replacement, source, flags=re.S)
        if count != 1:
            raise ValueError(f'Expected one SEO tag ({count}): {pattern}')
    source = re.sub(r'\s*<link rel="alternate" hreflang="[^"]+" href="[^"]+"\s*/?>', '', source)
    alternates = '\n'.join(f'  <link rel="alternate" hreflang="{code}" href="{SITE}{path}" />' for code, path in HOME_PATHS.items())
    alternates += f'\n  <link rel="alternate" hreflang="x-default" href="{SITE}/" />'
    source = re.sub(r'(<link rel="canonical"[^>]+>)', lambda m: m[0] + '\n' + alternates, source, count=1)
    source = re.sub(r'\s*<!-- SITE_I18N_SEO_START -->.*?<!-- SITE_I18N_SEO_END -->', '', source, flags=re.S)
    social = '\n  <!-- SITE_I18N_SEO_START -->\n'
    social += f'  <meta property="og:locale" content="{metadata["og_locale"]}" />\n'
    for code, item in load_metadata().items():
        if code != locale:
            social += f'  <meta property="og:locale:alternate" content="{item["og_locale"]}" />\n'
    social += '  <meta name="twitter:card" content="summary" />\n'
    social += '  <meta name="twitter:title" content="' + html.escape(metadata['title'], quote=True) + '" />\n'
    social += '  <meta name="twitter:description" content="' + html.escape(metadata['description'], quote=True) + '" />\n'
    social += '  <meta name="twitter:image" content="https://voxgo.cn/assets/logo.png" />\n  <!-- SITE_I18N_SEO_END -->'
    source = re.sub(r'(<meta property="og:image"[^>]+>)', lambda m: m[0] + social, source, count=1)
    source = re.sub(r'\n[ \t]*<details class="site-language-switcher">.*?</details>', '', source, flags=re.S)
    # Remove the old single-language link; the new menu sits outside nav overflow.
    source = re.sub(r'<a\s+href="(?:/|/en/)"\s*>(?:中文|English)</a>', '', source)
    marker = '</div>\n    </div>\n  </nav>'
    if marker not in source:
        raise ValueError('Navigation insertion point missing')
    source = source.replace(marker, '</div>\n      ' + language_menu(locale, metadata) + '\n    </div>\n  </nav>', 1)
    return source


def load_metadata():
    return json.loads(META_PATH.read_text('utf-8'))


def build_pages(root=ROOT):
    metadata, messages = load_metadata(), load_messages()
    pages = {}
    for locale in ('zh-CN', 'en'):
        rel = 'docs/index.html' if locale == 'zh-CN' else 'docs/en/index.html'
        pages[rel] = configure_page((root / rel).read_text('utf-8-sig'), locale, metadata[locale])
    for locale in GENERATED:
        parser = LocalizedPage(locale, messages)
        parser.feed(pages['docs/en/index.html'])
        content = configure_page(''.join(parser.parts), locale, metadata[locale])
        pages[f'docs/{locale}/index.html'] = content.replace('<!doctype html>', '<!doctype html>\n<!-- Generated by scripts/build_localized_website.py; edit the English page and website_locales catalogs. -->', 1)
    return pages


def sitemap_with_languages(source, lastmod=None):
    namespace = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    tree = ET.fromstring(source)
    existing = {node.findtext('s:loc', namespaces={'s': namespace}): node for node in tree}
    rows = []
    for path in HOME_PATHS.values():
        url = SITE + path
        previous = existing.get(url)
        old_date = previous.findtext('s:lastmod', namespaces={'s': namespace}) if previous is not None else None
        stamp = lastmod or old_date or date.today().isoformat()
        rows.append(f'  <url><loc>{url}</loc><lastmod>{stamp}</lastmod></url>')
    for node in tree:
        url = node.findtext('s:loc', namespaces={'s': namespace})
        if url not in {SITE + path for path in HOME_PATHS.values()}:
            stamp = node.findtext('s:lastmod', namespaces={'s': namespace})
            rows.append(f'  <url><loc>{html.escape(url)}</loc>' + (f'<lastmod>{stamp}</lastmod>' if stamp else '') + '</url>')
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="' + namespace + '">\n' + '\n'.join(rows) + '\n</urlset>\n'


def build(root=ROOT, check=False, lastmod=None):
    pages = build_pages(root)
    pages['docs/sitemap.xml'] = sitemap_with_languages((root / 'docs/sitemap.xml').read_text('utf-8'), lastmod)
    changed = []
    for rel, content in pages.items():
        path = root / rel
        if not path.exists() or path.read_text('utf-8-sig') != content:
            changed.append(rel)
    if check and changed:
        raise ValueError('Website regeneration required: ' + ', '.join(changed))
    if not check:
        for rel in changed:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(pages[rel], encoding='utf-8', newline='\n')
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true')
    group.add_argument('--write', action='store_true')
    parser.add_argument('--lastmod', help='ISO date for changed homepage content; never alters release dates')
    args = parser.parse_args()
    if args.lastmod:
        date.fromisoformat(args.lastmod)
    changed = build(check=args.check, lastmod=args.lastmod)
    print('Five-language website: ' + ('verified' if args.check else f'updated {len(changed)} files'))


if __name__ == '__main__':
    main()
