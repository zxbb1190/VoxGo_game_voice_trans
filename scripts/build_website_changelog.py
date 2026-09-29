"""Build static, SEO-visible changelog pages from published GitHub Releases.

Usage: python scripts/build_website_changelog.py [--tags v0.5.1 v0.5.0]
The GitHub Release body remains the content source. Generated HTML is checked
into docs/ so GitHub Pages and search crawlers need no runtime API request.
"""

from __future__ import annotations

import argparse
from datetime import date
import html
import json
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
API = "https://api.github.com/repos/zxbb1190/VoxGo_game_voice_trans"
SITE = "https://voxgo.cn"
TAG_PATTERN = re.compile(r"v\d+\.\d+\.\d+\Z")
HOME_START = "<!-- CHANGELOG_HOME_START -->"
HOME_END = "<!-- CHANGELOG_HOME_END -->"


def github_json(path: str) -> object:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "VoxGo-website-changelog"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    with urlopen(Request(API + path, headers=headers), timeout=30) as response:
        return json.load(response)


def release_notes(body: str) -> tuple[list[str], list[str]]:
    sections: dict[str, list[str]] = {"zh": [], "en": []}
    current = None
    for raw in body.splitlines():
        line = raw.strip()
        if line == "### 更新内容":
            current = "zh"
        elif line == "### What's new":
            current = "en"
        elif line.startswith("### "):
            current = None
        elif current and line.startswith("- "):
            sections[current].append(line[2:])
    if not sections["zh"] or not sections["en"]:
        raise ValueError("Release body must include ### 更新内容 and ### What's new bullet lists")
    return sections["zh"], sections["en"]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def page(title: str, description: str, canonical: str, body: str, article_date: str | None = None) -> str:
    schema = ""
    if article_date:
        data = {"@context": "https://schema.org", "@type": "Article", "headline": title,
                "datePublished": article_date, "mainEntityOfPage": canonical,
                "publisher": {"@type": "Organization", "name": "VoxGo"}}
        schema = '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace("<", "\\u003c") + "</script>"
    return f'''<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(title)}</title><meta name="description" content="{esc(description)}" />
<link rel="canonical" href="{esc(canonical)}" />
<meta property="og:title" content="{esc(title)}" /><meta property="og:description" content="{esc(description)}" />
<meta property="og:type" content="article" /><meta property="og:url" content="{esc(canonical)}" />
<meta property="og:image" content="{SITE}/assets/logo.png" />
<link rel="icon" href="/favicon.ico" /><link rel="stylesheet" href="/assets/css/changelog.css" />
{schema}</head><body>
<nav class="site-nav"><a class="brand" href="/"><img src="/assets/logo.png" alt="VoxGo Logo" />VoxGo</a><div><a href="/">官网</a><a href="/changelog/">更新日志</a><a href="/en/">English</a><a href="https://github.com/zxbb1190/VoxGo_game_voice_trans">GitHub</a></div></nav>
<main>{body}</main>
<footer>© VoxGo · <a href="/">返回官网</a> · <a href="https://github.com/zxbb1190/VoxGo_game_voice_trans/blob/main/LICENSE">GPLv3</a></footer>
</body></html>
'''


def version_page(release: dict) -> str:
    tag = release["tag_name"]
    version = tag[1:]
    date = release["published_at"][:10]
    zh, en = release_notes(release["body"])
    url = f"{SITE}/changelog/{tag}/"
    description = f"VoxGo {version} 更新日志：{zh[0]}"
    release_link = esc(release["html_url"])
    zh_list = "".join(f"<li>{esc(note)}</li>" for note in zh)
    en_list = "".join(f"<li>{esc(note)}</li>" for note in en)
    assets = [a for a in release.get("assets", []) if a["name"].endswith(".zip")]
    downloads = "".join(
        f'<li><a href="{esc(a["browser_download_url"])}">{esc(a["name"])}</a> <small>{a["size"] / 1048576:.1f} MiB</small></li>'
        for a in assets
    )
    content = f'''<div class="crumb"><a href="/">VoxGo</a> / <a href="/changelog/">更新日志</a> / {esc(tag)}</div>
<header class="release-hero"><span class="label">PATCH NOTES / {esc(tag)}</span><h1>VoxGo <strong>{esc(version)}</strong></h1><time datetime="{date}">{date}</time><p>本页内容由 <a href="{release_link}">GitHub Release</a> 生成。</p></header>
<section><h2>更新内容</h2><ol class="note-list">{zh_list}</ol></section>
<section lang="en"><h2>What's new</h2><ol class="note-list">{en_list}</ol></section>
<section><h2>下载 / Downloads</h2><ul class="download-list">{downloads}</ul><p>附件与 SHA256 校验信息请以 <a href="{release_link}">GitHub Release</a> 为准。</p></section>
<a class="back" href="/changelog/">← 全部更新日志</a>'''
    return page(f"VoxGo {version} 更新日志 / Patch Notes", description, url, content, date)


