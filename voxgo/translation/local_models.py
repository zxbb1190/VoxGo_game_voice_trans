"""Explicit, pinned downloads for the bundled CPU translation model catalog.

OPUS-MT by Helsinki-NLP; CTranslate2 conversion by gaudi. Both upstream
model cards declare Apache-2.0. Model weights are downloaded only on request.
"""
import hashlib
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import urllib.request
import urllib.error
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelFile:
    name: str
    size: int
    sha256: str


@dataclass(frozen=True)
class ModelDirection:
    direction: str
    repository: str
    revision: str
    files: tuple


@dataclass(frozen=True)
class LocalModel:
    name: str
    directions: tuple
    license: str = "Apache-2.0"

    @property
    def size_bytes(self):
        return sum(f.size for d in self.directions for f in d.files)


DEFAULT_LOCAL_MODEL = "opus-mt-en-zh"
LOCAL_MODELS = {DEFAULT_LOCAL_MODEL: LocalModel("OPUS-MT English ↔ 中文 (CPU)", (
    ModelDirection('en-zh', 'gaudi/opus-mt-en-zh-ctranslate2', 'dcd22168f08b99dd34c62bc2195e31dc2f04e90b', (
        ModelFile('README.md', 6720, 'e26c20de87b00a2a1330f6736a59e0f2d8b4aae3109064da1b8433242f213679'),
        ModelFile('config.json', 215, 'ce02c0c0d02f285d2ff34c80b0867ccb5c4a3b250a275e6d1d2884f5499a6e46'),
        ModelFile('model.bin', 155502615, 'f24c2bb82368f7de0196882de1d8b644d2aa54ae2439c3142f263de8a64ea2a9'),
        ModelFile('shared_vocabulary.json', 1303887, '37314a6abb25ed8f8497498aeeb31fcea98de892bf00ff7c2e8c966b26fe0b82'),
        ModelFile('source.spm', 806435, '5775ddc9e3ff2fae91554da56468ad35ff56edaba870fea74447bc7234bfdaa8'),
        ModelFile('target.spm', 804600, '81dc94efa84e4025ef38d25d5d07429fe41e3eb29d44003f1db6fe98487b0052'),
    )),
    ModelDirection('zh-en', 'gaudi/opus-mt-zh-en-ctranslate2', '05d8fc158397bae0c65b8d46c858b6c18e094c12', (
        ModelFile('README.md', 6720, 'e1995ec81dac199158d5836224864b6e297ddd920bf611c9dc0d78bea197c0d4'),
        ModelFile('config.json', 215, 'ce02c0c0d02f285d2ff34c80b0867ccb5c4a3b250a275e6d1d2884f5499a6e46'),
        ModelFile('model.bin', 155502615, 'a188bc45bce24635a1eb0cc42ad0b43afdad806b86af9beb3065bba11f3b212c'),
        ModelFile('shared_vocabulary.json', 1303998, 'acbf13516c56af2bb78ebdb770c2e4648fd8232ddd17af75298119cbfa7ee33d'),
        ModelFile('source.spm', 804677, 'e27a3a1b539f4959ec72ea60e453f49156289f95d4e6000b29332efc45616203'),
        ModelFile('target.spm', 806530, '6a881f4717cd7265f53fea54fd3dc689c767c05338fac7a4590f3088cb2d7855'),
    )),
))}
_DOWNLOAD_LOCK = threading.Lock()

# hf-mirror.com proxies Hugging Face repositories and is generally reachable
# from mainland China.  Users can explicitly select the official endpoint.
MODEL_SOURCES = {
    "modelscope": "https://modelscope.cn/models/zxman5233/opus-mt-en-zh-ctranslate2",
    "hf_mirror_net": "https://hf-mirror.net",
    "hf_mirror": "https://hf-mirror.com",
    "huggingface": "https://huggingface.co",
}
DEFAULT_MODEL_SOURCE = "modelscope"


