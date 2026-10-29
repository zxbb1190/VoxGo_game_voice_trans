"""Durable consent-only aggregate outbox. Callers hold lock for each sync cycle."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone, timedelta, date
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
import uuid

from .daily_metrics import METRICS, LIMIT
from .language_usage import usage_map, usage_rows, validate_totals, MAX_COUNT


def utc_today():
    return datetime.now(timezone.utc).date()


class CrossProcessLock:
    """Nonblocking uploader election, supported by Windows and POSIX."""
    def __init__(self, path):
        self.path = Path(path)
        self.file = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open('a+b')
        try:
            if os.name == 'nt':
                import msvcrt
                self.file.seek(0, 2)
                if not self.file.tell():
                    self.file.write(b'0')
                    self.file.flush()
                self.file.seek(0)
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            self.file.close()
            self.file = None
            return False

    def __exit__(self, *args):
        if self.file is not None:
            if os.name == 'nt':
                import msvcrt
                self.file.seek(0)
                msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)
            self.file.close()
            self.file = None


class AggregateStore:
    """Instantiate/use only after explicit consent. Corruption fails closed.

    State and exact pending payload are one atomic transaction. Watermarks remain
    after shard removal so stale shard resurrection cannot count data twice.
    """
    def __init__(self, root, app_version, today=utc_today, package_type=None, language_usage=False):
        self.root = Path(root)
        self.app_version = app_version
        self.today = today
        if language_usage is not None and type(language_usage) is not bool:
            raise ValueError('invalid language payload mode')
        # None is inspection/pruning before capability negotiation, never a POST.
        self.language_usage = language_usage
        from voxgo.package_info import package_type as current_package_type
        self.package_type = current_package_type() if package_type is None else package_type

    def lock(self):
        return CrossProcessLock(self.root / 'uploader.lock')

    def _read(self, path, limit):
        if path.is_symlink() or path.stat().st_size > limit:
            raise ValueError('invalid analytics state file')
        value = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(value, dict):
            raise ValueError('invalid analytics state')
        return value

    def _load(self):
        path = self.root / 'aggregate.json'
        if not path.exists():
            # An identity marker means state disappeared: never silently restart
            # revisions for an existing installation.
            if (self.root / 'identity.json').exists():
                raise ValueError('aggregate state missing')
            state = {'install_id': str(uuid.uuid4()), 'days': {}}
            self._save(state)
            self._atomic(self.root / 'identity.json', {'install_id': state['install_id']})
            return state
        state = self._read(path, 2 * 1024 * 1024)
        uuid.UUID(state['install_id'])
        marker = self.root / 'identity.json'
        if marker.exists():
            if self._read(marker, 1024).get('install_id') != state['install_id']:
                raise ValueError('installation identity mismatch')
        else:
            self._atomic(marker, {'install_id': state['install_id']})
        if not isinstance(state['days'], dict) or len(state['days']) > 7:
            raise ValueError('invalid daily aggregate')
        for day, entry in state['days'].items():
            date.fromisoformat(day)
            if (not isinstance(entry, dict) or type(entry['revision']) is not int
                    or entry['revision'] < 1 or len(entry['seen']) > 512):
                raise ValueError('invalid aggregate entry')
            self._metrics(entry['totals'])
            if (type(entry.get('language_payload_enabled', False)) is not bool
                    or type(entry.get('language_revision', 0)) is not int
                    or not 0 <= entry.get('language_revision', 0) <= entry['revision']):
                raise ValueError('invalid language revision')
            for metrics in entry['seen'].values():
                self._metrics(metrics)
            validate_totals(entry.get('language_totals', []), self._metrics(entry['totals']))
            language_seen = entry.get('language_seen', {})
            if not isinstance(language_seen, dict) or len(language_seen) > 512:
                raise ValueError('invalid language watermarks')
            for key, rows in language_seen.items():
                if key not in entry['seen']:
                    raise ValueError('missing language shard watermark')
                validate_totals(rows, self._metrics(entry['seen'][key]))
            language_pending = entry.get('language_pending')
            if language_pending is not None:
                if (language_pending.get('schema_version') != 3
                        or language_pending.get('install_id') != state['install_id']
                        or language_pending.get('date') != day
                        or type(language_pending.get('revision')) is not int
                        or language_pending['revision'] > entry['revision']):
                    raise ValueError('invalid language pending')
                validate_totals(language_pending.get('language_usage'), self._metrics(language_pending['metrics']))
                unsigned = {k: v for k, v in language_pending.items() if k != 'snapshot_id'}
                canonical = json.dumps(unsigned, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
                if language_pending.get('snapshot_id') != hashlib.sha256(canonical.encode('ascii')).hexdigest():
                    raise ValueError('invalid language pending hash')
                if language_pending['revision'] == entry['revision']:
                    if (self._metrics(language_pending['metrics']) != self._metrics(entry['totals'])
                            or usage_map(language_pending['language_usage']) != usage_map(entry.get('language_totals', []))):
                        raise ValueError('language pending differs from totals')
            pending = entry.get('pending')
            if pending is not None:
                if (pending['install_id'] != state['install_id'] or pending['date'] != day
                        or pending['revision'] != entry['revision']
                        or self._metrics(pending['metrics']) != self._metrics(entry['totals'])):
                    raise ValueError('invalid pending aggregate')
                unsigned = {key: value for key, value in pending.items() if key != 'snapshot_id'}
                canonical = json.dumps(unsigned, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
                if pending['snapshot_id'] != hashlib.sha256(canonical.encode('ascii')).hexdigest():
                    raise ValueError('invalid pending hash')
        return state

    def _atomic(self, target, value):
        data = json.dumps(value, sort_keys=True, allow_nan=False)
        if len(data.encode('utf-8')) > 2 * 1024 * 1024:
            raise ValueError('aggregate size limit')
        self.root.mkdir(parents=True, exist_ok=True)
        temp = None
        try:
            with NamedTemporaryFile('w', encoding='utf-8', dir=self.root,
                                    prefix='.aggregate-', delete=False) as file:
                temp = Path(file.name)
                file.write(data)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp, target)
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)

    def _save(self, state):
        self._atomic(self.root / 'aggregate.json', state)

    @staticmethod
    def _metrics(value):
        if not isinstance(value, dict) or set(value) - METRICS:
            raise ValueError('invalid metrics')
        if any(type(v) is not int or not 0 <= v <= LIMIT for v in value.values()):
            raise ValueError('invalid metric value')
        return {key: value.get(key, 0) for key in sorted(METRICS)}

    @property
    def install_id(self):
        return self._load()['install_id']

    def claim_round(self, now, next_attempt, force=False):
        state = self._load()
        if not force and now < state.get('next_attempt', 0):
            return False
        state['next_attempt'] = next_attempt
        self._save(state)
        return True

    def retry_state(self):
        state = self._load()
        return min(7, max(0, int(state.get('failures', 0))))

    def record_retry(self, failures, next_attempt):
        state = self._load()
        state['failures'] = min(7, max(0, failures))
        state['next_attempt'] = next_attempt
        self._save(state)

    def snapshots(self):
        state = self._load()
        today = self.today()
        first = today - timedelta(days=6)
        state['days'] = {day: entry for day, entry in state['days'].items()
                         if first <= date.fromisoformat(day) <= today}
        changed = set()
        # Older v1 baselines have no lifecycle counters. Extend only baselines;
        # an existing pending payload/hash remains exact until new data arrives.
        for entry in state['days'].values():
            entry['totals'] = self._metrics(entry['totals'])
        for path in sorted((self.root / 'shards').glob('*/*.json')):
            try:
                day = date.fromisoformat(path.stem)
                uuid.UUID(path.parent.name)
                if not first <= day <= today:
                    path.unlink(missing_ok=True)
                    continue
                shard = self._read(path, 32768)
                if shard.get('schema_version') not in (1, 2) or shard.get('date') != path.stem:
                    continue
                metrics = self._metrics(shard.get('metrics'))
            except (ValueError, KeyError, OSError, TypeError):
                continue
            entry = state['days'].setdefault(path.stem, {
                'revision': 0, 'totals': dict.fromkeys(sorted(METRICS), 0), 'seen': {}})
            key = path.parent.name
            if key not in entry['seen'] and len(entry['seen']) >= 512:
                continue
            previous = entry['seen'].get(key, dict.fromkeys(METRICS, 0))
            # Counter decreases indicate stale writes; retain high watermarks.
            delta = {name: max(0, metrics[name] - previous.get(name, 0)) for name in METRICS}
            if any(entry['totals'][name] + delta[name] > LIMIT for name in METRICS):
                continue
            for name in METRICS:
                entry['totals'][name] += delta[name]
            entry['seen'][key] = {name: max(metrics[name], previous.get(name, 0)) for name in METRICS}
            # Keep independent high watermarks so old writers can ignore this
            # extension without either erasing it or counting resurrected shards.
            try:
                incoming = validate_totals(shard.get('language_usage', []), metrics)
            except (ValueError, TypeError, KeyError):
                incoming = {}
            totals = usage_map(entry.get('language_totals', []))
            seen = entry.setdefault('language_seen', {})
            previous_language = usage_map(seen.get(key, []))
            candidate = deepcopy(totals)
            watermark = deepcopy(previous_language)
            language_changed = False
            for direction, amounts in incoming.items():
                old = previous_language.get(direction, {'success': 0, 'failed': 0})
                watermark[direction] = {name: max(amounts[name], old[name]) for name in ('success', 'failed')}
                accumulated = candidate.setdefault(direction, {'success': 0, 'failed': 0})
                for name in ('success', 'failed'):
                    increment = max(0, amounts[name] - old[name])
                    accumulated[name] += increment
                    language_changed |= increment > 0
            if all(max(row.values()) <= MAX_COUNT for row in candidate.values()):
                validate_totals(usage_rows(candidate), entry['totals'])
                entry['language_totals'] = usage_rows(candidate)
                if watermark:
                    seen[key] = usage_rows(watermark)
                if language_changed:
                    changed.add(path.stem)
            if any(delta.values()) or entry['revision'] == 0:
                changed.add(path.stem)
        for day, entry in state['days'].items():
            enabled = (entry.get('language_payload_enabled', False) if self.language_usage is None
                       else self.language_usage)
            if self.language_usage is not None and enabled != entry.get('language_payload_enabled', False):
                changed.add(day)
            # An older executable may have advanced only the coarse revision.
            if enabled and entry.get('language_revision', 0) != entry['revision']:
                changed.add(day)
            pending = entry.get('language_pending')
            if pending and pending['revision'] < entry['revision']:
                entry['language_pending'] = None
        for day in changed:
            entry = state['days'][day]
            entry['revision'] += 1
            enabled = (entry.get('language_payload_enabled', False) if self.language_usage is None
                       else self.language_usage)
            payload = {'schema_version': 3 if enabled else 2, 'install_id': state['install_id'],
                                'date': day, 'revision': entry['revision'],
                                'app_version': self.app_version,
                                'package_type': self.package_type, 'metrics': deepcopy(entry['totals'])}
            if enabled:
                payload['language_usage'] = deepcopy(entry.get('language_totals', []))
            canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
            payload['snapshot_id'] = hashlib.sha256(canonical.encode('ascii')).hexdigest()
            # schema3 has a separate outbox slot invisible to legacy binaries.
            entry['pending'] = None if enabled else payload
            entry['language_pending'] = payload if enabled else None
            entry['language_payload_enabled'] = enabled
            if enabled:
                entry['language_revision'] = entry['revision']
        self._save(state)
        return [deepcopy(entry.get('language_pending') or entry.get('pending'))
                for day, entry in sorted(state['days'].items())
                if entry.get('language_pending') is not None or entry.get('pending') is not None]

    def acknowledge(self, payload):
        state = self._load()
        entry = state['days'].get(payload.get('date'))
        slot = 'language_pending' if payload.get('schema_version') == 3 else 'pending'
        if entry is None or entry.get(slot) != payload:
            return False
        entry[slot] = None
        self._save(state)
        # Baseline and watermarks intentionally survive successful upload.
        return True
