import json
import tempfile
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from voxgo.analytics.client import AuthorizedAnalytics
from voxgo.analytics.consent import CONSENT_VERSION, may_upload


class RemoteConsentRuntimeTests(unittest.TestCase):
    def test_epoch_rotation_revocation_and_durable_gate(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch('voxgo.analytics.client.LocalAnalytics') as collector, \
                patch('voxgo.analytics.uploader.RemoteUploader') as uploader:
            root = Path(tmp)
            config = SimpleNamespace(telemetry_consent='unknown', telemetry_consent_version=0,
                                     telemetry_epoch='')
            analytics = AuthorizedAnalytics(root, '0.4.3', lambda: config)
            uploader.assert_not_called()
            config.telemetry_consent = 'allowed'
            config.telemetry_consent_version = CONSENT_VERSION
            config.telemetry_epoch = str(uuid.uuid4())
            analytics.refresh_consent()
            epoch = config.telemetry_epoch
            self.assertIsNone(analytics._remote_consent(epoch))
            (root / 'telemetry_consent.json').write_text(json.dumps(vars(config)))
            self.assertTrue(may_upload(analytics._remote_consent(epoch), True))
            # Another process revokes consent while our in-memory copy stays allowed.
            (root / 'telemetry_consent.json').write_text(json.dumps({'telemetry_consent': 'denied'}))
            self.assertIsNone(analytics._remote_consent(epoch))
            config.telemetry_consent = 'denied'
            config.telemetry_epoch = ''
            analytics.refresh_consent()
            self.assertIsNone(analytics.remote)
            uploader.return_value.stop.assert_called()
            config.telemetry_consent = 'allowed'
            config.telemetry_epoch = str(uuid.uuid4())
            analytics.refresh_consent()
            self.assertNotEqual(analytics._epoch, epoch)
            self.assertIsNone(analytics._remote_consent(epoch))
            analytics.stop()
            self.assertTrue(analytics._stopping)

    def test_getter_failure_is_fail_closed_and_local_events_continue(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch('voxgo.analytics.client.LocalAnalytics') as collector, \
                patch('voxgo.analytics.uploader.RemoteUploader') as uploader:
            def broken():
                raise OSError('settings unavailable')
            analytics = AuthorizedAnalytics(tmp, '0.4.3', broken)
            analytics.increment('translation_success')
            collector.return_value.increment.assert_called_with('translation_success', 1)
            uploader.assert_not_called()
            self.assertIsNone(analytics._remote_consent(str(uuid.uuid4())))
            analytics.stop()

    def test_regrant_does_not_count_a_second_application_start(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch('voxgo.analytics.client.LocalAnalytics') as collector, \
                patch('voxgo.analytics.uploader.RemoteUploader'):
            config = SimpleNamespace(telemetry_consent='allowed',
                telemetry_consent_version=CONSENT_VERSION, telemetry_epoch=str(uuid.uuid4()))
            analytics = AuthorizedAnalytics(tmp, '0.4.3', lambda: config)
            self.assertTrue(collector.call_args.kwargs['count_start'])
            config.telemetry_consent = 'denied'
            analytics.refresh_consent()
            config.telemetry_consent = 'allowed'
            config.telemetry_epoch = str(uuid.uuid4())
            analytics.refresh_consent()
            self.assertFalse(collector.call_args.kwargs['count_start'])
            analytics.stop()

    def test_shared_backend_hash_fixture(self):
        import hashlib
        fixture = Path(__file__).parent / 'fixtures' / 'telemetry-v1.json'
        payload = json.loads(fixture.read_text())
        expected = payload.pop('snapshot_id')
        actual = hashlib.sha256(json.dumps(payload, sort_keys=True,
            separators=(',', ':'), ensure_ascii=True).encode('ascii')).hexdigest()
        self.assertEqual(actual, expected)
