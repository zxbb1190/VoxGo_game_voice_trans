import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voxgo.asr.whisper_engine import WhisperConfig
from voxgo.config.schema import DebugConfig
from voxgo.i18n import UI_LANGUAGE_EN, UI_LANGUAGE_ZH
from voxgo.translation.base import TranslationConfig
from voxgo.ui.config_models import _build_feedback_report


class FeedbackReportTest(unittest.TestCase):
    def test_feedback_report_includes_recognition_runtime_metadata_in_chinese(self):
        report = _build_feedback_report(
            TranslationConfig(provider="openai_compatible", model="model-a", endpoint="https://example.com/v1"),
            WhisperConfig(device="cpu"),
            DebugConfig(enabled=True),
            "0.2.4",
            "C:/VoxGo",
            {
                "wait_ms": 12,
                "recognition_ms": 345,
                "translation_ms": 67,
                "overlay_ms": 8,
                "total_ms": 432,
                "latency_mode": "fast",
                "candidate_labels": "candidate,short_segment",
                "segment_voice_ms": 320,
                "segment_total_ms": 580,
                "whisper_model_size": "base.en",
                "whisper_device": "cpu",
                "whisper_compute_type": "int8",
                "whisper_cpu_threads": 4,
                "fast_path_allowed": True,
                "fast_path_ready": True,
            },
            "[系统声音] 耳机",
            UI_LANGUAGE_ZH,
        )

        self.assertIn("### 识别运行信息", report)
        self.assertIn("- 响应模式：fast", report)
        self.assertIn("- 候选标签：candidate,short_segment", report)
        self.assertIn("- 语音片段 / 总片段：320 ms / 580 ms", report)
        self.assertIn("- Whisper 模型：base.en", report)
        self.assertIn("- Whisper CPU 线程：4", report)
        self.assertIn("- 英文快路径允许：是", report)
        self.assertIn("- 英文快路径就绪：是", report)

    def test_feedback_report_includes_recognition_runtime_metadata_in_english(self):
        report = _build_feedback_report(
            TranslationConfig(provider="openai_compatible", model="model-a", endpoint="https://example.com/v1"),
            WhisperConfig(device="cpu"),
            DebugConfig(enabled=False),
            "0.2.4",
            "C:/VoxGo",
            {
                "latency_mode": "balanced",
                "candidate_labels": "candidate",
                "segment_voice_ms": 900,
                "segment_total_ms": 1200,
                "whisper_model_size": "small",
                "whisper_device": "cpu",
                "whisper_compute_type": "auto",
                "whisper_cpu_threads": 3,
                "fast_path_allowed": False,
                "fast_path_ready": False,
            },
            "Auto select",
            UI_LANGUAGE_EN,
        )

        self.assertIn("### Recognition Runtime", report)
        self.assertIn("- Response mode: balanced", report)
        self.assertIn("- Candidate labels: candidate", report)
        self.assertIn("- Segment voice / total: 900 ms / 1200 ms", report)
        self.assertIn("- Whisper model: small", report)
        self.assertIn("- Whisper CPU threads: 3", report)
        self.assertIn("- English fast path allowed: no", report)
        self.assertIn("- English fast path ready: no", report)


if __name__ == "__main__":
    unittest.main()
