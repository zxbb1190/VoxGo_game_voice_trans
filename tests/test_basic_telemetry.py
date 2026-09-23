import json
import tempfile
import threading
import time
import unittest
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from voxgo.analytics.basic import (BasicTelemetry, BasicStore, daily_identity,
                                   canonical_hash, installation_state)


class BasicTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.now = datetime(2026, 9, 23, 12, tzinfo=timezone.utc).timestamp()
        self.seed = str(uuid.uuid4())
        self.app = dict(basic_install_seed=self.seed, basic_first_run_date='2026-09-23',
            telemetry_v2_migrated=True, setup_completed=False,
            telemetry_consent='unknown', telemetry_consent_version=0, telemetry_epoch='',
            full_telemetry_source='new_install_pending')
        self.write()
        self.config = dict(schema_version=1, telemetry_enabled=False,
            basic_telemetry_enabled=True, telemetry_sample_rate=0, sync_interval_seconds=900)
        self.calls = []
        self.reply = lambda p: (200, {}, self.ack(p))
        self.uploader = self.make()

    def write(self):
        (self.root / 'user_settings.json').write_text(json.dumps({'app': self.app}), encoding='utf-8')
        (self.root / 'telemetry_consent.json').write_text(json.dumps({k: self.app[k] for k in
            ('telemetry_consent', 'telemetry_consent_version', 'telemetry_epoch', 'full_telemetry_source')}), encoding='utf-8')

    def ack(self, p, disposition='stored'):
        return dict(success=True, disposition=disposition,
                    **{k: p[k] for k in ('daily_id', 'date', 'revision', 'snapshot_id')})

    def transport(self, method, path, payload=None):
        self.calls.append((method, path, deepcopy(payload)))
        return (200, {}, self.config) if method == 'GET' else self.reply(payload)

    def make(self, **kwargs):
        return BasicTelemetry(self.root, '0.5.1', transport=self.transport, start=False,
                              clock=lambda: self.now, package_type='lite', **kwargs)

    def run_round(self):
        self.now += 1000
        self.uploader.sync_once()

    def test_daily_identity_rotates_without_sending_seed(self):
        a = daily_identity(self.seed, '2026-09-23')
        self.assertEqual(a, daily_identity(self.seed, '2026-09-23'))
        self.assertNotEqual(a, daily_identity(self.seed, '2026-09-24'))
        self.assertNotEqual(a, daily_identity(str(uuid.uuid4()), '2026-09-23'))
        self.uploader.sync_once()
        p = self.calls[-1][2]
        self.assertNotIn(self.seed, json.dumps(p))
        self.assertNotIn('telemetry_epoch', p)
        self.assertEqual(p['snapshot_id'], canonical_hash(p))

    def test_basic_runs_with_full_off_and_sample_zero_once_per_day(self):
        self.uploader.sync_once()
        self.assertEqual([c[0] for c in self.calls], ['GET', 'POST'])
        self.assertFalse(self.calls[-1][2]['full_telemetry'])
        for _ in range(5):
            self.run_round()
        self.assertEqual(len(self.calls), 2)
        self.make().sync_once()
        self.assertEqual(len(self.calls), 2)

    def test_state_change_new_revision_and_same_state_no_revision(self):
        self.uploader.sync_once()
        self.app.update(setup_completed=True, telemetry_consent='allowed',
                        telemetry_consent_version=3, telemetry_epoch=str(uuid.uuid4()),
                        full_telemetry_source='new_install_default')
        self.write()
        self.run_round()
        self.assertEqual(self.calls[-1][2]['revision'], 2)
        self.assertTrue(self.calls[-1][2]['full_telemetry'])
        self.app.update(telemetry_consent='denied', telemetry_epoch='', full_telemetry_source='user_disabled')
        self.write()
        self.run_round()
        self.assertEqual(self.calls[-1][2]['revision'], 3)
        self.assertFalse(self.calls[-1][2]['full_telemetry'])
        self.assertTrue(self.calls[-1][2]['setup_completed'])

    def test_version_and_package_changes_refresh_same_day(self):
        self.uploader.sync_once()
        self.uploader.version = '0.5.2'
        self.uploader.package = 'full'
        self.run_round()
        self.assertEqual(self.calls[-1][2]['revision'], 2)
        self.assertEqual(self.calls[-1][2]['package_type'], 'full')

    def test_new_day_independent_revision_and_not_first_run(self):
        self.uploader.sync_once()
        old = self.calls[-1][2]
        self.now += 86400
        self.uploader.sync_once()
        new = self.calls[-1][2]
        self.assertNotEqual(old['daily_id'], new['daily_id'])
        self.assertEqual(new['revision'], 1)
        self.assertFalse(new['first_run'])

    def test_failure_retry_is_persistent_and_state_change_cannot_bypass(self):
        self.reply = lambda p: (429, {'Retry-After': '3600'}, {})
        self.uploader.sync_once()
        saved = self.uploader.store.load()
        self.assertGreaterEqual(saved['next_attempt'], self.now + 3600)
        self.app['setup_completed'] = True
        self.write()
        self.run_round()
        self.make().sync_once()
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.uploader.store.load()['days']['2026-09-23']['snapshot']['revision'], 2)

    def test_bad_ack_or_http_retains_pending(self):
        for field, bad in [('daily_id', '0'*64), ('date', '2026-09-22'), ('revision', True),
                           ('snapshot_id', '0'*64), ('disposition', 'unknown')]:
            with self.subTest(field=field):
                self.reply = lambda p: (200, {}, {**self.ack(p), field: bad})
                self.now += 86400
                self.uploader.sync_once()
                self.assertTrue(all(e['pending'] for e in self.uploader.store.load()['days'].values()))

    def test_superseded_ack_clears_only_matching_payload(self):
        store = self.uploader.store
        fields = installation_state(self.root, '0.5.1', 'lite', '2026-09-23')
        state = store.load()
        store.refresh(state, fields)
        old = deepcopy(state['days']['2026-09-23']['snapshot'])
        store.refresh(state, {**fields, 'setup_completed': True})
        self.assertFalse(store.acknowledge(state, old, self.ack(old)))
        latest = state['days']['2026-09-23']['snapshot']
        self.assertTrue(store.acknowledge(state, latest, self.ack(latest, 'superseded')))

    def test_config_absent_false_or_invalid_never_posts(self):
        for value in (False, None, 'true'):
            self.config['basic_telemetry_enabled'] = value
            self.now += 86400
            self.uploader.sync_once()
        self.assertTrue(all(c[0] == 'GET' for c in self.calls))

    def test_unpersisted_migration_or_corrupt_state_never_networks(self):
        self.app['telemetry_v2_migrated'] = False
        self.write()
        self.uploader.sync_once()
        self.assertFalse(self.calls)

    def test_corrupt_full_authority_cannot_disable_basic(self):
        (self.root / 'telemetry_consent.json').write_text('{broken', encoding='utf-8')
        self.uploader.sync_once()
        self.assertEqual(self.calls[-1][0], 'POST')
        self.assertFalse(self.calls[-1][2]['full_telemetry'])
        self.assertEqual(self.calls[-1][2]['full_telemetry_source'], 'unknown')

    def test_partial_authority_cannot_reuse_stale_allowed_settings(self):
        self.app.update(telemetry_consent='allowed', telemetry_consent_version=3,
                        telemetry_epoch=str(uuid.uuid4()), full_telemetry_source='user_enabled')
        self.write()
        (self.root / 'telemetry_consent.json').write_text('{}', encoding='utf-8')
        self.uploader.sync_once()
        self.assertEqual(self.calls[-1][0], 'POST')
        self.assertFalse(self.calls[-1][2]['full_telemetry'])
        self.assertEqual(self.calls[-1][2]['full_telemetry_source'], 'unknown')

    def test_shared_wire_fixtures_have_identical_canonical_hashes(self):
        for name in ('telemetry-basic-v1.json', 'telemetry-v2.json'):
            with self.subTest(name=name):
                payload = json.loads((Path(__file__).parent / 'fixtures' / name).read_text(encoding='utf-8'))
                self.assertEqual(payload['snapshot_id'], canonical_hash(payload))

    def test_real_migration_uploads_before_wizard_and_persists_revoke(self):
        from voxgo.config.loader import load_config, save_user_settings
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config = load_config(runtime_dir=root)
            # This test uses the real migration's UTC date, not a synthetic first date.
            stamp = datetime.now(timezone.utc).timestamp()
            uploader = BasicTelemetry(root, '0.5.1', transport=self.transport,
                start=False, package_type='lite', clock=lambda: stamp)
            uploader.sync_once()
            self.assertTrue(self.calls[-1][2]['first_run'])
            self.assertFalse(self.calls[-1][2]['setup_completed'])
            config.app.setup_completed = True
            config.app.telemetry_consent = 'allowed'
            config.app.telemetry_consent_version = 3
            config.app.telemetry_epoch = str(uuid.uuid4())
            config.app.full_telemetry_source = 'new_install_default'
            config.app._telemetry_consent_changed = True
            save_user_settings(config, root)
            stamp += 1000
            uploader.sync_once()
            self.assertTrue(self.calls[-1][2]['full_telemetry'])
            config.app.telemetry_consent = 'denied'
            config.app.telemetry_epoch = ''
            config.app.full_telemetry_source = 'user_disabled'
            config.app._telemetry_consent_changed = True
            save_user_settings(config, root)
            stamp += 1000
            uploader.sync_once()
            self.assertFalse(self.calls[-1][2]['full_telemetry'])
            self.assertEqual(self.calls[-1][2]['revision'], 3)

    def test_corrupt_basic_state_never_networks(self):
        self.app['telemetry_v2_migrated'] = True
        self.write()
        self.uploader.store.root.mkdir(parents=True, exist_ok=True)
        self.uploader.store.path.write_text('{bad', encoding='utf-8')
        self.run_round()
        self.assertFalse(self.calls)

    def test_tampered_pending_extra_fields_never_leave_machine(self):
        self.reply = lambda p: (500, {}, {})
        self.uploader.sync_once()
        state = self.uploader.store.load()
        payload = state['days']['2026-09-23']['snapshot']
        payload['extra'] = 'should not leave disk'
        payload['snapshot_id'] = canonical_hash(payload)
        self.uploader.store.save(state)
        self.calls.clear()
        self.run_round()
        self.assertFalse(self.calls)

    def test_cross_process_uploader_lock_prevents_duplicate_requests(self):
        with self.uploader.store.lock() as acquired:
            self.assertTrue(acquired)
            self.uploader.sync_once()
        self.assertFalse(self.calls)
        self.run_round()
        self.assertEqual(len(self.calls), 2)

    def test_stop_during_get_prevents_post_and_returns_without_waiting(self):
        entered, release = threading.Event(), threading.Event()
        def blocking(*args):
            entered.set()
            release.wait(3)
            return 200, {}, self.config
        self.uploader.transport = blocking
        thread = threading.Thread(target=self.uploader.sync_once)
        thread.start()
        self.assertTrue(entered.wait(2))
        start = time.monotonic()
        self.uploader.stop()
        self.assertLess(time.monotonic() - start, .1)
        release.set()
        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertTrue(self.uploader.store.load()['days']['2026-09-23']['pending'])

    def test_retention_keeps_seven_days_even_offline(self):
        self.reply = lambda p: (503, {}, {})
        for _ in range(10):
            self.uploader.sync_once()
            self.now += 86400
        self.assertEqual(len(self.uploader.store.load()['days']), 7)


if __name__ == '__main__':
    unittest.main()
