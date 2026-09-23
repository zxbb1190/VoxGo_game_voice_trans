"""Bounded, consent-gated HTTPS uploader. Never used on the exit path."""
import hashlib
import json
import random
import threading
import time
import urllib.error
import urllib.request
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit
from pathlib import Path

from .aggregation import AggregateStore
from .consent import may_upload, normalize_consent
from .debug import AnalyticsDebug

API_ROOT = 'https://api.voxgo.cn'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class HTTPTransport:
    def __init__(self, api_root=API_ROOT):
        parsed = urlsplit(api_root)
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username
                or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ('', '/')):
            raise ValueError('invalid HTTPS API origin')
        self.api_root = api_root.rstrip('/')

    def __call__(self, method, path, payload=None):
        if path not in ('/v1/config', '/v1/telemetry/sync', '/v1/telemetry/basic'):
            raise ValueError('invalid API path')
        body = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode() if payload else None
        request = urllib.request.Request(self.api_root + path, data=body, method=method,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        opener = urllib.request.build_opener(NoRedirect())
        try:
            # Background uploads need time for the Worker and D1 acknowledgement.
            response = opener.open(request, timeout=15 if method == 'POST' else 5)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            raw = response.read(32769)
            if len(raw) > 32768:
                raise ValueError('response too large')
            try:
                data = json.loads(raw or b'{}')
            except (ValueError, UnicodeError):
                data = None
            return response.status, dict(response.headers), data


def parse_config(data):
    if not isinstance(data, dict) or type(data.get('schema_version')) is not int or data.get('schema_version') != 1:
        raise ValueError('invalid configuration')
    enabled = data.get('telemetry_enabled')
    rate = data.get('telemetry_sample_rate')
    interval = data.get('sync_interval_seconds')
    if (type(enabled) is not bool or type(rate) not in (int, float)
            or not 0 <= rate <= 1 or type(interval) is not int
            or not 900 <= interval <= 86400):
        raise ValueError('invalid configuration')
    return enabled, rate, interval


class RemoteUploader:
    def __init__(self, root, consent_getter, transport=None, start=True, app_version="0.4.3",
                 startup_delay=3.0, clock=None):
        self.root = Path(root)
        self.debug = AnalyticsDebug(self.root)
        self.consent_getter = consent_getter
        self.app_version = app_version
        self.transport = transport or HTTPTransport()
        if not 2.0 <= startup_delay <= 5.0:
            raise ValueError('startup_delay must be between 2 and 5 seconds')
        self.startup_delay = float(startup_delay)
        self.clock = clock or time.time
        self.stopped = threading.Event()
        self.next_attempt = 0
        self.thread = threading.Thread(target=self._run, name='telemetry-uploader', daemon=True)
        if start:
            self.thread.start()

    def allowed(self):
        try:
            return not self.stopped.is_set() and may_upload(self.consent_getter(), True)
        except Exception:
            return False

    def stop(self):
        self.stopped.set()

    def _defer_retry(self, store, headers=None, status=None):
        failures = store.retry_state() + 1
        delay = min(86400, 900 * 2 ** min(failures - 1, 7))
        if status == 403:
            delay = max(21600, delay)
        value = next((value for key, value in (headers or {}).items()
                      if key.lower() == 'retry-after'), None)
        if value is not None:
            try:
                try:
                    retry = int(value)
                except (ValueError, TypeError):
                    retry = parsedate_to_datetime(value).timestamp() - self.clock()
                delay = max(delay, min(86400, retry))
            except (ValueError, TypeError, OverflowError):
                pass
        self.next_attempt = self.clock() + delay + random.uniform(0, 60)
        store.record_retry(failures, self.next_attempt)
        self.debug.update(failure_count=failures, next_retry_at=self.next_attempt)

    def sync_once(self):
        if not self.allowed():
            self.debug.update(persist=False, skip_reason='consent_or_stopped')
            return
        if self.clock() < self.next_attempt:
            return  # Preserve the last substantive outcome during the polling wait.
        self.debug.update(last_schedule=self.clock(), skip_reason=None,
                          config_enabled=None, sampled=None, http_status=None,
                          error_type=None)
        try:
            consent = self.consent_getter()
            self.debug.update(consent=normalize_consent(getattr(consent, 'telemetry_consent', None)),
                              consent_version=getattr(consent, 'telemetry_consent_version', 0))
        except Exception:
            self.debug.update(skip_reason='consent_read_error')
        self.next_attempt = self.clock() + 900 + random.uniform(0, 60)
        store = None
        stage = 'aggregate'
        try:
            store = AggregateStore(self.root, self.app_version)
            with store.lock() as acquired:
                if not acquired or not self.allowed():
                    self.debug.update(persist=self.allowed(), skip_reason=
                                      'lock_busy' if not acquired else 'consent_or_stopped')
                    return
                self.debug.update(daily_snapshot_exists=any(
                    (self.root / 'shards').glob('*/*.json')))
                pending = store.snapshots()
                state = store._load()
                self.debug.update(outbox_count=len(pending),
                    revision=max((p['revision'] for p in pending), default=None),
                    next_retry_at=state.get('next_attempt', 0),
                    failure_count=state.get('failures', 0))
                if not pending:
                    self.debug.update(skip_reason='no_pending_snapshot')
                    return
                if not store.claim_round(self.clock(), self.next_attempt):
                    self.debug.update(skip_reason='persisted_retry_not_due')
                    return
                try:
                    stage = 'config_request'
                    self.debug.update(last_attempt=self.clock(), last_result='config_request',
                        config_attempt_at=self.clock(), config_request_url=(
                            self.transport.api_root + '/v1/config' if isinstance(self.transport, HTTPTransport) else None),
                        config_http_status=None, config_server_header=None, config_cf_ray=None,
                        config_raw_enabled=None, config_effective_enabled=None)
                    status, headers, data = self.transport('GET', '/v1/config')
                    response_headers = {k.lower(): v for k, v in headers.items()}
                    raw_enabled = data.get('telemetry_enabled') if isinstance(data, dict) else None
                    self.debug.update(http_status=status, config_http_status=status,
                        config_server_header=response_headers.get('server'),
                        config_cf_ray=response_headers.get('cf-ray'),
                        config_raw_enabled=raw_enabled if type(raw_enabled) is bool else None)
                    if not self.allowed():
                        self.debug.update(persist=False, skip_reason='consent_or_stopped')
                        return
                    if status != 200:
                        self._defer_retry(store, headers, status)
                        self.debug.update(last_result='config_http_error', skip_reason='config_http_error')
                        return
                    stage = 'config_parse'
                    enabled, rate, interval = parse_config(data)
                    self.debug.update(config_enabled=enabled, config_effective_enabled=enabled, last_result='config_valid')
                except Exception as error:
                    self._defer_retry(store)
                    self.debug.update(error_type=type(error).__name__, last_result=stage + '_error',
                                      skip_reason=stage + '_error')
                    return
                self.next_attempt = self.clock() + interval + random.uniform(0, 60)
                store.claim_round(0, self.next_attempt, force=True)
                self.debug.update(next_retry_at=self.next_attempt)
                if not enabled:
                    store.record_retry(0, self.next_attempt)
                    self.debug.update(failure_count=0, skip_reason='remote_disabled')
                    return
                identity = store.install_id
                bucket = int(hashlib.sha256(identity.encode()).hexdigest()[:8], 16) / 2**32
                self.debug.update(sampled=bucket < rate)
                if bucket >= rate:
                    self.debug.update(skip_reason='not_sampled')
                    return
                started = time.monotonic()
                for payload in store.snapshots()[:7]:
                    if not self.allowed() or time.monotonic() - started > 10:
                        self.debug.update(persist=self.allowed(), skip_reason=
                            'consent_or_stopped' if not self.allowed() else 'round_time_limit')
                        break
                    try:
                        stage = 'post_request'
                        self.debug.update(last_attempt=self.clock(), revision=payload['revision'],
                                          last_result='post_request', http_status=None)
                        status, headers, result = self.transport('POST', '/v1/telemetry/sync', payload)
                        self.debug.update(http_status=status, persist=self.allowed())
                    except Exception as error:
                        self._defer_retry(store)
                        self.debug.update(error_type=type(error).__name__,
                                          last_result='post_network_error', skip_reason='post_network_error')
                        break
                    if not self.allowed():
                        self.debug.update(persist=False, skip_reason='consent_or_stopped')
                        break
                    if (status == 200 and isinstance(result, dict) and result.get('success') is True
                            and result.get('snapshot_id') == payload['snapshot_id']
                            and type(result.get('revision')) is int
                            and result['revision'] == payload['revision']):
                        store.acknowledge(payload)
                        store.record_retry(0, self.next_attempt)
                        self.debug.update(failure_count=0, last_result='acknowledged', skip_reason=None,
                                          outbox_count=max(0, self.debug.state['outbox_count'] - 1))
                    elif status == 400:
                        store.acknowledge(payload)
                        self.debug.update(last_result='snapshot_rejected', skip_reason='snapshot_rejected',
                                          outbox_count=max(0, self.debug.state['outbox_count'] - 1))
                    else:
                        self._defer_retry(store, headers, status)
                        reason = 'invalid_ack' if status == 200 else 'post_http_error'
                        self.debug.update(last_result=reason, skip_reason=reason)
                        break
        except Exception as error:
            self.debug.update(persist=self.allowed(), error_type=type(error).__name__,
                              last_result='local_state_error', skip_reason='local_state_error')
            return

    def _run(self):
        # Recovery is deliberately delayed so startup/UI initialization never
        # waits on disk, DNS, TLS, or the remote service.
        self.debug.update(uploader_started=True, persist=False)
        if self.stopped.wait(self.startup_delay):
            return
        while not self.stopped.is_set():
            self.sync_once()
            self.stopped.wait(1)