class _ModelRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Handle mirror 308 redirects while keeping the destination allow-listed."""
    def __init__(self, source):
        super().__init__()
        self.allowed = {urlparse(MODEL_SOURCES[source]).hostname}
        if source == "hf_mirror":
            self.allowed.add("huggingface.co")

    def _redirect(self, req, fp, headers):
        target = urljoin(req.full_url, headers["Location"])
        parsed = urlparse(target)
        if parsed.scheme != "https" or parsed.hostname not in self.allowed:
            raise ValueError("Offline model redirect target is not allow-listed")
        return self.parent.open(urllib.request.Request(target, headers=dict(req.headers)))

    def http_error_308(self, req, fp, code, msg, headers):
        return self._redirect(req, fp, headers)


def model_source_url(repository, revision, filename, source=DEFAULT_MODEL_SOURCE):
    """Build a pinned model URL from the allow-listed source catalog."""
    try:
        base = MODEL_SOURCES[source].rstrip("/")
    except KeyError:
        raise ValueError(f"Unknown model source: {source}")
    if any(".." in part or not part for part in (repository, revision, filename)):
        raise ValueError("Unsafe model path")
    if source == "modelscope":
        directions = {
            "gaudi/opus-mt-en-zh-ctranslate2": "en-zh",
            "gaudi/opus-mt-zh-en-ctranslate2": "zh-en",
        }
        if repository not in directions:
            raise ValueError("Unknown ModelScope model mapping")
        return f"{base}/resolve/master/{directions[repository]}/{filename}"
    return f"{base}/{repository}/resolve/{revision}/{filename}"


def default_model_root():
    base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]
    return base / ".translation-models"


def model_path(model_id=DEFAULT_LOCAL_MODEL, root=None):
    if model_id not in LOCAL_MODELS:
        raise ValueError("Unknown offline translation model")
    root = Path(root) if root is not None else default_model_root()
    path = root / model_id
    if path.is_symlink() or path.resolve().parent != root.resolve():
        raise ValueError("Unsafe offline model path")
    return path


def _valid_file(path, item):
    if path.is_symlink() or not path.is_file() or path.stat().st_size != item.size:
        return False
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == item.sha256


def _ready(path, model):
    for direction in model.directions:
        folder = path / direction.direction
        if folder.is_symlink():
            return False
        for item in direction.files:
            if not _valid_file(folder / item.name, item):
                return False
    return True


def model_files_present(model_id=DEFAULT_LOCAL_MODEL, root=None):
    """Cheap UI status only; the inference worker still verifies every checksum."""
    try:
        path = model_path(model_id, root)
        for direction in LOCAL_MODELS[model_id].directions:
            folder = path / direction.direction
            if folder.is_symlink():
                return False
            for item in direction.files:
                file = folder / item.name
                if file.is_symlink() or not file.is_file() or file.stat().st_size != item.size:
                    return False
        return True
    except (OSError, ValueError, KeyError):
        return False


def is_model_ready(model_id=DEFAULT_LOCAL_MODEL, root=None):
    """Check all pinned lengths and hashes; call from a worker, not the UI thread."""
    try:
        return _ready(model_path(model_id, root), LOCAL_MODELS[model_id])
    except (OSError, ValueError, KeyError):
        return False


def download_model(model_id=DEFAULT_LOCAL_MODEL, progress=None, root=None, source=None):
    """Blocking explicit download. progress(received, total); raises on failure.

    A complete verified directory is published with rename. Interrupted downloads
    never count as ready. Only catalog filenames are used, never server paths.
    """
    path = model_path(model_id, root)
    model = LOCAL_MODELS[model_id]
    with _DOWNLOAD_LOCK:
        if is_model_ready(model_id, root):
            if progress:
                progress(model.size_bytes, model.size_bytes)
            return path
        path.parent.mkdir(parents=True, exist_ok=True)
        if shutil.disk_usage(path.parent).free < model.size_bytes + 32 * 1024 * 1024:
            raise OSError("Not enough free disk space for offline translation models")
        staging = Path(tempfile.mkdtemp(prefix=".download-", dir=path.parent))
        received = 0
        try:
            if source:
                sources = [source]
            elif model_id == DEFAULT_LOCAL_MODEL:
                sources = ["modelscope", "hf_mirror_net", "hf_mirror", "huggingface"]
            else:
                # Test/custom catalogs may not have a ModelScope mapping.
                sources = ["hf_mirror"]
            errors = []
            for active_source in sources:
              try:
               for direction in model.directions:
                folder = staging / direction.direction
                folder.mkdir()
                for item in direction.files:
                    url = model_source_url(direction.repository, direction.revision, item.name, active_source)
                    request = urllib.request.Request(url, headers={"User-Agent": "VoxGo-offline-models"})
                    opener = urllib.request.build_opener(_ModelRedirectHandler(active_source))
                    with opener.open(request, timeout=60) as response, (folder / item.name).open("wb") as output:
                        if not response.geturl().startswith("https://"):
                            raise ValueError("Offline model download requires HTTPS")
                        count = 0
                        while True:
                            chunk = response.read(1024 * 1024)
                            if not chunk:
                                break
                            count += len(chunk)
                            if count > item.size:
                                raise ValueError("Offline model file exceeds expected size")
                            output.write(chunk)
                            received += len(chunk)
                            if progress:
                                progress(received, model.size_bytes)
                    if not _valid_file(folder / item.name, item):
                        raise ValueError(f"Offline model checksum mismatch: {item.name}")
               break
              except Exception as exc:
               errors.append(f"{active_source}: {exc}")
               for child in list(staging.iterdir()):
                   if child.is_dir(): shutil.rmtree(child)
               if active_source == sources[-1]:
                   if len(sources) == 1:
                       raise
                   raise RuntimeError("Model download failed; switch download source and retry. " + " | ".join(errors)) from exc
            if path.exists():
                # Only an incomplete, application-owned catalog directory is removed.
                if path.is_symlink():
                    raise ValueError("Unsafe offline model path")
                shutil.rmtree(path)
            os.replace(staging, path)
            return path
        finally:
            if staging.exists():
                shutil.rmtree(staging)
