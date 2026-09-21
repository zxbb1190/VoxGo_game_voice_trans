"""Explicit reset of a selected, known Whisper cache; never a whole models root."""

from pathlib import Path
import os
import shutil
import stat


class ModelCacheResetError(RuntimeError):
    """A reset was unsafe or could not complete (possibly files still in use)."""


# Deliberately do not accept custom repository IDs or local model paths here.
# Keep this allowlist aligned with the faster-whisper models offered by VoxGo.
_MODEL_REPOS = {
    name: f"Systran/faster-whisper-{name}"
    for name in (
        "tiny", "tiny.en", "base", "base.en", "small", "small.en",
        "medium", "medium.en", "large-v1", "large-v2", "large-v3",
    )
}
_MODEL_REPOS.update({
    "large": "Systran/faster-whisper-large-v3",
    **{name: f"Systran/faster-{name.replace('distil-', 'distil-whisper-', 1)}"
       for name in ("distil-large-v2", "distil-medium.en", "distil-small.en", "distil-large-v3")},
    "distil-large-v3.5": "distil-whisper/distil-large-v3.5-ct2",
    "large-v3-turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
    "turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
})


def _reject_redirect(path: Path) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISLNK(info.st_mode) or (
        getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    ):
        raise ModelCacheResetError("Model cache contains a link or junction; automatic reset refused.")


def reset_model_cache(download_root, model_size: str) -> tuple[Path, ...]:
    """Delete only the selected official model's two provider cache directories.

    The caller must stop recognition/download tasks and release loaded models first.
    Missing caches are harmless. Custom/local models require manual management.
    All targets are checked before deletion; I/O failure may leave a partial reset,
    which is safe to retry after other VoxGo instances have been closed.
    """
    if not isinstance(model_size, str) or model_size not in _MODEL_REPOS:
        raise ModelCacheResetError("Only a supported built-in Whisper model can be reset automatically.")
    root = Path(os.path.abspath(os.fspath(download_root)))
    repo = _MODEL_REPOS[model_size]
    targets = (root / "modelscope" / repo, root / ("models--" + repo.replace("/", "--")))
    existing = []
    try:
        for parent in (*reversed(root.parents), root):
            _reject_redirect(parent)
        for target in targets:
            for parent in reversed(target.relative_to(root).parents):
                _reject_redirect(root / parent)
            _reject_redirect(target)
            if not target.exists():
                continue
            if not target.is_dir():
                raise ModelCacheResetError("Expected a model cache directory; automatic reset refused.")
            for directory, dirs, files in os.walk(target, followlinks=False):
                for name in dirs + files:
                    _reject_redirect(Path(directory) / name)
            existing.append(target)
        for target in existing:
            shutil.rmtree(target)
    except OSError as exc:
        raise ModelCacheResetError(
            "Model cache reset could not complete. Close other VoxGo instances and retry; "
            "check file permissions if the problem persists."
        ) from exc
    return tuple(existing)
