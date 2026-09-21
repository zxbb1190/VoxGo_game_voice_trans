import json
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from voxgo.analytics.aggregation import AggregateStore
from voxgo.analytics.consent import CONSENT_VERSION
from voxgo.analytics.debug import AnalyticsDebug
from voxgo.analytics.uploader import RemoteUploader


class AnalyticsDebugTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.now = 2000000000
        self.calls = []
        self.config = dict(schema_version=1, telemetry_enabled=True,
                           telemetry_sample_rate=1, sync_interval_seconds=900)
        self.consent = SimpleNamespace(telemetry_consent='allowed',
                                       telemetry_consent_version=CONSENT_VERSION)
        day = datetime.now(timezone.utc).date().isoformat()
        shard = self.root / 'shards' / str(uuid.uuid4()) / (day + '.json')
        shard.parent.mkdir(parents=True)
        shard.write_text(json.dumps(dict(schema_version=1, date=day,
                                        metrics={'app_starts': 1})))

    def transport(self, method, path, payload=None):
        self.calls.append(method)
        if method == 'GET':
            return 200, {}, self.config
        return 200, {}, dict(success=True, revision=payload['revision'],
                            snapshot_id=payload['snapshot_id'])

    def uploader(self, transport=None):
        return RemoteUploader(self.root, lambda: self.consent, start=False,
                              clock=lambda: self.now, transport=transport or self.transport)

    def state(self):
        return json.loads((self.root / 'debug-state.json').read_text())

    def test_persisted_gate_reports_actual_deadline_without_network(self):
        store = AggregateStore(self.root, '0.4.3')
        with store.lock():
            store.snapshots()
            store.record_retry(2, self.now + 10000)
        self.uploader().sync_once()
        state = self.state()
        self.assertEqual(state['skip_reason'], 'persisted_retry_not_due')
        self.assertEqual(state['next_retry_at'], self.now + 10000)
        self.assertEqual(state['failure_count'], 2)
        self.assertEqual(state['outbox_count'], 1)
        self.assertTrue(state['daily_snapshot_exists'])
        self.assertEqual(self.calls, [])

    def test_config_branches_and_exact_ack_have_local_evidence(self):
        for enabled, rate, reason in [(False, 1, 'remote_disabled'),
                                      (True, 0, 'not_sampled'),
                                      (True, 1, None)]:
            self.now += 100000
            self.config.update(telemetry_enabled=enabled, telemetry_sample_rate=rate)
            self.uploader().sync_once()
            state = self.state()
            self.assertEqual(state['skip_reason'], reason)
            self.assertEqual(state['config_enabled'], enabled)
        self.assertEqual(self.state()['last_result'], 'acknowledged')
        self.assertEqual(self.state()['outbox_count'], 0)
        self.assertEqual(self.calls, ['GET', 'GET', 'GET', 'POST'])

    def test_exception_message_never_recorded(self):
        def broken(*args):
            raise OSError('secret API key and translated text')
        self.uploader(broken).sync_once()
        state = self.state()
        self.assertEqual(state['error_type'], 'OSError')
        self.assertEqual(state['skip_reason'], 'config_request_error')
        self.assertNotIn('secret', json.dumps(state))

    def test_debug_failure_cannot_prevent_upload(self):
        (self.root / 'debug-state.json').mkdir()
        self.uploader().sync_once()
        self.assertEqual(self.calls, ['GET', 'POST'])

    def test_whitelist_bounded_file_and_no_epoch_recreation(self):
        debug = AnalyticsDebug(self.root)
        debug.update(payload='secret', error_type='/sensitive/path',
                     last_result='ok', revision=5)
        self.assertNotIn('payload', self.state())
        self.assertIsNone(self.state()['error_type'])
        self.assertLess((self.root / 'debug-state.json').stat().st_size, 4096)
        missing = self.root / 'removed_epoch'
        AnalyticsDebug(missing).update(last_result='ok')
        self.assertFalse(missing.exists())


if __name__ == '__main__':
    unittest.main()
