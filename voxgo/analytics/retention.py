"""Best-effort bounded cleanup of consent-scoped remote analytics files."""
from datetime import date, datetime, timedelta, timezone
import os
from pathlib import Path
import re
import stat
import uuid

MAX_FILES = 90
MAX_BYTES = 2 * 1024 * 1024
SCAN_LIMIT = 10000


def _uuid(value):
    try:
        return str(uuid.UUID(str(value))) == value
    except (ValueError, TypeError, AttributeError):
        return False


def cleanup_remote(root, current_epoch):
    """Keep the current consent epoch and seven UTC days of bounded shards.

    Never follows directory links. A single pass examines at most SCAN_LIMIT
    directory entries; oversized or concurrently modified trees converge over
    subsequent background passes. Identity, aggregation and lock files in the
    active epoch are outside the shards subtree and are left untouched.
    """
    root = Path(root)
    remaining = SCAN_LIMIT
    today = datetime.now(timezone.utc).date()
    cutoff = today - timedelta(days=6)
    keep = current_epoch if _uuid(current_epoch) else None

    def entries(directory):
        nonlocal remaining
        try:
            with os.scandir(directory) as scan:
                for entry in scan:
                    if remaining <= 0:
                        return
                    remaining -= 1
                    yield Path(entry.path)
        except OSError:
            return

    def mode(path):
        try:
            return path.lstat().st_mode
        except OSError:
            return 0

    def is_link(path):
        try:
            info = path.lstat()
            return (stat.S_ISLNK(info.st_mode) or bool(
                getattr(info, 'st_file_attributes', 0) &
                getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 1024)))
        except OSError:
            return False

    def unlink(path):
        try:
            path.unlink()
        except OSError:
            if is_link(path):
                try:
                    path.rmdir()
                except OSError:
                    pass

    def prune(path):
        try:
            path.rmdir()
        except OSError:
            pass

    def remove_tree(path):
        # Iterative traversal avoids recursion on malformed directories.
        stack = [(path, False)]
        while stack:
            node, visited = stack.pop()
            if visited:
                prune(node)
            elif stat.S_ISDIR(mode(node)) and not is_link(node):
                stack.append((node, True))
                stack.extend((child, False) for child in entries(node))
            else:
                unlink(node)

    try:
        if is_link(root) or not root.is_dir():
            return
        for epoch in entries(root):
            if not _uuid(epoch.name):
                continue
            if epoch.name != keep:
                remove_tree(epoch)
                continue
            if is_link(epoch) or not epoch.is_dir():
                continue
            shards = epoch / 'shards'
            if is_link(shards) or not shards.is_dir():
                continue
            files = []
            directories = []
            stack = [shards]
            while stack and remaining > 0:
                directory = stack.pop()
                directories.append(directory)
                for path in entries(directory):
                    info = path.lstat()
                    if is_link(path):
                        unlink(path)
                    elif stat.S_ISDIR(info.st_mode):
                        stack.append(path)
                    elif stat.S_ISREG(info.st_mode):
                        match = re.fullmatch(r'(\d{4}-\d{2}-\d{2})\.json(?:\.corrupt-\d+)?', path.name)
                        try:
                            day = (date.fromisoformat(match[1]) if match else
                                   datetime.fromtimestamp(info.st_mtime, timezone.utc).date())
                        except (ValueError, OverflowError, OSError):
                            unlink(path)
                            continue
                        if day < cutoff or day > today:
                            unlink(path)
                            continue
                        live = path.name.endswith('.json')
                        files.append(((live, day, info.st_mtime), path, info.st_size))
            used = count = 0
            for _, path, size in sorted(files, key=lambda row: row[0], reverse=True):
                if count >= MAX_FILES or used + size > MAX_BYTES:
                    unlink(path)
                else:
                    count += 1
                    used += size
            for directory in reversed(directories):
                prune(directory)
    except OSError:
        # Cleanup is never allowed to affect translation or shutdown.
        return
