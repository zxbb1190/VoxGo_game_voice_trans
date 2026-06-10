import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voxgo.asr.whisper_engine import (
    SpeechRecognizer,
    WhisperConfig,
    describe_model_download_source,
    format_model_download_error,
    normalize_model_download_endpoint,
    normalize_model_download_source,
)


class ModelDownloadConfigTest(unittest.TestCase):
    def test_model_download_endpoint_normalization(self):
        self.assertEqual(normalize_model_download_endpoint(""), "")
        self.assertEqual(normalize_model_download_endpoint("official"), "")
        self.assertEqual(normalize_model_download_endpoint("huggingface.co"), "")
        self.assertEqual(normalize_model_download_endpoint("hf-mirror"), "https://hf-mirror.com")
        self.assertEqual(normalize_model_download_endpoint("mirror.example.com"), "https://mirror.example.com")
        self.assertEqual(normalize_model_download_endpoint("https://mirror.example.com/"), "https://mirror.example.com")

    def test_model_download_source_label(self):
        self.assertEqual(normalize_model_download_source("", ""), "modelscope")
        self.assertEqual(normalize_model_download_source("modelscope", ""), "modelscope")
        self.assertEqual(normalize_model_download_source("huggingface", ""), "huggingface")
        self.assertEqual(
            normalize_model_download_source("custom_hf_endpoint", "https://mirror.example.com"),
            "custom_hf_endpoint",
        )
        self.assertEqual(describe_model_download_source("", ""), "ModelScope 国内源")
        self.assertEqual(describe_model_download_source("modelscope", ""), "ModelScope 国内源")
        self.assertEqual(describe_model_download_source("huggingface", ""), "官方 Hugging Face")
        self.assertEqual(
            describe_model_download_source("custom_hf_endpoint", "hf-mirror"),
            "自定义 Hugging Face Endpoint: hf-mirror.com",
        )
        self.assertEqual(
            describe_model_download_source("https://mirror.example.com"),
            "自定义 Hugging Face Endpoint: https://mirror.example.com",
        )

    def test_modelscope_urls_target_modelscope_repo(self):
        recognizer = SpeechRecognizer(WhisperConfig(model_size="small"))

        self.assertEqual(
            recognizer._modelscope_file_list_url("Systran/faster-whisper-small"),
            "https://www.modelscope.cn/api/v1/models/Systran/faster-whisper-small/repo/files?Revision=master",
        )
        self.assertEqual(
            recognizer._modelscope_resolve_url("Systran/faster-whisper-small", "model.bin"),
            "https://www.modelscope.cn/models/Systran/faster-whisper-small/resolve/master/model.bin",
        )

    def test_model_size_maps_to_faster_whisper_repo(self):
        recognizer = SpeechRecognizer(WhisperConfig(model_size="small"))

        self.assertEqual(recognizer._model_repo_id(), "Systran/faster-whisper-small")

    def test_english_model_size_maps_to_faster_whisper_repo(self):
        recognizer = SpeechRecognizer(WhisperConfig(model_size="small", active_model_size="small.en"))

        self.assertEqual(recognizer._model_repo_id(), "Systran/faster-whisper-small.en")

    def test_english_model_falls_back_to_configured_multilingual_model(self):
        recognizer = SpeechRecognizer(
            WhisperConfig(
                model_size="small",
                active_model_size="base.en",
                english_model_size="small.en",
                fast_english_model_size="base.en",
            )
        )

        self.assertEqual(recognizer._fallback_model_size("base.en"), "small")
        self.assertEqual(recognizer._fallback_model_size("small"), "")

    def test_custom_repo_id_is_used_directly(self):
        recognizer = SpeechRecognizer(WhisperConfig(model_size="example/faster-whisper-custom"))

        self.assertEqual(recognizer._model_repo_id(), "example/faster-whisper-custom")

    def test_snapshot_required_file_check(self):
        recognizer = SpeechRecognizer(WhisperConfig())
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot = Path(temp_dir)
            (snapshot / "config.json").write_text("{}", encoding="utf-8")
            (snapshot / "model.bin").write_bytes(b"model")

            self.assertFalse(recognizer._snapshot_has_required_model_files(str(snapshot)))

            (snapshot / "tokenizer.json").write_text("{}", encoding="utf-8")
            self.assertTrue(recognizer._snapshot_has_required_model_files(str(snapshot)))

    def test_download_error_includes_user_visible_context(self):
        message = format_model_download_error(
            TimeoutError("network timeout"),
            "Systran/faster-whisper-small",
            "官方 Hugging Face",
        )

        self.assertIn("模型下载失败", message)
        self.assertIn("Systran/faster-whisper-small", message)
        self.assertIn("官方 Hugging Face", message)
        self.assertIn("TimeoutError", message)

    def test_tqdm_progress_callback_receives_byte_progress(self):
        events = []
        recognizer = SpeechRecognizer(
            WhisperConfig(model_size="small"),
            download_progress_callback=events.append,
        )
        progress_cls = recognizer._progress_tqdm_class(
            "Systran/faster-whisper-small",
            "官方 Hugging Face",
        )

        progress = progress_cls(total=100, unit="B", unit_scale=True)
        progress.update(40)
        progress.close()

        self.assertTrue(any(event.total_bytes == 100 for event in events))
        self.assertTrue(any(event.downloaded_bytes == 40 for event in events))


if __name__ == "__main__":
    unittest.main()
