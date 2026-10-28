"""Chinese recognition display only; never normalize ASR or translation input."""
from functools import lru_cache
import threading

_lock = threading.RLock()
_warned = False


@lru_cache(maxsize=1)
def _converter():
    from voxgo.ui._opencc import OpenCC
    return OpenCC('t2s')


@lru_cache(maxsize=256)
def _simplified(text):
    with _lock:
        return _converter().convert(text)


def recognition_display_text(text: str, source_language: str) -> str:
    # Use the event's source language, not the later mutable UI selection.
    if source_language != 'zh' or not text:
        return text
    try:
        return _simplified(text)
    except Exception as exc:
        # A missing/damaged display resource must not prevent translation.
        global _warned
        with _lock:
            if not _warned:
                from loguru import logger
                logger.warning('Chinese source display conversion unavailable: {}', type(exc).__name__)
                _warned = True
        return text
