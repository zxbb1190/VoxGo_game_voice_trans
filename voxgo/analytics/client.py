"""Bounded local analytics and consent-isolated remote collection."""
from __future__ import annotations

import queue
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from collections import deque
from pathlib import Path

from .daily_metrics import DailyMetrics
from .storage import DailySnapshotStore
from voxgo.package_info import package_type


class LocalAnalytics:
    """Best-effort collector. No public method waits for disk or network IO."""

    def __init__(self, root, app_version, *, flush_interval=30.0, storage_root=None, cleanup_hook=None,
                 collection_allowed=None, count_start=True, lifecycle_root=None):
        self._root = Path(storage_root) if storage_root is not None else Path(root) / 'analytics'
        self._version = app_version
        self._cleanup_hook = cleanup_hook
        self._collection_allowed = collection_allowed
        self._count_start = count_start
        self._lifecycle_root = Path(lifecycle_root) if lifecycle_root is not None else None
        self._lifecycle = None
        self._lifecycle_abandoned = threading.Event()
        self._lifecycle_guard = threading.RLock()
        self._lifecycle_finalized = False
        self._clean_exit_worker = None
        self._package_type = package_type()
        self._interval = max(0.1, float(flush_interval))
        self._queue = queue.Queue(maxsize=1024)
        self._stopped = threading.Event()
        self._state_lock = threading.Lock()
        self._desired_active = (False, None, time.monotonic())
        self._transitions = deque(maxlen=1024)
        self._thread = threading.Thread(target=self._run, name='local-analytics', daemon=True)
        try:
            self._thread.start()
        except Exception:
            self._stopped.set()

    def _submit(self, *command):
        try:
            if not self._stopped.is_set():
                self._queue.put_nowait(command)
        except Exception:
            pass

    def increment(self, name, value=1):
        self._submit('increment', name, value)

    def observe(self, name, elapsed_ms):
        self._submit('observe', name, elapsed_ms)

    def set_active(self, active, mode=None):
        try:
            if not self._stopped.is_set():
                with self._state_lock:
                    if self._desired_active[:2] == (bool(active), mode):
                        return
                    self._desired_active = (bool(active), mode, time.monotonic())
                    self._transitions.append(self._desired_active)
        except Exception:
            pass

    def stop(self):
        """Signal a final best-effort flush; never join during application exit."""
        try:
            self.set_active(False)
            self._stopped.set()
        except Exception:
            pass

    def mark_clean_exit(self):
        # Called after Qt has ended and service cleanup succeeded, never on quit request.
        # Disk/lock stalls must not hold application exit indefinitely.
        if self._clean_exit_worker is None:
            self._clean_exit_worker = threading.Thread(
                target=self._finish_clean_exit, name='analytics-clean-exit', daemon=True)
            self._clean_exit_worker.start()
        self._clean_exit_worker.join(timeout=0.2)

    def _finish_clean_exit(self):
        try:
            self._finish_clean_exit_impl()
        except Exception:
            pass  # Lifecycle accounting cannot break application shutdown.

    def _finish_clean_exit_impl(self):
        with self._lifecycle_guard:
            if self._lifecycle_finalized or self._lifecycle_abandoned.is_set():
                return
            # A very fast clean exit may beat the daemon writer's initialization.
            # Finish the small local marker transaction here rather than allow a
            # late writer to create a false unclean marker after successful exit.
            self._start_lifecycle()
            if self._lifecycle is not None and self._can_collect():
                self._lifecycle.mark_clean_exit()
                self._cleanup()
            self._lifecycle_finalized = True

    def _start_lifecycle(self):
        with self._lifecycle_guard:
            if (self._lifecycle is not None or self._lifecycle_root is None
                    or self._lifecycle_finalized or self._lifecycle_abandoned.is_set()
                    or not self._can_collect()):
                return
            from .lifecycle import LifecycleTracker
            self._lifecycle = LifecycleTracker(self._lifecycle_root, self._package_type, self._version)
            self._lifecycle.start()
            if self._lifecycle_abandoned.is_set() or not self._can_collect():
                self._lifecycle.abandon()

    def abandon_lifecycle(self):
        self._lifecycle_abandoned.set()
        with self._lifecycle_guard:
            if self._lifecycle is not None:
                self._lifecycle.abandon()

    def _cleanup(self):
        # Enforce one budget across process directories, including damaged/temp files.
        try:
            cutoff = time.time() - 30 * 86400
            files = []
            directories = list(self._root.iterdir())
            lifecycle_shards = self._root / 'shards'
            if lifecycle_shards.is_dir() and not lifecycle_shards.is_symlink():
                directories.extend(lifecycle_shards.iterdir())
            for directory in directories:
                if (not re.fullmatch(r'[0-9a-f]{32}', directory.name)
                        or not directory.is_dir() or directory.is_symlink()):
                    continue
                for path in directory.iterdir():
                    if path.is_symlink() or not path.is_file():
                        continue
                    if (not re.fullmatch(r'\d{4}-\d{2}-\d{2}\.json(?:\.corrupt-\d+)?', path.name)
                            and not path.name.startswith('.snapshot-')):
                        continue
                    stat = path.stat()
                    if stat.st_mtime < cutoff:
                        path.unlink(missing_ok=True)
                    else:
                        files.append((stat.st_mtime, str(path), stat.st_size))
            used = 0
            for index, (_, name, size) in enumerate(sorted(files, reverse=True)):
                if index >= 90 or used + size > 2 * 1024 * 1024:
                    Path(name).unlink(missing_ok=True)
                else:
                    used += size
            for directory in directories:
                if (re.fullmatch(r'[0-9a-f]{32}', directory.name)
                        and directory.is_dir() and not directory.is_symlink()):
                    try:
                        directory.rmdir()
                    except OSError:
                        pass
        except OSError:
            pass
        if self._cleanup_hook:
            try:
                self._cleanup_hook()
            except Exception:
                pass

    def _can_collect(self):
        # Only called by the background writer; durable authorization may use IO.
        try:
            return self._collection_allowed is None or bool(self._collection_allowed())
        except Exception:
            return False

    def _run(self):
        try:
            if not self._can_collect():
                self._stopped.set()
                return
            store = DailySnapshotStore(self._root / uuid.uuid4().hex,
                today=lambda: datetime.now(timezone.utc).date())
            metrics = DailyMetrics(store, self._version, package_type=self._package_type)
            with self._lifecycle_guard:
                if self._lifecycle_abandoned.is_set() or not self._can_collect():
                    return
                self._start_lifecycle()
                if self._lifecycle_abandoned.is_set() or not self._can_collect():
                    return
                if self._count_start:
                    metrics.increment('app_starts')
                metrics.increment('sessions')
                metrics.flush()
            self._cleanup()
            last_tick = last_flush = time.monotonic()
            active = False
            remainder = 0.0
            modes = set()
            participation_day = store.today().isoformat()
            current_mode = None
            while True:
                try:
                    command = self._queue.get(timeout=0.1)
                except queue.Empty:
                    command = None
                day = store.today().isoformat()
                if day != participation_day:
                    participation_day = day
                    modes.clear()
                    metrics.increment('sessions')
                    if active and current_mode in ('offline', 'api'):
                        modes.add(current_mode)
                        metrics.increment(current_mode + '_sessions')
                if command:
                    try:
                        getattr(metrics, command[0])(*command[1:])
                    except Exception:
                        pass
                now = time.monotonic()
                with self._state_lock:
                    states = list(self._transitions)
                    self._transitions.clear()
                for state in states:
                    transition = max(last_tick, min(now, state[2]))
                    if active:
                        remainder += min(2.0, max(0.0, transition - last_tick))
                    active = state[0]
                    current_mode = state[1]
                    last_tick = transition
                    if active and state[1] in ('offline', 'api') and state[1] not in modes:
                        modes.add(state[1])
                        metrics.increment(state[1] + '_sessions')
                if active:
                    remainder += min(2.0, max(0.0, now - last_tick))
                last_tick = now
                seconds = int(remainder)
                if seconds:
                    metrics.increment('session_seconds', seconds)
                    remainder -= seconds
                finishing = self._stopped.is_set() and self._queue.empty()
                if finishing or now - last_flush >= self._interval:
                    with self._lifecycle_guard:
                        if self._lifecycle_abandoned.is_set() or not self._can_collect():
                            self._stopped.set()
                            return
                        metrics.flush()
                    self._cleanup()
                    last_flush = now
                if finishing:
                    return
        except Exception:
            # Analytics must not affect startup, translation, or shutdown.
            self._stopped.set()


