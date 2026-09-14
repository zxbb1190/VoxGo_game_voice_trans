import asyncio
from dataclasses import replace
import hashlib
import io
from pathlib import Path
import tempfile
import threading
import sys
from types import SimpleNamespace
import time
import unittest
from unittest.mock import patch, Mock

from voxgo.translation.base import TranslationConfig, TranslationRequest
from voxgo.translation.local import LocalTranslationProvider
from voxgo.translation import local_models as models


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = b"verified model content"
        self.file = models.ModelFile("model.bin", len(self.data), hashlib.sha256(self.data).hexdigest())
        self.model = models.LocalModel("Test", (models.ModelDirection("en-zh", "owner/model", "a" * 40, (self.file,)),))
        self.catalog = patch.dict(models.LOCAL_MODELS, {"test": self.model})
        self.catalog.start()
        self.addCleanup(self.catalog.stop)

    def response(self, data):
        response = io.BytesIO(data)
        response.geturl = lambda: "https://huggingface.co/model.bin"
        return response

    def test_atomic_download_and_offline_readiness(self):
        observed = []
        def progress(received, total):
            self.assertFalse(models.is_model_ready("test", self.root))
            observed.append((received, total))
        with patch.object(models.urllib.request.OpenerDirector, "open", return_value=self.response(self.data)) as fetch:
            path = models.download_model("test", progress, self.root)
            self.assertTrue(models.is_model_ready("test", self.root))
            self.assertEqual(path, self.root / "test")
            models.download_model("test", root=self.root)
            self.assertEqual(fetch.call_count, 1)
        self.assertEqual(observed[-1], (len(self.data), len(self.data)))
        # Same-size corruption must not count as installed.
        (path / "en-zh" / "model.bin").write_bytes(b"x" * len(self.data))
        self.assertFalse(models.is_model_ready("test", self.root))

    def test_bad_hash_never_publishes(self):
        with patch.object(models.urllib.request.OpenerDirector, "open", return_value=self.response(b"x" * len(self.data))):
            with self.assertRaisesRegex(ValueError, "checksum"):
                models.download_model("test", root=self.root)
        self.assertFalse((self.root / "test").exists())
        self.assertEqual(list(self.root.iterdir()), [])

    def test_oversized_download_is_rejected(self):
        with patch.object(models.urllib.request.OpenerDirector, "open", return_value=self.response(self.data + b"overflow")):
            with self.assertRaisesRegex(ValueError, "size"):
                models.download_model("test", root=self.root)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_path_traversal_id_rejected_without_network(self):
        with patch.object(models.urllib.request, "urlopen") as fetch:
            with self.assertRaises(ValueError):
                models.download_model("../outside", root=self.root)
            fetch.assert_not_called()

    def test_cancelled_progress_cleans_partial_download(self):
        def cancel(*args):
            raise RuntimeError("cancel")
        with patch.object(models.urllib.request.OpenerDirector, "open", return_value=self.response(self.data)):
            with self.assertRaisesRegex(RuntimeError, "cancel"):
                models.download_model("test", cancel, self.root)
        self.assertEqual(list(self.root.iterdir()), [])


class ProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_missing_model_never_downloads(self):
        with tempfile.TemporaryDirectory() as root:
            provider = LocalTranslationProvider(TranslationConfig(), model_root=root)
            self.assertFalse(provider.requires_api_key())
            with patch.object(models.urllib.request, "urlopen") as fetch:
                result = await provider.test()
            self.assertFalse(result.ok)
            self.assertIn("download", result.message)
            fetch.assert_not_called()

    async def test_inference_does_not_block_event_loop(self):
        provider = LocalTranslationProvider(TranslationConfig())
        entered = threading.Event()
        release = threading.Event()
        def translate(request, model_id=None):
            entered.set()
            release.wait(2)
            return "翻译"
        with patch.object(provider, "_translate_sync", side_effect=translate):
            task = asyncio.create_task(provider.translate(TranslationRequest("text", "en", "zh")))
            for _ in range(100):
                if entered.is_set():
                    break
                await asyncio.sleep(.005)
            self.assertTrue(entered.is_set())
            self.assertFalse(task.done())
            release.set()
            result = await task
            self.assertEqual(result.translated, "翻译")
            self.assertEqual(result.provider, "local")

    async def test_unsupported_direction_is_explicit(self):
        provider = LocalTranslationProvider(TranslationConfig())
        with self.assertRaisesRegex(ValueError, "English"):
            await provider.translate(TranslationRequest("bonjour", "fr", "zh"))

    async def test_snapshot_providers_reuse_loaded_engine(self):
        from voxgo.translation.local import _ENGINES
        _ENGINES.clear()
        self.addCleanup(_ENGINES.clear)
        translator = Mock()
        translator.translate_batch.return_value = [SimpleNamespace(hypotheses=[["translated"]])]
        ct2 = SimpleNamespace(Translator=Mock(return_value=translator))
        tokenizer = Mock()
        tokenizer.encode.return_value = ["hello"]
        tokenizer.decode.return_value = "你好"
        spm = SimpleNamespace(SentencePieceProcessor=Mock(return_value=tokenizer))
        with tempfile.TemporaryDirectory() as root, patch.dict(sys.modules, {"ctranslate2": ct2, "sentencepiece": spm}), patch("voxgo.translation.local.is_model_ready", return_value=True) as ready:
            for _ in range(3):
                provider = LocalTranslationProvider(TranslationConfig(), model_root=root)
                result = await provider.translate(TranslationRequest("hello", "en", "zh"))
                self.assertEqual(result.translated, "你好")
            self.assertEqual(ct2.Translator.call_count, 1)
            self.assertEqual(ready.call_count, 1)
            self.assertEqual(translator.translate_batch.call_count, 3)
            self.assertEqual(translator.translate_batch.call_args.args[0][0], [">>cmn_Hans<<", "hello", "</s>"])
            provider = LocalTranslationProvider(TranslationConfig(), model_root=root)
            await provider.translate(TranslationRequest("中文", "zh", "en"))
            self.assertEqual(translator.translate_batch.call_args.args[0][0], ["hello", "</s>"])
            tokenizer.encode.return_value = ["x"] * 255
            with self.assertRaisesRegex(ValueError, "too long"):
                await provider.translate(TranslationRequest("long", "en", "zh"))


    async def test_native_work_is_serialized_and_queue_bounded(self):
        provider = LocalTranslationProvider(TranslationConfig())
        entered = threading.Event()
        release = threading.Event()
        calls = []
        def translate(request, model_id=None):
            calls.append(request.text)
            entered.set()
            release.wait(2)
            return request.text
        with patch.object(provider, "_translate_sync", side_effect=translate):
            a = asyncio.create_task(provider.translate(TranslationRequest("a", "en", "zh")))
            while not entered.is_set():
                await asyncio.sleep(.005)
            b = asyncio.create_task(provider.translate(TranslationRequest("b", "en", "zh")))
            await asyncio.sleep(.01)
            with self.assertRaisesRegex(RuntimeError, "busy"):
                await provider.translate(TranslationRequest("c", "en", "zh"))
            self.assertEqual(calls, ["a"])
            release.set()
            await asyncio.gather(a, b)
            self.assertEqual(calls, ["a", "b"])


if __name__ == "__main__":
    unittest.main()
