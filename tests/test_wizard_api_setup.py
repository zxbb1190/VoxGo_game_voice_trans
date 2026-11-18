"""Exercise the real wizard and modal choices without contacting a provider."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from voxgo.config.loader import default_app_config
from voxgo.translation.base import PLACEHOLDER_API_KEYS
from voxgo.ui.api_setup import ApiConfigurationRequiredDialog
from voxgo.ui.dialogs import FirstRunWizard


class WizardApiSetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self):
        self.config = default_app_config()
        self.config.app.language = "zh-CN"
        self.config.translation.provider = "openai_compatible"
        self.config.translation.api_key = ""
        self.wizard = FirstRunWizard(self.config.audio, self.config.translation, app_config=self.config.app)
        self.addCleanup(self.close_wizard)
        self.wizard.show()
        self.wizard.next_button.click()
        self.assertEqual(self.wizard.stack.currentIndex(), 1)
        self.runner_patch = patch("voxgo.ui.dialogs.TranslationTestRunner")
        self.runner = self.runner_patch.start()
        self.addCleanup(self.runner_patch.stop)
        self.addCleanup(self.runner.assert_not_called)

    def close_wizard(self):
        self.wizard.reject()
        self.wizard.deleteLater()
        self.qt.processEvents()

    def provider(self, name):
        self.wizard.wizard_provider_combo.setCurrentIndex(self.wizard.wizard_provider_combo.findData(name))

    def choose(self, action):
        observed = []

        def respond():
            dialog = self.qt.activeModalWidget()
            if isinstance(dialog, ApiConfigurationRequiredDialog):
                observed.append((dialog.skip_button.text(), dialog.configure_button.text()))
                if action == "escape":
                    QTest.keyClick(dialog, Qt.Key_Escape)
                elif action == "enter":
                    QTest.keyClick(dialog, Qt.Key_Return)
                elif action == "close":
                    dialog.close()
                else:
                    getattr(dialog, action + "_button").click()
            elif dialog is not None:
                dialog.reject()

        QTimer.singleShot(0, respond)
        self.wizard.next_button.click()
        self.qt.processEvents()
        self.assertEqual(observed, [("继续跳过", "配置 API")])

    def advance_without_prompt(self):
        with patch.object(ApiConfigurationRequiredDialog, "exec_", side_effect=AssertionError("Unexpected API prompt")):
            self.wizard.next_button.click()
        self.assertEqual(self.wizard.stack.currentIndex(), 2)

    def test_configure_keeps_page_focuses_key_and_entered_key_allows_next(self):
        self.choose("configure")
        self.assertEqual(self.wizard.stack.currentIndex(), 1)
        self.assertIs(self.wizard.focusWidget(), self.wizard.wizard_api_key_input)
        self.assertFalse(self.config.app.setup_completed)
        self.wizard.wizard_api_key_input.setText("  test-only-key  ")
        self.advance_without_prompt()
        self.assertEqual(self.config.translation.api_key, "test-only-key")

    def test_skip_explicitly_advances_and_rechecks_on_return(self):
        self.choose("skip")
        self.assertEqual(self.wizard.stack.currentIndex(), 2)
        self.assertEqual(self.config.translation.api_key, "")
        self.assertFalse(self.config.app.setup_completed)
        self.wizard.back_button.click()
        self.choose("configure")
        self.assertEqual(self.wizard.stack.currentIndex(), 1)

    def test_close_escape_and_default_enter_stay_on_configuration(self):
        for action in ("close", "escape", "enter"):
            with self.subTest(action=action):
                self.choose(action)
                self.assertEqual(self.wizard.stack.currentIndex(), 1)
                self.assertFalse(self.config.app.setup_completed)

    def test_empty_whitespace_and_template_keys_are_unconfigured_for_both_online_providers(self):
        for provider in ("google", "openai_compatible"):
            self.provider(provider)
            for key in PLACEHOLDER_API_KEYS | {"   "}:
                with self.subTest(provider=provider, key=key):
                    self.wizard.wizard_api_key_input.setText(key)
                    self.choose("configure")
                    self.assertEqual(self.wizard.stack.currentIndex(), 1)

    def test_missing_endpoint_or_model_focuses_that_field_instead_of_reusing_old_value(self):
        self.wizard.wizard_api_key_input.setText("test-only-key")
        for name in ("endpoint", "model"):
            field = getattr(self.wizard, "wizard_" + name + "_input")
            old = field.text()
            field.setText("  ")
            self.choose("configure")
            self.assertEqual(self.wizard.stack.currentIndex(), 1)
            self.assertIs(self.wizard.focusWidget(), field)
            self.assertEqual(getattr(self.config.translation, name), "")
            field.setText(old)
        self.wizard.wizard_endpoint_input.setText("http://[invalid")
        self.choose("configure")
        self.assertIs(self.wizard.focusWidget(), self.wizard.wizard_endpoint_input)

    def test_google_needs_key_even_with_local_endpoint_and_ignores_disabled_fields(self):
        self.provider("google")
        self.wizard.wizard_endpoint_input.setText("http://localhost:1234/v1")
        self.choose("configure")
        self.wizard.wizard_endpoint_input.clear()
        self.wizard.wizard_model_input.clear()
        self.wizard.wizard_api_key_input.setText("test-only-google-key")
        self.advance_without_prompt()

    def test_localhost_compatible_services_can_continue_without_key(self):
        for endpoint in ("http://localhost:1234/v1", "http://127.0.0.1:11434/v1", "http://[::1]:1234/v1"):
            with self.subTest(endpoint=endpoint):
                self.wizard.wizard_endpoint_input.setText(endpoint)
                self.advance_without_prompt()
                self.wizard.back_button.click()

    def test_local_translation_uses_only_model_gate(self):
        self.provider("local")
        with patch.object(self.wizard.wizard_local_model_panel, "confirm_before_continue", return_value=False) as gate:
            with patch.object(ApiConfigurationRequiredDialog, "exec_", side_effect=AssertionError("Unexpected API prompt")):
                self.wizard.next_button.click()
            gate.assert_called_once()
            self.assertEqual(self.wizard.stack.currentIndex(), 1)
        with patch.object(self.wizard.wizard_local_model_panel, "confirm_before_continue", return_value=True):
            self.advance_without_prompt()

    def test_all_five_languages_have_localized_safe_default_dialog(self):
        messages = set()
        buttons = set()
        for language in ("zh-CN", "en-US", "ja-JP", "ko-KR", "ru-RU"):
            dialog = ApiConfigurationRequiredDialog(language)
            self.assertFalse(dialog.windowFlags() & Qt.WindowContextHelpButtonHint)
            self.assertTrue(dialog.configure_button.isDefault())
            self.assertFalse(dialog.skip_button.autoDefault())
            messages.add(dialog.message.text())
            buttons.add(dialog.configure_button.text())
            dialog.deleteLater()
        self.assertEqual(len(messages), 5)
        self.assertEqual(len(buttons), 5)