def index_page(releases: list[dict]) -> str:
    items = "".join(
        f'<article class="release-row"><span class="label">{esc(r["published_at"][:10])}</span>'
        f'<h2><a href="/changelog/{esc(r["tag_name"])}/">VoxGo {esc(r["tag_name"][1:])}</a></h2>'
        f'<p>{esc(release_notes(r["body"])[0][0])}</p><a href="/changelog/{esc(r["tag_name"])}/">阅读更新内容 →</a></article>'
        for r in releases
    )
    content = f'''<div class="crumb"><a href="/">VoxGo</a> / 更新日志</div><header class="release-hero"><span class="label">RELEASE HISTORY</span><h1>更新日志<br /><strong>PATCH NOTES</strong></h1><p>VoxGo 每个版本的改动，以及对应的正式发行版。</p></header><section class="release-list">{items}</section>'''
    return page("VoxGo 更新日志 / Patch Notes", "查看 VoxGo 游戏语音翻译工具的版本更新、发布日期与下载信息。", f"{SITE}/changelog/", content)


def home_block(releases: list[dict], language: str = "zh") -> str:
    latest = releases[0]
    zh, en = release_notes(latest["body"])
    date = latest["published_at"][:10]
    bullets = "".join(f"<li>{esc(note)}</li>" for note in (en if language == "en" else zh)[:5])
    history = "".join(
        f'<div class="patch-history"><a href="/changelog/{esc(r["tag_name"])}/">VoxGo {esc(r["tag_name"][1:])}</a>'
        f'<time datetime="{esc(r["published_at"][:10])}">{esc(r["published_at"][:10])}</time></div>'
        for r in releases[1:3]
    )
    return f'''<div class="patch-board"><div class="patch-version" aria-hidden="true">{esc(latest["tag_name"][1:])}</div><div class="patch-content"><span class="patch-date">{date} / LATEST RELEASE</span><h3><a href="/changelog/{esc(latest["tag_name"])}/">VoxGo {esc(latest["tag_name"][1:])}</a></h3><ul>{bullets}</ul></div></div>{history}'''


def write_sitemap(releases: list[dict]) -> None:
    build_date = date.today().isoformat()
    urls = [(f"{SITE}/", build_date),
            (f"{SITE}/en/", build_date),
            (f"{SITE}/changelog/", build_date)]
    urls.extend((f"{SITE}/changelog/{r['tag_name']}/", r["published_at"][:10]) for r in releases)
    entries = "".join(f"  <url><loc>{esc(url)}</loc><lastmod>{date}</lastmod></url>\n" for url, date in urls)
    (DOCS / "sitemap.xml").write_bytes((
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + entries + '</urlset>\n').encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tags", nargs="+", help="Published tags to render, newest first")
    args = parser.parse_args()
    if args.tags:
        releases = [github_json(f"/releases/tags/{tag}") for tag in args.tags]
    else:
        releases = []
        page_number = 1
        while True:
            batch = github_json(f"/releases?per_page=100&page={page_number}")
            releases.extend(batch)
            if len(batch) < 100:
                break
            page_number += 1
        releases = [r for r in releases if TAG_PATTERN.fullmatch(r["tag_name"]) and not r["draft"] and not r["prerelease"]]
    if not releases:
        raise ValueError("No published VoxGo releases found")
    for r in releases:
        if not TAG_PATTERN.fullmatch(r["tag_name"]) or r.get("draft") or r.get("prerelease"):
            raise ValueError(f"Not a published stable release: {r['tag_name']}")
        release_notes(r["body"])
    releases.sort(key=lambda r: tuple(map(int, r["tag_name"][1:].split("."))), reverse=True)
    changelog = DOCS / "changelog"
    changelog.mkdir(exist_ok=True)
    (changelog / "index.html").write_bytes(index_page(releases).encode("utf-8"))
    for r in releases:
        directory = changelog / r["tag_name"]
        directory.mkdir(exist_ok=True)
        (directory / "index.html").write_bytes(version_page(r).encode("utf-8"))
    home = DOCS / "index.html"
    source = home.read_bytes().decode("utf-8")
    if source.count(HOME_START) != 1 or source.count(HOME_END) != 1:
        raise ValueError("Home page changelog markers missing or duplicated")
    start = source.index(HOME_START) + len(HOME_START)
    end = source.index(HOME_END)
    newline = "\r\n" if "\r\n" in source else "\n"
    block = ("\n      " + home_block(releases) + "\n      ").replace("\n", newline)
    home.write_bytes((source[:start] + block + source[end:]).encode("utf-8"))
    english_home = DOCS / "en" / "index.html"
    english_source = english_home.read_bytes().decode("utf-8")
    if english_source.count(HOME_START) != 1 or english_source.count(HOME_END) != 1:
        raise ValueError("English home page changelog markers missing or duplicated")
    english_start = english_source.index(HOME_START) + len(HOME_START)
    english_end = english_source.index(HOME_END)
    english_newline = "\r\n" if "\r\n" in english_source else "\n"
    english_block = ("\n      " + home_block(releases, "en") + "\n      ").replace("\n", english_newline)
    english_home.write_bytes((english_source[:english_start] + english_block + english_source[english_end:]).encode("utf-8"))
    write_sitemap(releases)
    print("Generated static changelog for " + ", ".join(r["tag_name"] for r in releases))


if __name__ == "__main__":
    main()
