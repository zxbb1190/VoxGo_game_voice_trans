"""Content-free daily installation state, independent of Full consent.

All IO runs on the daemon worker. The shared on-disk lock elects one uploader
and protects revisions across processes. No business events enter this channel.
"""
from copy import deepcopy
from datetime import datetime, timezone, timedelta, date
import hashlib
import json
from pathlib import Path
import random
import re
import threading
import time
from types import SimpleNamespace
import uuid

from .aggregation import AggregateStore, CrossProcessLock
from .consent import may_upload
from .debug import AnalyticsDebug
from .uploader import HTTPTransport, parse_config

SOURCES = frozenset(('new_install_pending', 'new_install_default', 'user_enabled',
    'user_disabled', 'migration_allowed', 'migration_denied', 'migration_unknown', 'unknown'))
PACKAGES = frozenset(('lite', 'full', 'full-cuda', 'source', 'unknown'))
FIELDS = frozenset(('schema_version', 'date', 'daily_id', 'revision', 'snapshot_id',
    'app_version', 'package_type', 'first_run', 'setup_completed', 'full_telemetry',
    'full_telemetry_source'))


def valid_snapshot(payload):
    if not isinstance(payload, dict) or set(payload) != FIELDS:
        return False
    try:
        return (type(payload['schema_version']) is int and payload['schema_version'] == 1
            and isinstance(payload['date'], str)
            and date.fromisoformat(payload['date']).isoformat() == payload['date']
            and isinstance(payload['daily_id'], str)
            and re.fullmatch('[a-f0-9]{64}', payload['daily_id']) is not None
            and type(payload['revision']) is int and 0 < payload['revision'] <= 2**53 - 1
            and isinstance(payload['app_version'], str) and len(payload['app_version']) <= 64
            and re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?', payload['app_version']) is not None
            and payload['package_type'] in PACKAGES
            and payload['full_telemetry_source'] in SOURCES
            and all(type(payload[k]) is bool for k in ('first_run', 'setup_completed', 'full_telemetry'))
            and payload['snapshot_id'] == canonical_hash(payload))
    except (ValueError, TypeError, KeyError):
        return False


def canonical_hash(payload):
    unsigned = {key: value for key, value in payload.items() if key != 'snapshot_id'}
    return hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True).encode('ascii')).hexdigest()


def daily_identity(seed, day):
    if not isinstance(seed, str) or str(uuid.UUID(seed)) != seed:
        raise ValueError('invalid_basic_seed')
    if date.fromisoformat(day).isoformat() != day:
        raise ValueError('invalid_basic_date')
    # Delimited domain separation, not a hardware identifier or a secret salt.
    return hashlib.sha256(('voxgo-basic-v1\0' + seed + '\0' + day).encode('ascii')).hexdigest()


def read_json(path, limit=1024 * 1024):
    if path.is_symlink() or path.stat().st_size > limit:
        raise ValueError('invalid_basic_file')
    value = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(value, dict):
        raise ValueError('invalid_basic_object')
    return value


def installation_state(root, version, package, day):
    """Read persisted settings; never start using an uncommitted random seed."""
    app = read_json(root / 'user_settings.json').get('app')
    if not isinstance(app, dict) or app.get('telemetry_v2_migrated') is not True:
        raise ValueError('basic_migration_required')
    identity = daily_identity(app.get('basic_install_seed'), day)
    first = app.get('basic_first_run_date', '')
    if first and (not isinstance(first, str) or date.fromisoformat(first).isoformat() != first):
        raise ValueError('invalid_first_run_date')
    if type(app.get('setup_completed')) is not bool or package not in PACKAGES:
        raise ValueError('invalid_basic_state')
    authority = root / 'telemetry_consent.json'
    from .migration import validated_consent
    try:
        saved = read_json(authority)
        validated = validated_consent(saved)
        consent = {**app, **validated}
        valid_authority = all(saved.get(key) == value for key, value in validated.items())
        consent['full_telemetry_source'] = (saved.get('full_telemetry_source',
            app.get('full_telemetry_source', 'unknown')) if valid_authority else 'unknown')
    except (OSError, ValueError, TypeError):
        # Full's missing/corrupt authority must never disable independent Basic.
        consent = {**app, **validated_consent({}), 'full_telemetry_source': 'unknown'}
    source = consent.get('full_telemetry_source', 'unknown')
    if source not in SOURCES:
        source = 'unknown'
    epoch = consent.get('telemetry_epoch', '')
    try:
        valid_epoch = isinstance(epoch, str) and str(uuid.UUID(epoch)) == epoch
    except (ValueError, TypeError, AttributeError):
        valid_epoch = False
    full = may_upload(SimpleNamespace(**consent), True) and valid_epoch
    return dict(schema_version=1, date=day, daily_id=identity, app_version=version,
                package_type=package, first_run=first == day,
                setup_completed=app['setup_completed'], full_telemetry=full,
                full_telemetry_source=source)


