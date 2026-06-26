"""Windows scheduling helpers for game-friendly runtime behavior."""

import ctypes
import os
import threading

from loguru import logger


BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
THREAD_PRIORITY_BELOW_NORMAL = -1
THREAD_PRIORITY_LOWEST = -2


def apply_game_friendly_process_priority() -> bool:
    if os.name != "nt":
        return False
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.GetCurrentProcess()
        if not kernel32.SetPriorityClass(handle, BELOW_NORMAL_PRIORITY_CLASS):
            raise ctypes.WinError(ctypes.get_last_error())
        logger.info("process priority set to BELOW_NORMAL for game-friendly scheduling")
        return True
    except Exception as exc:
        logger.debug("failed to set process priority: {}", exc)
        return False


def apply_game_friendly_thread_priority(name: str = "", lowest: bool = False) -> bool:
    if os.name != "nt":
        return False
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.GetCurrentThread()
        priority = THREAD_PRIORITY_LOWEST if lowest else THREAD_PRIORITY_BELOW_NORMAL
        if not kernel32.SetThreadPriority(handle, priority):
            raise ctypes.WinError(ctypes.get_last_error())
        logger.debug(
            "thread priority lowered: thread={}, priority={}",
            name or threading.current_thread().name,
            priority,
        )
        return True
    except Exception as exc:
        logger.debug("failed to set thread priority: {}", exc)
        return False
