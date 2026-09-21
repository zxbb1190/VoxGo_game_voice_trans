"""Crash-safe, consent-scoped process lifecycle counters.

Each run owns a marker protected by an operating-system file lock.  A later
run may classify a marker as unclean only after it can acquire that lock, so
another live VoxGo process is never mistaken for a crashed one.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import uuid
from itertools import islice
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


_RUN_NAME = re.compile(r"([0-9a-f]{32})\.json")
_DAY_NAME = re.compile(r"(\d{4}-\d{2}-\d{2})\.json")
_METRICS = {"clean_exits", "unclean_starts"}
_NAMESPACE = uuid.UUID("b3ff2e74-f5c2-4b41-a5b6-9a1df891129c")
_NEW_MARKER_GRACE_SECONDS = 2


def _utc_now():
    return datetime.now(timezone.utc)


class LifecycleTracker:
    """Record one clean or unclean outcome for each application run.

    ``root`` is the collection/consent scope.  Resulting shards are written to
    ``root/shards`` in the same format consumed by ``DailySnapshotStore`` and
    ``AggregateStore``.  All methods are best effort and return failure rather
    than allowing analytics storage errors to affect the application.
    """

    def __init__(self, root, package_type, app_version, *, now=_utc_now,
                 marker_retention_days=7, shard_retention_days=30,
                 scan_limit=256):
        self.root = Path(root)
        self.package_type = str(package_type)[:100]
        self.app_version = str(app_version)[:100]
        self.now = now
        self.marker_retention_days = max(1, int(marker_retention_days))
        self.shard_retention_days = max(1, int(shard_retention_days))
        self.scan_limit = max(1, int(scan_limit))
        self.run_id = None
        self._marker = None
        self._lock_path = None
        self._handle = None
        self._started = False
        self._cleaned = False

    @property
    def runs_root(self):
        return self.root / "runs"

    @property
    def intents_root(self):
        return self.root / "lifecycle-intents"

    @property
    def shards_root(self):
        return self.root / "shards"

    def start(self):
        """Create and lock this run marker, then recover abandoned markers."""
        if self._started:
            return True
        try:
            self.runs_root.mkdir(parents=True, exist_ok=True)
            self.intents_root.mkdir(parents=True, exist_ok=True)
            self.shards_root.mkdir(parents=True, exist_ok=True)
            instant = self._instant()
            self.run_id = uuid.uuid4().hex
            self._marker = self.runs_root / f"{self.run_id}.json"
            self._lock_path = self.runs_root / f"{self.run_id}.lock"
            marker = {
                "schema_version": 1,
                "run_id": self.run_id,
                "started_at": instant.isoformat(),
                "day": instant.date().isoformat(),
                "app_version": self.app_version,
                "package_type": self.package_type,
            }
            descriptor = os.open(self._lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR,
                                 0o600)
            handle = os.fdopen(descriptor, "r+b", buffering=0)
            handle.write(b"1")
            os.fsync(handle.fileno())
            handle.seek(0)
            if not self._try_lock(handle):
                handle.close()
                self._lock_path.unlink(missing_ok=True)
                return False
            self._handle = handle
            if not self._atomic_json(self._marker, marker, create_parents=False):
                self._release()
                self._lock_path.unlink(missing_ok=True)
                return False
            self._started = True
            self._recover_markers(instant)
            self._cleanup_shards(instant.date())
            self._cleanup_orphan_intents()
            return True
        except Exception:
            self._release()
            try:
                if self._marker:
                    self._marker.unlink(missing_ok=True)
                if self._lock_path:
                    self._lock_path.unlink(missing_ok=True)
            except OSError:
                pass
            return False

    def mark_clean_exit(self):
        """Durably record a proven clean shutdown and retire this run marker."""
        if self._cleaned:
            return True
        if not self._started or not self._marker or not self._marker.exists():
            return False
        try:
            # A removed consent scope must never be recreated during shutdown.
            if not self.root.is_dir() or not self.shards_root.is_dir():
                return False
            instant = self._instant()
            intent = self._intent("clean_exits", instant.date().isoformat())
            if not self._atomic_json(self._intent_path(self.run_id), intent,
                                     create_parents=False):
                return False
            if not self._write_shard(intent, create_parents=False):
                return False
            if not self._remove(self._marker):
                return False
            self._remove(self._intent_path(self.run_id))
            self._cleaned = True
            self._release()
            self._remove(self._lock_path)
            return True
        except Exception:
            return False

    def abandon(self):
        """Release resources without recording a clean exit.

        This is intended for consent-scope removal.  The owner removes the old
        scope; this method itself deliberately performs no writes or deletion.
        """
        self._release()

    close_without_clean_exit = abandon

    def _instant(self):
        value = self.now()
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _intent(self, metric, day, marker=None):
        marker = marker or {}
        return {
            "schema_version": 1,
            "run_id": marker.get("run_id", self.run_id),
            "metric": metric,
            "day": day,
            "app_version": marker.get("app_version", self.app_version),
            "package_type": marker.get("package_type", self.package_type),
        }

    def _intent_path(self, run_id):
        return self.intents_root / f"{run_id}.json"

    def _recover_markers(self, instant):
        try:
            paths = list(islice(self.runs_root.iterdir(), self.scan_limit))
        except OSError:
            return
        for path in paths:
            match = _RUN_NAME.fullmatch(path.name)
            if not match or match[1] == self.run_id or path.is_symlink():
                continue
            handle = None
            lock_path = path.with_suffix(".lock")
            try:
                try:
                    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
                    handle = os.fdopen(descriptor, "r+b", buffering=0)
                    if lock_path.stat().st_size == 0:
                        handle.write(b"1")
                        handle.flush()
                    handle.seek(0)
                except OSError:
                    continue
                if not self._try_lock(handle):
                    handle.close()
                    continue
                marker = self._read_json(path)
                if not self._valid_marker(marker, match[1]):
                    if self._old_enough(path, instant):
                        self._remove(path)
                    self._unlock_close(handle)
                    if not path.exists():
                        self._remove(lock_path)
                    continue
                intent_path = self._intent_path(match[1])
                intent = self._read_json(intent_path)
                if not self._valid_intent(intent, marker):
                    intent = None
                if intent is None:
                    started = date.fromisoformat(marker["day"])
                    if started < instant.date() - timedelta(
                            days=self.marker_retention_days - 1):
                        self._remove(path)
                        self._remove(intent_path)
                        self._unlock_close(handle)
                        self._remove(lock_path)
                        continue
                    intent = self._intent("unclean_starts",
                                          instant.date().isoformat(), marker)
                    if not self._atomic_json(intent_path, intent,
                                             create_parents=False):
                        self._unlock_close(handle)
                        continue
                if self._write_shard(intent, create_parents=False):
                    if self._remove(path):
                        self._remove(intent_path)
                self._unlock_close(handle)
                if not path.exists():
                    self._remove(lock_path)
            except Exception:
                if handle is not None:
                    self._unlock_close(handle)

    def _write_shard(self, intent, *, create_parents):
        metric = intent["metric"]
        run_id = intent["run_id"]
        day = intent["day"]
        shard_id = uuid.uuid5(_NAMESPACE, f"{run_id}:{metric}").hex
        directory = self.shards_root / shard_id
        try:
            if create_parents:
                directory.mkdir(parents=True, exist_ok=True)
            else:
                # Creating the event directory is safe only while its existing
                # consent scope and shard root are still present.
                directory.mkdir(exist_ok=True)
            payload = {
                "schema_version": 1,
                "date": day,
                "app_version": intent["app_version"],
                "package_type": intent["package_type"],
                "metrics": {metric: 1},
            }
            return self._atomic_json(directory / f"{day}.json", payload,
                                     create_parents=False)
        except OSError:
            return False

    def _cleanup_shards(self, today):
        cutoff = today - timedelta(days=self.shard_retention_days - 1)
        seen = 0
        try:
            directories = islice(self.shards_root.iterdir(), self.scan_limit)
        except OSError:
            return
        for directory in directories:
            if seen >= self.scan_limit or not directory.is_dir() or directory.is_symlink():
                continue
            try:
                files = list(directory.iterdir())
            except OSError:
                continue
            for path in files:
                if seen >= self.scan_limit:
                    break
                seen += 1
                match = _DAY_NAME.fullmatch(path.name)
                if not match or path.is_symlink():
                    continue
                payload = self._read_json(path)
                metrics = payload.get("metrics") if isinstance(payload, dict) else None
                if not (isinstance(metrics, dict) and len(metrics) == 1
                        and next(iter(metrics), None) in _METRICS
                        and next(iter(metrics.values()), None) == 1):
                    continue
                try:
                    shard_day = date.fromisoformat(match[1])
                except ValueError:
                    continue
                if shard_day < cutoff or shard_day > today:
                    self._remove(path)
            try:
                if not any(directory.iterdir()):
                    directory.rmdir()
            except OSError:
                pass

    def _cleanup_orphan_intents(self):
        try:
            paths = list(islice(self.intents_root.iterdir(), self.scan_limit))
        except OSError:
            return
        for path in paths:
            match = _RUN_NAME.fullmatch(path.name)
            if match and not (self.runs_root / path.name).exists():
                self._remove(path)

    @staticmethod
    def _valid_marker(value, run_id):
        if not isinstance(value, dict):
            return False
        try:
            date.fromisoformat(value["day"])
        except (KeyError, TypeError, ValueError):
            return False
        return (value.get("schema_version") == 1 and value.get("run_id") == run_id
                and isinstance(value.get("app_version"), str)
                and isinstance(value.get("package_type"), str))

    @staticmethod
    def _valid_intent(value, marker):
        if not isinstance(value, dict) or value.get("schema_version") != 1:
            return False
        if value.get("run_id") != marker.get("run_id") or value.get("metric") not in _METRICS:
            return False
        try:
            date.fromisoformat(value["day"])
        except (KeyError, TypeError, ValueError):
            return False
        return (isinstance(value.get("app_version"), str)
                and isinstance(value.get("package_type"), str))

    @staticmethod
    def _read_json(path):
        try:
            if path.is_symlink() or path.stat().st_size > 4096:
                return {}
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _old_enough(path, instant):
        try:
            modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
            return (instant - modified).total_seconds() >= _NEW_MARKER_GRACE_SECONDS
        except OSError:
            return False

    @staticmethod
    def _atomic_json(target, value, *, create_parents):
        temporary = None
        try:
            if create_parents:
                target.parent.mkdir(parents=True, exist_ok=True)
            if not target.parent.is_dir():
                return False
            payload = json.dumps(value, sort_keys=True, allow_nan=False)
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent,
                                             prefix=".lifecycle-", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
            return True
        except (OSError, TypeError, ValueError):
            try:
                if temporary:
                    temporary.unlink(missing_ok=True)
            except OSError:
                pass
            return False

    @staticmethod
    def _remove(path):
        try:
            path.unlink(missing_ok=True)
            return not path.exists()
        except OSError:
            return False

    @staticmethod
    def _try_lock(handle):
        try:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (OSError, IOError):
            return False

    @staticmethod
    def _unlock_close(handle):
        try:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except (OSError, IOError):
            pass
        try:
            handle.close()
        except OSError:
            pass

    def _release(self):
        handle, self._handle = self._handle, None
        if handle is not None:
            self._unlock_close(handle)
        self._started = False

    def __del__(self):
        self._release()
