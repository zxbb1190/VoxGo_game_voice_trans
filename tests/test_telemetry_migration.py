import json
import tempfile
import subprocess
import sys
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from voxgo.analytics.migration import initialize_telemetry_v2
from voxgo.config.loader import default_app_config, load_config, save_user_settings
from voxgo.ui.config_models import _copy_runtime_config
from voxgo.update.installer import PRESERVE_PATHS

class TelemetryMigrationTests(unittest.TestCase):
    def test_new_install_identity_is_durable_and_first_day_immutable(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first = default_app_config()
            initialize_telemetry_v2(first, root, datetime(2026, 9, 23, tzinfo=timezone.utc))
            self.assertEqual(first.app.telemetry_install_origin, 'new_install')
            self.assertEqual(first.app.telemetry_consent, 'unknown')
            self.assertEqual(first.app.full_telemetry_source, 'new_install_pending')
            seed = first.app.basic_install_seed
            other = default_app_config()
            initialize_telemetry_v2(other, root, datetime(2026, 9, 24, tzinfo=timezone.utc))
            self.assertEqual(other.app.basic_install_seed, seed)
            self.assertEqual(other.app.basic_first_run_date, '2026-09-23')
            stale = default_app_config()
            save_user_settings(stale, root)
            self.assertEqual(json.loads((root/'user_settings.json').read_text())['app']['basic_install_seed'], seed)
            self.assertEqual(_copy_runtime_config(other.app).basic_install_seed, seed)

    def test_historical_upgrade_recovers_valid_settings_without_old_remote_files(self):
        for state in ('allowed', 'denied', 'unknown'):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                epoch = str(uuid.uuid4()) if state == 'allowed' else ''
                (root/'user_settings.json').write_text(json.dumps({'app': {'setup_completed': True, 'telemetry_consent': state, 'telemetry_consent_version': 3, 'telemetry_epoch': epoch}}))
                config = load_config(runtime_dir=root)
                self.assertEqual(config.app.telemetry_install_origin, 'historical_install')
                self.assertEqual(config.app.basic_first_run_date, '')
                self.assertEqual(config.app.telemetry_consent, state)
                self.assertEqual(config.app.telemetry_epoch, epoch)
                self.assertEqual(config.app.full_telemetry_source, 'migration_'+state)
                self.assertTrue((root/'telemetry_consent.json').exists())

    def test_existing_revocation_or_corrupt_authority_wins(self):
        for authority in ('corrupt', json.dumps({'telemetry_consent': 'denied', 'telemetry_consent_version': 3, 'telemetry_epoch': ''})):
            with tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root/'user_settings.json').write_text(json.dumps({'app': {'telemetry_consent': 'allowed', 'telemetry_consent_version': 3, 'telemetry_epoch': str(uuid.uuid4())}}))
                (root/'telemetry_consent.json').write_text(authority)
                config = load_config(runtime_dir=root)
                self.assertNotEqual(config.app.telemetry_consent, 'allowed')

    def test_invalid_legacy_grants_and_corrupt_settings_never_become_new(self):
        for payload in ('broken', json.dumps({'app': {'telemetry_consent': 'allowed', 'telemetry_consent_version': 3, 'telemetry_epoch': 'bad'}}), json.dumps({'app': {'telemetry_consent': 'allowed', 'telemetry_consent_version': True, 'telemetry_epoch': str(uuid.uuid4())}})):
            with tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root/'user_settings.json').write_text(payload)
                config = load_config(runtime_dir=root)
                self.assertEqual(config.app.telemetry_install_origin, 'historical_install')
                self.assertEqual(config.app.telemetry_consent, 'unknown')

    def test_failed_persistence_does_not_expose_a_seed(self):
        with tempfile.TemporaryDirectory() as folder:
            config = default_app_config()
            with patch('voxgo.analytics.migration.atomic_json', side_effect=OSError('disk unavailable')):
                initialize_telemetry_v2(config, Path(folder))
            self.assertFalse(config.app.telemetry_v2_migrated)
            self.assertEqual(config.app.basic_install_seed, '')

    def test_update_preserves_telemetry_state(self):
        for path in ('user_settings.json', 'telemetry_consent.json', 'analytics', 'analytics-remote', 'analytics-basic'):
            self.assertIn(path, PRESERVE_PATHS)

    def test_concurrent_initialization_creates_one_installation(self):
        with tempfile.TemporaryDirectory() as folder:
            # Isolate migration from large ASR / Torch imports in each test child.
            script = """
from pathlib import Path
import sys
from types import SimpleNamespace
from voxgo.analytics.migration import initialize_telemetry_v2
from unittest.mock import patch
config = SimpleNamespace(app=SimpleNamespace(setup_completed=False, telemetry_consent='unknown'))
serializer = SimpleNamespace(serialize_user_settings=lambda c: {'app': vars(c.app).copy()})
with patch.dict(sys.modules, {'voxgo.config.loader': serializer}):
    initialize_telemetry_v2(config, Path(sys.argv[1]))
print(config.app.basic_install_seed)
"""
            processes = [subprocess.Popen([sys.executable, '-c', script, folder], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace') for _ in range(3)]
            seeds = []
            results = [process.communicate(timeout=30) for process in processes]
            for process, (out, err) in zip(processes, results):
                self.assertEqual(process.returncode, 0, err)
                seeds.append(out.strip())
            self.assertTrue(seeds[0])
            self.assertEqual(len(set(seeds)), 1)
            app = json.loads((Path(folder)/'user_settings.json').read_text())['app']
            self.assertIs(app['setup_completed'], False)
            self.assertEqual(app['telemetry_install_origin'], 'new_install')

    def test_old_denial_remains_denial_and_external_config_is_historical(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'user_settings.json').write_text(json.dumps({'app': {'telemetry_consent': 'denied', 'telemetry_consent_version': 2, 'telemetry_epoch': ''}}))
            config = load_config(runtime_dir=root)
            self.assertEqual(config.app.telemetry_consent, 'denied')
            self.assertEqual(config.app.telemetry_consent_version, 2)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            external = root/'config.json'
            external.write_text('{}')
            self.assertEqual(load_config(str(external), root).app.telemetry_install_origin, 'historical_install')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            bundled = root/'_internal/config.json'
            bundled.parent.mkdir()
            bundled.write_text('{}')
            self.assertEqual(load_config(str(bundled), root).app.telemetry_install_origin, 'new_install')

    def test_corrupt_other_section_does_not_reset_completed_setup(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'user_settings.json').write_text(json.dumps({'audio': 5, 'app': {'setup_completed': True}}))
            config = load_config(runtime_dir=root)
            self.assertIs(config.app.setup_completed, True)
            self.assertIs(json.loads((root/'user_settings.json').read_text())['app']['setup_completed'], True)

    def test_corrupt_v2_identity_never_rewrites_first_date(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = {'app': {'basic_install_seed': 'damaged', 'basic_first_run_date': '2026-09-20',
                            'telemetry_v2_migrated': True, 'telemetry_install_origin': 'new_install'}}
            (root/'user_settings.json').write_text(json.dumps(data))
            config = load_config(runtime_dir=root)
            self.assertFalse(config.app.telemetry_v2_migrated)
            self.assertEqual(config.app.basic_install_seed, '')
            self.assertTrue(save_user_settings(config, root))
            saved = json.loads((root/'user_settings.json').read_text())['app']
            self.assertEqual(saved['basic_first_run_date'], '2026-09-20')
            self.assertEqual(saved['basic_install_seed'], 'damaged')

    def test_contended_revocation_reports_not_saved_and_keeps_intent(self):
        from voxgo.analytics.aggregation import CrossProcessLock
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config = default_app_config()
            config.app.telemetry_consent = 'allowed'
            config.app.telemetry_consent_version = 3
            config.app.telemetry_epoch = str(uuid.uuid4())
            config.app._telemetry_consent_changed = True
            self.assertTrue(save_user_settings(config, root))
            config.app.telemetry_consent = 'denied'
            config.app.telemetry_epoch = ''
            config.app._telemetry_consent_changed = True
            with CrossProcessLock(root/'.telemetry-settings.lock') as held:
                self.assertTrue(held)
                self.assertFalse(save_user_settings(config, root))
            self.assertEqual(config.app._telemetry_save_error, 'consent_not_saved')
            self.assertTrue(config.app._telemetry_consent_changed)
            self.assertEqual(json.loads((root/'telemetry_consent.json').read_text())['telemetry_consent'], 'allowed')
            self.assertTrue(save_user_settings(config, root))
            self.assertEqual(json.loads((root/'telemetry_consent.json').read_text())['telemetry_consent'], 'denied')