class AuthorizedAnalytics:
    """Remote buffers are isolated by explicit authorization epoch."""
    def __init__(self, root, app_version, consent_getter):
        self.root = Path(root)
        self.version = app_version
        self.get_consent = consent_getter
        self.local = LocalAnalytics(root, app_version, cleanup_hook=self._cleanup_remote,
                                    lifecycle_root=Path(root) / 'analytics')
        self.remote = None
        self.uploader = None
        self._epoch = None
        self._active = (False, None)
        self._lock = threading.RLock()
        self._stopping = False
        self._remote_started = False
        self.refresh_consent()

    def _cleanup_remote(self):
        import json
        from types import SimpleNamespace
        from .consent import may_upload
        from .retention import cleanup_remote
        from .aggregation import AggregateStore
        # Runs on the local writer thread; never on a translation/UI callback.
        try:
            data = json.loads((self.root / 'telemetry_consent.json').read_text(encoding='utf-8'))
            config = SimpleNamespace(**data)
        except Exception:
            return
        epoch = getattr(config, 'telemetry_epoch', '') if may_upload(config, True) else None
        cleanup_remote(self.root / 'analytics-remote', epoch)
        if epoch and str(uuid.UUID(epoch)) == epoch:
            remote_root = self.root / 'analytics-remote' / epoch
            if (remote_root / 'aggregate.json').exists():
                store = AggregateStore(remote_root, self.version)
                with store.lock() as acquired:
                    if acquired:
                        store.snapshots()  # Prune expired aggregate days even offline.

    def _remote_consent(self, epoch):
        # Read durable consent before every HTTP request, so revocation in a
        # second process also disables this process. Missing/corrupt = denied.
        import json
        from types import SimpleNamespace
        from .consent import may_upload
        try:
            current = self.get_consent()
            if not may_upload(current, True) or getattr(current, 'telemetry_epoch', '') != epoch:
                return None
            path = self.root / 'telemetry_consent.json'
            if path.stat().st_size > 1024 * 1024:
                return None
            saved = SimpleNamespace(**json.loads(path.read_text(encoding='utf-8')))
            return saved if getattr(saved, 'telemetry_epoch', '') == epoch else None
        except Exception:
            return None

    def refresh_consent(self):
        from .consent import may_upload
        from .uploader import RemoteUploader
        with self._lock:
            try:
                config = self.get_consent()
            except Exception:
                config = None
            epoch = getattr(config, 'telemetry_epoch', '')
            try:
                valid_epoch = str(uuid.UUID(epoch)) == epoch
            except (ValueError, TypeError, AttributeError):
                valid_epoch = False
            allowed = not self._stopping and may_upload(config, True) and valid_epoch
            if not allowed or epoch != self._epoch:
                if self.uploader:
                    self.uploader.stop()
                if self.remote:
                    self.remote.stop()
                    self.remote.abandon_lifecycle()
                self.uploader = self.remote = None
                self._epoch = None
            if allowed and self.remote is None:
                self._epoch = epoch
                remote_root = self.root / 'analytics-remote' / epoch
                self.remote = LocalAnalytics(self.root, self.version,
                    storage_root=remote_root / 'shards',
                    lifecycle_root=remote_root,
                    collection_allowed=lambda: may_upload(self._remote_consent(epoch), True),
                    count_start=not self._remote_started)
                self._remote_started = True
                self.remote.set_active(*self._active)
                self.uploader = RemoteUploader(remote_root,
                    lambda: self._remote_consent(epoch), app_version=self.version)

    def _call(self, method, *args):
        try:
            with self._lock:
                if self._stopping:
                    return
                getattr(self.local, method)(*args)
                self.refresh_consent()
                if self.remote:
                    getattr(self.remote, method)(*args)
        except Exception:
            pass

    def increment(self, name, value=1):
        self._call('increment', name, value)

    def observe(self, name, elapsed_ms):
        self._call('observe', name, elapsed_ms)

    def set_active(self, active, mode=None):
        self._active = (active, mode)
        self._call('set_active', active, mode)

    def stop(self):
        with self._lock:
            self._stopping = True
            if self.uploader:
                self.uploader.stop()
            self.local.stop()
            if self.remote:
                self.remote.stop()

    def mark_clean_exit(self):
        self.local.mark_clean_exit()
        if self.remote:
            self.remote.mark_clean_exit()