class BasicStore:
    def __init__(self, root):
        self.root = Path(root)
        self.path = self.root / 'state.json'

    def lock(self):
        return CrossProcessLock(self.root / 'uploader.lock')

    def load(self):
        if not self.path.exists():
            if (self.root / 'initialized').exists():
                raise ValueError('basic_state_missing')
            return dict(days={}, failures=0, next_attempt=0)
        state = read_json(self.path, 65536)
        if not isinstance(state.get('days'), dict) or len(state['days']) > 7:
            raise ValueError('invalid_basic_days')
        if (type(state.get('failures')) is not int or not 0 <= state['failures'] <= 7
                or type(state.get('next_attempt')) not in (int, float)
                or not 0 <= state['next_attempt'] < 10**12):
            raise ValueError('invalid_basic_retry')
        for day, entry in state['days'].items():
            payload = entry['snapshot']
            if (not valid_snapshot(payload) or payload['date'] != day
                    or type(entry.get('pending')) is not bool):
                raise ValueError('invalid_basic_snapshot')
        return state

    def save(self, state):
        # Reuse atomic JSON persistence, not Full's shards/cumulative machinery.
        atomic = AggregateStore(self.root, '0.0.0')
        atomic._atomic(self.path, state)
        if not (self.root / 'initialized').exists():
            atomic._atomic(self.root / 'initialized', {'initialized': True})

    def refresh(self, state, fields):
        day = fields['date']
        cutoff = (date.fromisoformat(day) - timedelta(days=6)).isoformat()
        state['days'] = {d: e for d, e in state['days'].items() if cutoff <= d <= day}
        entry = state['days'].get(day)
        previous = entry['snapshot'] if entry else None
        fields = dict(fields)
        if previous:
            if previous['daily_id'] != fields['daily_id']:
                raise ValueError('basic_identity_changed')
            fields['first_run'] |= previous['first_run']
            fields['setup_completed'] |= previous['setup_completed']
        old_fields = {k: v for k, v in (previous or {}).items() if k not in ('revision', 'snapshot_id')}
        if old_fields != fields:
            fields['revision'] = previous['revision'] + 1 if previous else 1
            fields['snapshot_id'] = canonical_hash(fields)
            if not valid_snapshot(fields):
                raise ValueError('invalid_basic_snapshot')
            state['days'][day] = dict(snapshot=fields, pending=True)

    def acknowledge(self, state, payload, result):
        if (not isinstance(result, dict) or result.get('success') is not True
                or result.get('disposition') not in ('stored', 'superseded')
                or type(result.get('revision')) is not int
                or any(result.get(k) != payload[k] for k in ('daily_id', 'date', 'revision', 'snapshot_id'))):
            return False
        entry = state['days'].get(payload['date'])
        if not entry or entry['snapshot'] != payload:
            return False
        entry['pending'] = False
        return True


