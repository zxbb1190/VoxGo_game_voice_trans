"""Best-effort local storage for daily analytics snapshots."""
from __future__ import annotations
import hashlib
import json, os, time
import threading
from datetime import date, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile

class DailySnapshotStore:
    """Atomic, bounded snapshot files; failures never escape the analytics boundary."""
    def __init__(self, root: Path, retention_days: int = 30, max_files: int = 90,
                 max_bytes: int = 2 * 1024 * 1024, today=date.today):
        self.root = Path(root)
        self.retention_days = max(1, int(retention_days))
        self.max_files = max(1, int(max_files))
        self.max_bytes = max(1, int(max_bytes))
        self.today = today
        self.lock = threading.RLock()
        self.cleanup()

    def path_for(self, day: str) -> Path:
        if not __import__('re').fullmatch(r"\d{4}-\d{2}-\d{2}", day):
            raise ValueError("invalid snapshot date")
        date.fromisoformat(day)
        return self.root / f"{day}.json"

    def load(self, day: str) -> dict:
        with self.lock:
            return self._load(day)

    def _load(self, day: str) -> dict:
        path = self.path_for(day)
        try:
            if path.is_symlink():
                return {}
            if path.exists() and path.stat().st_size > 32768:
                raise ValueError("snapshot too large")
            data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            if not isinstance(data, dict):
                raise ValueError("invalid snapshot")
            return data
        except Exception:
            if path.exists():
                try: path.rename(path.with_suffix(path.suffix + f".corrupt-{time.time_ns()}"))
                except OSError: pass
            self.cleanup()
            return {}

    def save(self, day: str, snapshot: dict) -> bool:
        with self.lock:
            return self._save(day, snapshot)

    def _save(self, day: str, snapshot: dict) -> bool:
        try:
            current = self.today()
            if not current - timedelta(days=self.retention_days - 1) <= date.fromisoformat(day) <= current:
                return False
            payload = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, allow_nan=False)
            if len(payload.encode('utf-8')) > min(32768, self.max_bytes):
                return False
            target = self.path_for(day); target.parent.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile("w", encoding="utf-8", dir=target.parent, prefix=".snapshot-", delete=False) as f:
                temp = Path(f.name)
                f.write(payload); f.flush(); os.fsync(f.fileno())
            os.replace(temp, target); self.cleanup(); return target.exists()
        except Exception:
            try:
                if 'temp' in locals(): temp.unlink(missing_ok=True)
            except OSError: pass
            return False

    @staticmethod
    def revision(snapshot):
        payload = json.dumps(snapshot, sort_keys=True, allow_nan=False).encode('utf-8')
        return hashlib.sha256(payload).hexdigest()

    def mark_uploaded(self, day: str, uploaded_revision: str) -> bool:
        # Acknowledging yesterday's old revision must not erase newer counters.
        with self.lock:
            try:
                if date.fromisoformat(day) >= self.today():
                    return False
                snapshot = self.load(day)
                if not snapshot or self.revision(snapshot) != uploaded_revision:
                    return False
                self.path_for(day).unlink(missing_ok=True)
                self.cleanup()
                return True
            except (OSError, ValueError, TypeError):
                return False

    def cleanup(self, now: date | None = None) -> None:
        with self.lock:
            self._cleanup(now)

    def _cleanup(self, now=None):
        try:
            now = now or self.today()
            cutoff = now - timedelta(days=self.retention_days - 1)
            files = []
            for path in self.root.iterdir():
                if not path.is_file() or path.is_symlink():
                    continue
                import re
                match = re.fullmatch(r'(\d{4}-\d{2}-\d{2})\.json(?:\.corrupt-\d+)?', path.name)
                if not match and not path.name.startswith('.snapshot-'):
                    continue
                try:
                    stat = path.stat()
                    d = date.fromisoformat(match[1]) if match else date.fromtimestamp(stat.st_mtime)
                    if d < cutoff or d > now or (not match and d < now):
                        path.unlink()
                        continue
                    live = path.name.endswith('.json')
                    files.append(((live and d == now, live, stat.st_mtime), path, stat.st_size))
                except (ValueError, OSError):
                    continue
            used = 0
            for index, (_, path, size) in enumerate(sorted(files, reverse=True)):
                if index >= self.max_files or used + size > self.max_bytes:
                    try: path.unlink()
                    except OSError: pass
                else:
                    used += size
        except OSError:
            pass
