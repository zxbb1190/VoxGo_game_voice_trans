import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication
from voxgo.config.loader import default_app_config, save_user_settings, load_config
from voxgo.translation import TranslationConfig
from voxgo.ui.config_models import _copy_translation_config
from voxgo.ui.dialogs import FirstRunWizard, UpdatePromptDialog
from voxgo.ui.settings_dialog import SettingsDialog
from voxgo.ui.download_panels import UpdateInstallPanel, LocalModelPanel
from voxgo.update.checker import UpdateInfo


class UpdateOfflineUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_local_selection_disables_cloud_credentials_and_preserves_cloud_values(self):
        config = default_app_config()
        cloud_model = config.translation.model
        dialog = SettingsDialog(config.overlay, config.hotkeys, translation_config=config.translation)
        try:
            dialog.provider_combo.setCurrentIndex(dialog.provider_combo.findData("local"))
            self.assertFalse(dialog.local_model_panel.isHidden())
            self.assertFalse(dialog.api_key_input.isEnabled())
            self.assertFalse(dialog.endpoint_input.isEnabled())
            self.assertEqual(config.translation.provider, "local")
            self.assertEqual(config.translation.model, cloud_model)
            dialog.provider_combo.setCurrentIndex(dialog.provider_combo.findData("openai_compatible"))
            self.assertTrue(dialog.api_key_input.isEnabled())
            self.assertTrue(dialog.local_model_panel.isHidden())
        finally:
            dialog.close()

    def test_wizard_can_select_offline_without_api_key(self):
        config = TranslationConfig()
        wizard = FirstRunWizard(None, translation_config=config)
        try:
            wizard.wizard_provider_combo.setCurrentIndex(wizard.wizard_provider_combo.findData("local"))
            wizard._collect_translation_values()
            self.assertEqual(config.provider, "local")
            self.assertFalse(wizard.wizard_local_model_panel.isHidden())
            self.assertFalse(wizard.wizard_api_key_input.isEnabled())
        finally:
            wizard._completed = True
            wizard.close()

    def test_local_config_survives_copy_and_disk_roundtrip(self):
        config = default_app_config()
        config.translation.provider = "local"
        config.translation.local_model = "opus-mt-en-zh"
        self.assertEqual(_copy_translation_config(config.translation).local_model, "opus-mt-en-zh")
        with tempfile.TemporaryDirectory() as directory:
            save_user_settings(config, Path(directory))
            loaded = load_config(runtime_dir=Path(directory))
        self.assertEqual(loaded.translation.provider, "local")
        self.assertEqual(loaded.translation.local_model, "opus-mt-en-zh")

    def test_update_download_does_not_exit_and_install_handoff_does(self):
        shutdown = []
        with patch("voxgo.update.installer.auto_update_supported", return_value=True):
            panel = UpdateInstallPanel(UpdateInfo(latest="9.0.0"), "en-US", lambda: shutdown.append(True))
        try:
            prepared = object()
            panel._finished(prepared)
            self.assertIs(panel.prepared, prepared)
            self.assertEqual(shutdown, [])
            self.assertEqual(panel.button.text(), "Install and Restart")
            panel.installing = True
            panel._failed("Unable to start helper")
            self.assertEqual(shutdown, [])
            self.assertFalse(panel.installing)
            panel.installing = True
            panel._finished(object())
            self.assertEqual(shutdown, [True])
        finally:
            panel.close()

    def test_source_mode_has_no_install_action(self):
        with patch("voxgo.update.installer.auto_update_supported", return_value=False):
            panel = UpdateInstallPanel(UpdateInfo(latest="9.0.0"), "en-US", lambda: None)
        self.assertFalse(panel.button.isEnabled())
        panel.close()

    def test_downloaded_model_still_offers_integrity_repair(self):
        with patch("voxgo.translation.local_models.model_files_present", return_value=True):
            panel = LocalModelPanel(TranslationConfig(), "en-US")
        self.assertTrue(panel.button.isEnabled())
        self.assertEqual(panel.button.text(), "Verify / Repair Model")
        panel.close()

    def test_dismissing_prepared_update_cleans_staging_but_not_after_handoff(self):
        dialog = UpdatePromptDialog(UpdateInfo(latest="9.0.0"), "0.4.1", lambda version: None)
        prepared = Mock()
        dialog.install_panel.prepared = prepared
        dialog.reject()
        prepared.cleanup.assert_called_once()
        dialog.install_panel.prepared = prepared
        dialog.install_panel.installing = True
        dialog.reject()
        prepared.cleanup.assert_called_once()


if __name__ == "__main__":
    unittest.main()