class BasicTelemetry:
    def __init__(self, root, app_version, transport=None, start=True, clock=time.time,
                 package_type=None, startup_delay=3):
        from voxgo.package_info import package_type as current_package
        self.root = Path(root)
        self.version = app_version
        self.package = current_package() if package_type is None else package_type
        self.transport = transport or HTTPTransport()
        self.clock = clock
        self.store = BasicStore(self.root / 'analytics-basic')
        self.debug = AnalyticsDebug(self.store.root)
        self.stopped = threading.Event()
        self.startup_delay = startup_delay
        self.next_poll = 0
        self.thread = threading.Thread(target=self._run, name='telemetry-basic', daemon=True)
        if start:
            self.thread.start()

    def stop(self):
        self.stopped.set()  # Never join a network operation on shutdown.

    def _defer(self, state, headers=None, status=None):
        from email.utils import parsedate_to_datetime
        state['failures'] = min(7, state['failures'] + 1)
        delay = min(86400, 900 * 2 ** (state['failures'] - 1))
        if status == 403:
            delay = max(delay, 21600)
        retry = next((v for k, v in (headers or {}).items() if k.lower() == 'retry-after'), None)
        try:
            try:
                delay = max(delay, min(86400, int(retry)))
            except (ValueError, TypeError):
                delay = max(delay, min(86400, parsedate_to_datetime(retry).timestamp() - self.clock()))
        except (ValueError, TypeError, AttributeError, OverflowError):
            pass
        state['next_attempt'] = self.clock() + delay + random.uniform(0, 60)
        self.debug.update(last_result='retry', failure_count=state['failures'],
                          next_retry_at=state['next_attempt'])

    def sync_once(self):
        if self.stopped.is_set() or self.clock() < self.next_poll:
            return
        self.next_poll = self.clock() + 10
        try:
            with self.store.lock() as acquired:
                if not acquired or self.stopped.is_set():
                    return
                day = datetime.fromtimestamp(self.clock(), timezone.utc).date().isoformat()
                fields = installation_state(self.root, self.version, self.package, day)
                state = self.store.load()
                before = deepcopy(state)
                self.store.refresh(state, fields)
                if state != before:
                    self.store.save(state)
                pending = [e['snapshot'] for _, e in sorted(state['days'].items()) if e['pending']]
                self.debug.update(outbox_count=len(pending), failure_count=state['failures'],
                                  next_retry_at=state['next_attempt'])
                if not pending or self.clock() < state['next_attempt']:
                    return
                state['next_attempt'] = self.clock() + 900 + random.uniform(0, 60)
                self.store.save(state)  # Crash-safe frequency bound before any IO.
                try:
                    if self.stopped.is_set():
                        return
                    status, headers, config = self.transport('GET', '/v1/config')
                    self.debug.update(http_status=status, last_result='config_request')
                    if status != 200:
                        self._defer(state, headers, status)
                        return
                    _, _, interval = parse_config(config)
                    if type(config.get('basic_telemetry_enabled')) is not bool:
                        raise ValueError('basic_config_unavailable')
                    state['next_attempt'] = self.clock() + interval + random.uniform(0, 60)
                    if not config['basic_telemetry_enabled']:
                        state['failures'] = 0
                        self.debug.update(last_result='remote_disabled')
                        return
                    for payload in pending:
                        if self.stopped.is_set():
                            break
                        status, headers, result = self.transport('POST', '/v1/telemetry/basic', payload)
                        self.debug.update(http_status=status)
                        if status != 200 or not self.store.acknowledge(state, payload, result):
                            self._defer(state, headers, status)
                            break
                        state['failures'] = 0
                        self.debug.update(last_result='acknowledged', revision=payload['revision'])
                except Exception:
                    self._defer(state)
                finally:
                    self.store.save(state)
                    self.debug.update(outbox_count=sum(e['pending'] for e in state['days'].values()),
                        failure_count=state['failures'], next_retry_at=state['next_attempt'])
        except Exception:
            self.debug.update(last_result='local_state_error')
            self.next_poll = self.clock() + 60

    def _run(self):
        if self.stopped.wait(self.startup_delay):
            return
        while not self.stopped.is_set():
            self.sync_once()
            self.stopped.wait(10)
