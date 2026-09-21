import json
import tempfile
import threading
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from voxgo.analytics.aggregation import AggregateStore
from voxgo.analytics.consent import CONSENT_VERSION
from voxgo.analytics.uploader import RemoteUploader, parse_config


class UploaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'remote'
        self.consent = SimpleNamespace(telemetry_consent='allowed',
                                       telemetry_consent_version=CONSENT_VERSION)
        self.config = dict(schema_version=1, telemetry_enabled=True,
                           telemetry_sample_rate=1.0, sync_interval_seconds=900)
        self.calls = []
        self.reply = lambda payload: (200, {}, {'success': True, 'snapshot_id': payload['snapshot_id'], 'revision': payload['revision']})
        self.now = 2000000000
        clock = patch('voxgo.analytics.uploader.time.time', side_effect=lambda: self.now)
        clock.start()
        self.addCleanup(clock.stop)
        jitter = patch('voxgo.analytics.uploader.random.uniform', return_value=0)
        jitter.start()
        self.addCleanup(jitter.stop)

    def transport(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if method == 'GET':
            return 200, {}, self.config
        return self.reply(payload)

    def uploader(self):
        return RemoteUploader(self.root, lambda: self.consent,
                              transport=self.transport, start=False)

    def test_startup_delay_is_bounded_and_stop_wakes_thread(self):
        self.write_shard()
        entered = threading.Event()
        uploader = RemoteUploader(self.root, lambda: self.consent,
                                  transport=lambda *args: (entered.set() or (200, {}, self.config)),
                                  startup_delay=2.0, start=True)
        try:
            self.assertFalse(entered.wait(0.2))
            uploader.stop()
            uploader.thread.join(1)
            self.assertFalse(uploader.thread.is_alive())
        finally:
            uploader.stop()

    def test_startup_delay_rejects_unsafe_values(self):
        with self.assertRaises(ValueError):
            self.uploader_with_delay(1.9)
        with self.assertRaises(ValueError):
            self.uploader_with_delay(5.1)

    def uploader_with_delay(self, delay):
        return RemoteUploader(self.root, lambda: self.consent,
                              transport=self.transport, start=False,
                              startup_delay=delay)

    def write_shard(self):
        day = datetime.now(timezone.utc).date().isoformat()
        path = self.root / 'shards' / str(uuid.uuid4()) / (day + '.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'schema_version': 1, 'date': day,
                                   'metrics': {'translation_success': 3}}))

    def pending(self):
        store = AggregateStore(self.root, '0.4.3')
        with store.lock() as acquired:
            self.assertTrue(acquired)
            return store.snapshots()

    def test_denied_unknown_and_old_consent_never_access_network_or_disk(self):
        for state, version in [('denied', CONSENT_VERSION), ('unknown', CONSENT_VERSION),
                               ('allowed', CONSENT_VERSION - 1)]:
            with self.subTest(state=state, version=version):
                self.consent.telemetry_consent = state
                self.consent.telemetry_consent_version = version
                self.uploader().sync_once()
                self.assertEqual(self.calls, [])
                self.assertFalse(self.root.exists())

    def test_remote_disabled_and_zero_sample_never_post(self):
        self.write_shard()
        self.config['telemetry_enabled'] = False
        self.uploader().sync_once()
        self.assertEqual([call[0] for call in self.calls], ['GET'])
        self.now += 901
        self.config.update(telemetry_enabled=True, telemetry_sample_rate=0)
        self.uploader().sync_once()
        self.assertEqual([call[0] for call in self.calls], ['GET', 'GET'])

    def test_success_acknowledges_exact_snapshot(self):
        self.write_shard()
        self.uploader().sync_once()
        self.assertEqual([call[0] for call in self.calls], ['GET', 'POST'])
        self.assertEqual(self.pending(), [])

    def test_wrong_ack_and_server_failure_retain_exact_retry(self):
        self.write_shard()
        self.reply = lambda payload: (200, {}, {'snapshot_id': 'wrong'})
        self.uploader().sync_once()
        first = self.calls[-1][2]
        self.assertEqual(self.pending(), [first])
        self.now += 901
        self.reply = lambda payload: (503, {}, {})
        self.uploader().sync_once()
        self.assertEqual(self.calls[-1][2], first)
        self.assertEqual(self.pending(), [first])

    def test_retry_schedule_survives_restart(self):
        self.write_shard()
        self.reply = lambda payload: (429, {'Retry-After': '3600'}, {})
        self.uploader().sync_once()
        original_calls = len(self.calls)
        self.now += 901
        self.uploader().sync_once()
        self.assertEqual(len(self.calls), original_calls)
        self.now += 2700
        self.uploader().sync_once()
        self.assertEqual(len(self.calls), original_calls + 2)

    def test_bad_request_is_not_retried_forever(self):
        self.write_shard()
        self.reply = lambda payload: (400, {}, {})
        self.uploader().sync_once()
        self.assertEqual(self.pending(), [])

    def test_stop_never_starts_request(self):
        uploader = self.uploader()
        uploader.stop()
        uploader.sync_once()
        self.assertEqual(self.calls, [])
        self.assertFalse(self.root.exists())

    def test_revocation_during_config_prevents_post(self):
        self.write_shard()
        def transport(method, path, payload=None):
            self.calls.append((method, path, payload))
            self.consent.telemetry_consent = 'denied'
            return 200, {}, self.config
        uploader = self.uploader()
        uploader.transport = transport
        uploader.sync_once()
        self.assertEqual([call[0] for call in self.calls], ['GET'])

    def test_network_exception_does_not_escape(self):
        uploader = self.uploader()
        uploader.transport = lambda *args: (_ for _ in ()).throw(TimeoutError())
        uploader.sync_once()
        self.assertGreater(uploader.next_attempt, self.now)

    def test_config_rejects_bad_types_ranges_and_missing_fields(self):
        self.assertEqual(parse_config(self.config), (True, 1.0, 900))
        for field, bad in [('schema_version', 2), ('telemetry_enabled', 1),
                           ('telemetry_sample_rate', True), ('telemetry_sample_rate', -1),
                           ('telemetry_sample_rate', float('nan')),
                           ('sync_interval_seconds', 899), ('sync_interval_seconds', 86401),
                           ('sync_interval_seconds', 900.0)]:
            with self.subTest(field=field, bad=bad):
                with self.assertRaises(ValueError):
                    parse_config(dict(self.config, **{field: bad}))
        for value in [None, [], {}, {'schema_version': 1}]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_config(value)

    def test_status_retry_classification_and_persistent_backoff(self):
        self.write_shard()
        for status, delay in [(500, 900), (502, 1800), (403, 21600), (429, 7200)]:
            self.reply = lambda payload, status=status: (status, {}, None)
            uploader = self.uploader()
            uploader.sync_once()
            self.assertGreaterEqual(uploader.next_attempt - self.now, delay)
            self.assertTrue(self.pending())
            self.now = uploader.next_attempt + 1

    def test_success_preserves_daily_baseline(self):
        self.write_shard()
        self.uploader().sync_once()
        state = json.loads((self.root / 'aggregate.json').read_text())
        entry = next(iter(state['days'].values()))
        self.assertIsNone(entry['pending'])
        self.assertEqual(entry['totals']['translation_success'], 3)
        self.assertTrue(entry['seen'])

    def test_consent_exception_is_fail_closed(self):
        uploader = self.uploader()
        uploader.consent_getter = lambda: (_ for _ in ()).throw(OSError())
        uploader.sync_once()
        self.assertFalse(self.calls)

    def test_stop_returns_while_network_is_blocked_and_prevents_post(self):
        import threading
        import time
        entered, release = threading.Event(), threading.Event()
        self.write_shard()
        uploader = self.uploader()
        def blocked(*args):
            self.calls.append(args)
            entered.set()
            release.wait(3)
            return 200, {}, self.config
        uploader.transport = blocked
        thread = threading.Thread(target=uploader.sync_once)
        thread.start()
        try:
            self.assertTrue(entered.wait(2))
            begin = time.monotonic()
            uploader.stop()
            self.assertLess(time.monotonic() - begin, .1)
            self.assertTrue(thread.is_alive())
        finally:
            release.set()
            thread.join(3)
        self.assertEqual(len(self.calls), 1)
