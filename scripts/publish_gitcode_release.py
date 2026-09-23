"""Mirror an already-built Lite ZIP to the GitCode release for the same tag.

Requires GITCODE_TOKEN, a GitCode commit SHA for a release that does not yet
exist, and the exact ZIP published on GitHub. No third-party packages needed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen


API = "https://api.gitcode.com/api/v5/repos/zxbb1190/VoxGo/releases"
TAG_PATTERN = re.compile(r"v\d+\.\d+\.\d+\Z")


class PublishError(RuntimeError):
    """A safe, credential-free error message for the release operator."""


def _request(url: str, *, method: str = "GET", data=None, headers=None, timeout=30):
    request = Request(url, data=data, headers=headers or {}, method=method)
    try:
        return urlopen(request, timeout=timeout)
    except HTTPError as exc:
        # The API puts its access token in the URL. Never include exc or its URL.
        raise PublishError(f"GitCode {method} returned HTTP {exc.code}") from None
    except URLError:
        raise PublishError(f"GitCode {method} network request failed") from None


def _api_json(path: str, token: str, *, method="GET", payload=None, params=None):
    query = {"access_token": token, **(params or {})}
    url = f"{API}{path}?{urlencode(query)}"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    with _request(url, method=method, data=body, headers=headers) as response:
        if response.status not in (200, 201):
            raise PublishError(f"GitCode {method} returned HTTP {response.status}")
        try:
            value = json.load(response)
        except (ValueError, UnicodeError) as exc:
            raise PublishError("GitCode returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise PublishError("GitCode returned an unexpected JSON shape")
    return value


def _sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _remote_sha256(url: str):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "gitcode.com":
        raise PublishError("GitCode returned an unexpected download URL")
    digest = hashlib.sha256()
    size = 0
    with _request(url, timeout=300) as response:
        for chunk in iter(lambda: response.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _asset_url(release: dict, filename: str):
    for asset in release.get("assets", []):
        if isinstance(asset, dict) and asset.get("name") == filename:
            url = asset.get("browser_download_url")
            if not url:
                raise PublishError("GitCode release lists the Lite asset without a download URL")
            return url
    return None


def publish(*, tag: str, package: Path, notes: str, token: str,
            target_commitish: str | None, expected_sha256: str | None = None):
    if not TAG_PATTERN.fullmatch(tag):
        raise PublishError("Tag must look like v0.5.1")
    if not token:
        raise PublishError("GITCODE_TOKEN is required")
    if not package.is_file() or package.name != f"VoxGo-{tag}-lite.zip":
        raise PublishError(f"Expected the official VoxGo-{tag}-lite.zip file")
    if not notes.strip():
        raise PublishError("Release notes cannot be empty")

    size = package.stat().st_size
    local_digest = _sha256(package)
    if expected_sha256:
        if not re.fullmatch(r"[a-fA-F0-9]{64}", expected_sha256):
            raise PublishError("--sha256 must be a 64-character SHA256 digest")
        if local_digest != expected_sha256.lower():
            raise PublishError("Local ZIP does not match the expected GitHub SHA256")
    tag_path = f"/tags/{quote(tag, safe='')}"
    try:
        release = _api_json(tag_path, token)
    except PublishError as exc:
        if "HTTP 404" not in str(exc):
            raise
        if not target_commitish or not re.fullmatch(r"[a-fA-F0-9]{40}", target_commitish):
            raise PublishError(
                "GitCode release is absent; provide --target-commitish with the matching 40-character GitCode commit SHA"
            ) from None
        release = _api_json(
            "", token, method="POST",
            payload={
                "tag_name": tag,
                "name": f"VoxGo {tag}",
                "body": notes,
                "target_commitish": target_commitish,
                "release_status": "latest",
            },
        )
    if release.get("tag_name") != tag:
        raise PublishError("GitCode returned a release for the wrong tag")

    download_url = _asset_url(release, package.name)
    if not download_url:
        upload = _api_json(
            f"/{quote(tag, safe='')}/upload_url", token,
            params={"file_name": package.name},
        )
        upload_url = upload.get("url")
        parsed_upload = urlparse(upload_url or "")
        if parsed_upload.scheme != "https" or not parsed_upload.hostname:
            raise PublishError("GitCode returned an invalid upload URL")
        upload_headers = upload.get("headers")
        if not isinstance(upload_headers, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in upload_headers.items()
        ):
            raise PublishError("GitCode returned invalid upload headers")
        upload_headers["Content-Length"] = str(size)
        with package.open("rb") as source:
            with _request(upload_url, method="PUT", data=source,
                          headers=upload_headers, timeout=600) as response:
                if response.status not in (200, 201, 204):
                    raise PublishError(f"GitCode upload returned HTTP {response.status}")

        for attempt in range(12):
            release = _api_json(tag_path, token)
            download_url = _asset_url(release, package.name)
            if download_url:
                break
            if attempt < 11:
                time.sleep(5)
        if not download_url:
            raise PublishError("Upload finished but the asset is absent from the GitCode release")

    # Verify exactly the public URL that the website exposes, not merely an
    # alternate asset URL returned by the API.
    download_url = (
        f"https://gitcode.com/zxbb1190/VoxGo/releases/download/{tag}/{package.name}"
    )
    remote_digest, remote_size = _remote_sha256(download_url)
    if remote_size != size or remote_digest != local_digest:
        raise PublishError("GitCode attachment does not match the GitHub ZIP (size or SHA256 differs)")
    return download_url, local_digest, size


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="Release tag, for example v0.5.1")
    parser.add_argument("--zip", type=Path, required=True, help="Exact official GitHub Lite ZIP")
    parser.add_argument("--notes-file", type=Path, required=True, help="UTF-8 bilingual release notes")
    parser.add_argument("--target-commitish", help="GitCode commit SHA when creating a missing release")
    parser.add_argument("--sha256", help="Expected GitHub SHA256 of the Lite ZIP")
    args = parser.parse_args(argv)
    try:
        notes = args.notes_file.read_text(encoding="utf-8-sig")
        url, sha256, size = publish(
            tag=args.tag, package=args.zip, notes=notes,
            token=os.environ.get("GITCODE_TOKEN", ""),
            target_commitish=args.target_commitish,
            expected_sha256=args.sha256,
        )
    except (OSError, PublishError) as exc:
        print(f"GitCode release failed: {exc}", file=sys.stderr)
        return 1
    print(f"GitCode Lite: {url}")
    print(f"SHA256: {sha256} ({size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
