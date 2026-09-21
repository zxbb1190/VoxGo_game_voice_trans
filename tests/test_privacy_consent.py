import os
import uuid
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PyQt5.QtWidgets import QApplication, QMessageBox
from voxgo.analytics.consent import may_upload, CONSENT_VERSION
from voxgo.config.loader import default_app_config, save_user_settings, load_user_settings
from voxgo.ui.config_models import _copy_runtime_config
from voxgo.ui.settings_dialog import SettingsDialog
from voxgo.ui.dialogs import FirstRunWizard


class PrivacyConsentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def test_default_denied_invalid_and_old_consent_fail_closed(self):
        config = default_app_config().app
        for state in ('unknown', 'denied', 'invalid', True):
            config.telemetry_consent = state
            config.telemetry_consent_version = CONSENT_VERSION
            self.assertFalse(may_upload(config, True))
        config.telemetry_consent = 'allowed'
        self.assertFalse(may_upload(config))
        self.assertTrue(may_upload(config, True))
        config.telemetry_consent_version = 0
        self.assertFalse(may_upload(config, True))

    def test_explicit_allow_cancel_and_revoke_persist(self):
        config = default_app_config()
        dialog = SettingsDialog(config.overlay, config.hotkeys, app_config=config.app)
        try:
            self.assertFalse(dialog.telemetry_consent_check.isChecked())
            with patch('voxgo.ui.telemetry_consent.confirm_telemetry', return_value=QMessageBox.No):
                dialog.telemetry_consent_check.click()
            self.assertEqual(dialog.app_config.telemetry_consent, 'unknown')
            with patch('voxgo.ui.telemetry_consent.confirm_telemetry', return_value=QMessageBox.Yes):
                dialog.telemetry_consent_check.click()
            self.assertTrue(may_upload(dialog.app_config, True))
            first_epoch = dialog.app_config.telemetry_epoch
            self.assertEqual(str(uuid.UUID(first_epoch)), first_epoch)
            dialog.telemetry_consent_check.click()
            self.assertEqual(dialog.app_config.telemetry_consent, 'denied')
            self.assertEqual(dialog.app_config.telemetry_epoch, '')
            with patch('voxgo.ui.telemetry_consent.confirm_telemetry', return_value=QMessageBox.Yes):
                dialog.telemetry_consent_check.click()
            self.assertNotEqual(dialog.app_config.telemetry_epoch, first_epoch)
            dialog.telemetry_consent_check.click()
            config.app = _copy_runtime_config(dialog.app_config)
            with tempfile.TemporaryDirectory() as folder:
                save_user_settings(config, Path(folder))
                loaded = default_app_config()
                load_user_settings(loaded, Path(folder))
            self.assertEqual(loaded.app.telemetry_consent, 'denied')
            self.assertEqual(loaded.app.telemetry_epoch, '')
            self.assertFalse(may_upload(loaded.app, True))
        finally:
            dialog.close()

    def test_first_run_optional_explicit_consent(self):
        config = default_app_config()
        wizard = FirstRunWizard(None, translation_config=config.translation, app_config=config.app)
        try:
            self.assertTrue(wizard.wizard_telemetry_check.isChecked())
            with patch('voxgo.ui.telemetry_consent.confirm_telemetry', return_value=QMessageBox.Yes):
                wizard._complete_setup()
            self.assertTrue(may_upload(wizard.app_config, True))
            epoch = wizard.app_config.telemetry_epoch
            self.assertEqual(str(uuid.UUID(epoch)), epoch)
            config.app = _copy_runtime_config(wizard.app_config)
            with tempfile.TemporaryDirectory() as folder:
                save_user_settings(config, Path(folder))
                loaded = default_app_config()
                load_user_settings(loaded, Path(folder))
            self.assertEqual(loaded.app.telemetry_epoch, epoch)
        finally:
            wizard.close()

    def test_stale_process_save_cannot_restore_revoked_consent(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first = default_app_config()
            first.app.telemetry_consent = 'allowed'
            first.app.telemetry_consent_version = CONSENT_VERSION
            first.app.telemetry_epoch = str(uuid.uuid4())
            first.app._telemetry_consent_changed = True
            save_user_settings(first, root)
            stale = default_app_config()
            load_user_settings(stale, root)
            first.app.telemetry_consent = 'denied'
            first.app.telemetry_epoch = ''
            first.app._telemetry_consent_changed = True
            save_user_settings(first, root)
            save_user_settings(stale, root)  # unrelated save still has old allowed epoch
            loaded = default_app_config()
            load_user_settings(loaded, root)
            self.assertEqual(loaded.app.telemetry_consent, 'denied')
            self.assertFalse(may_upload(loaded.app, True))
