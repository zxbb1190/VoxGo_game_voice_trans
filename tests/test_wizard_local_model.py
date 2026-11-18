"""Real Qt navigation with isolated model files and a controlled download worker."""
import hashlib
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from voxgo.config.loader import default_app_config
from voxgo.translation import local_models as models
from voxgo.ui.dialogs import FirstRunWizard
from voxgo.ui.download_panels import LocalModelRequiredDialog


class WizardLocalModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.data = b"test-only model bytes"
        model_file = models.ModelFile("model.bin", len(self.data), hashlib.sha256(self.data).hexdigest())
        model = models.LocalModel("Test", tuple(
            models.ModelDirection(direction, "owner/model", "a" * 40, (model_file,))
            for direction in ("en-zh", "zh-en")
        ))
        for mocked in (patch.dict(models.LOCAL_MODELS, {"opus-mt-en-zh": model}, clear=True),
                       patch.object(models, "default_model_root", return_value=self.root)):
            mocked.start()
            self.addCleanup(mocked.stop)
        self.config = default_app_config()
        self.config.app.language = "zh-CN"
        self.config.translation.provider = "local"
        self.wizard = FirstRunWizard(self.config.audio, self.config.translation, app_config=self.config.app)
        self.panel = self.wizard.wizard_local_model_panel
        self.wizard.show()
        self.wizard.next_button.click()
        self.assertEqual(self.wizard.stack.currentIndex(), 1)
        self.addCleanup(self.close_wizard)

    def close_wizard(self):
        self.wizard.reject()
        self.wizard.deleteLater()
        self.qt.processEvents()

    def write_model(self):
        for direction in ("en-zh", "zh-en"):
            path = self.root / "opus-mt-en-zh" / direction / "model.bin"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(self.data)

    def choose(self, action, before=None):
        observed = []

        def respond():
            dialog = self.qt.activeModalWidget()
            if isinstance(dialog, LocalModelRequiredDialog):
                observed.append((dialog.windowTitle(), dialog.message.text(),
                                 dialog.skip_button.text(), dialog.download_button.text()))
                if before:
                    before()
                if action == "escape":
                    QTest.keyClick(dialog, Qt.Key_Escape)
                elif action == "close":
                    dialog.close()
                else:
                    getattr(dialog, action + "_button").click()

        QTimer.singleShot(0, respond)
        self.wizard.next_button.click()
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0][2:], ("继续跳过", "下载模型"))
        return observed[0][1]

    def wait_until(self, predicate):
        deadline = time.monotonic() + 3
        while not predicate() and time.monotonic() < deadline:
            QTest.qWait(10)
        self.assertTrue(predicate(), "Download worker did not settle")

    def test_skip_advances_only_after_explicit_choice_and_rechecks_on_return(self):
        with patch.object(models, "download_model") as download:
            self.choose("skip")
            self.assertEqual(self.wizard.stack.currentIndex(), 2)
            self.assertFalse(self.config.app.setup_completed)
            self.assertEqual(self.config.translation.provider, "local")
            self.wizard.back_button.click()
            self.choose("close")
            self.assertEqual(self.wizard.stack.currentIndex(), 1)
            download.assert_not_called()

    def test_close_and_escape_neither_advance_nor_download(self):
        with patch.object(models, "download_model") as download:
            for action in ("close", "escape"):
                self.choose(action)
                self.assertEqual(self.wizard.stack.currentIndex(), 1)
                self.assertFalse(self.config.app.setup_completed)
            download.assert_not_called()

    def test_complete_model_and_online_providers_need_no_prompt(self):
        self.write_model()
        with patch.object(LocalModelRequiredDialog, "exec_", side_effect=AssertionError("Unexpected prompt")):
            self.wizard.next_button.click()
            self.assertEqual(self.wizard.stack.currentIndex(), 2)
            for provider in ("google", "openai_compatible"):
                self.wizard.back_button.click()
                self.wizard.wizard_api_key_input.setText("test-only-configured-key")
                self.wizard.wizard_provider_combo.setCurrentIndex(
                    self.wizard.wizard_provider_combo.findData(provider))
                with patch.object(models, "model_files_present", return_value=False):
                    self.wizard.next_button.click()
                self.assertEqual(self.wizard.stack.currentIndex(), 2)

    def test_partial_model_still_prompts(self):
        self.write_model()
        path = self.root / "opus-mt-en-zh" / "zh-en" / "model.bin"
        path.write_bytes(self.data[:3])
        self.choose("close")
        self.assertEqual(self.wizard.stack.currentIndex(), 1)
        path.unlink()
        self.choose("close")
        self.assertEqual(self.wizard.stack.currentIndex(), 1)

    def test_download_shows_progress_stays_on_page_and_never_starts_twice(self):
        entered, release = threading.Event(), threading.Event()

        def download(model_id, progress, source):
            entered.set()
            progress(10, 100)
            if not release.wait(3):
                raise TimeoutError("Test worker timed out")
            self.write_model()
            progress(100, 100)
            return self.root / model_id

        self.panel.source_combo.setCurrentIndex(self.panel.source_combo.findData("hf_mirror_net"))
        with patch.object(models, "download_model", side_effect=download) as fetch:
            try:
                self.choose("download")
                self.wait_until(lambda: entered.is_set() and self.panel.bar.value() == 10)
                self.assertEqual(self.wizard.stack.currentIndex(), 1)
                self.assertTrue(self.panel.bar.isVisible())
                self.assertFalse(self.panel.button.isEnabled())
                self.assertIn("模型正在下载", self.choose("download"))
                self.assertEqual(self.panel.bar.value(), 10)
                self.assertIn("10%", self.panel.status.text())
                fetch.assert_called_once()
                self.assertEqual(fetch.call_args.kwargs["source"], "hf_mirror_net")
                self.choose("skip")
                self.assertEqual(self.wizard.stack.currentIndex(), 2)
                self.assertTrue(self.panel.busy)
            finally:
                release.set()
                self.wait_until(lambda: not self.panel.busy)
        self.wizard.back_button.click()
        self.assertFalse(self.panel.bar.isVisible())
        with patch.object(LocalModelRequiredDialog, "exec_", side_effect=AssertionError("Unexpected prompt")):
            self.wizard.next_button.click()
        self.assertEqual(self.wizard.stack.currentIndex(), 2)

    def test_failed_download_keeps_page_and_allows_retry(self):
        with patch.object(models, "download_model", side_effect=OSError("connection failed")):
            self.choose("download")
            self.wait_until(lambda: not self.panel.busy)
        self.assertEqual(self.wizard.stack.currentIndex(), 1)
        self.assertTrue(self.panel.button.isEnabled())
        self.assertTrue(self.panel.source_combo.isEnabled())
        self.assertIn("失败", self.panel.status.text())

        def succeed(*args, **kwargs):
            self.write_model()
            return self.root / "opus-mt-en-zh"

        with patch.object(models, "download_model", side_effect=succeed) as fetch:
            self.choose("download")
            self.wait_until(lambda: not self.panel.busy)
            fetch.assert_called_once()
        self.assertEqual(self.wizard.stack.currentIndex(), 1)
        self.wizard.next_button.click()
        self.assertEqual(self.wizard.stack.currentIndex(), 2)

    def test_model_finished_while_prompt_open_does_not_restart_download(self):
        with patch.object(models, "download_model") as download:
            self.choose("download", before=self.write_model)
            download.assert_not_called()
        self.assertEqual(self.wizard.stack.currentIndex(), 1)
        self.wizard.next_button.click()
        self.assertEqual(self.wizard.stack.currentIndex(), 2)

    def test_prompt_is_localized_in_all_five_languages(self):
        messages = set()
        for language in ("zh-CN", "en-US", "ja-JP", "ko-KR", "ru-RU"):
            for downloading in (False, True):
                dialog = LocalModelRequiredDialog(language, downloading)
                self.assertTrue(dialog.download_button.isDefault())
                messages.add(dialog.message.text())
                dialog.deleteLater()
        self.assertEqual(len(messages), 10)
