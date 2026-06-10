import asyncio
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voxgo.asr.pipeline import SpeechPipeline
from voxgo.asr.whisper_engine import TranscriptionResult, WhisperConfig
from voxgo.audio.capture import AudioConfig, SpeechSegment
from voxgo.config.schema import AppConfig
from voxgo.runtime.events import EventBus, TranscriptReady, TranslationReady
from voxgo.runtime.work_items import LatencyTrace, SpeechWorkItem
from voxgo.translation.base import TranslationConfig, TranslationResult
from voxgo.translation.runtime import TranslationRuntime


class FakeRecognizer:
    def transcribe_audio_bytes_with_language(self, audio_data, sample_rate, language_override=None):
        return TranscriptionResult("hello there", "en", 0.95)


class FakeTranslator:
    def __init__(self):
        self.closed = False
        self.config = TranslationConfig(source_lang="en", target_lang="zh")
        self.calls = []
        self.config_calls = []

    async def translate_result(self, text, detected_language=""):
        self.calls.append((text, detected_language))
        return TranslationResult(
            translated="translated",
            source_lang=detected_language or "en",
            target_lang="zh",
            provider="fake",
        )

    async def translate_result_with_config(self, text, detected_language="", config=None):
        self.calls.append((text, detected_language))
        self.config_calls.append((text, detected_language, config.source_lang, config.target_lang))
        return TranslationResult(
            translated="translated",
            source_lang=config.source_lang,
            target_lang=config.target_lang,
            provider="fake",
        )

    async def close(self):
        self.closed = True

    def clear_context(self):
        pass


class RuntimeServicesTest(unittest.TestCase):
    def test_latency_trace_summary_includes_recognition_runtime_metadata(self):
        trace = LatencyTrace(
            "translation-1",
            speech_detected_at=1.0,
            queued_at=1.1,
            latency_mode="fast",
            candidate_labels=("candidate", "short_segment"),
            segment_voice_seconds=0.32,
            segment_total_seconds=0.58,
            whisper_model_size="base.en",
            whisper_device="cpu",
            whisper_compute_type="int8",
            whisper_cpu_threads=4,
            fast_path_allowed=True,
            fast_path_ready=True,
            dequeued_at=1.2,
            transcription_started_at=1.2,
            transcription_finished_at=1.7,
            translation_started_at=1.7,
            translation_finished_at=1.9,
            overlay_updated_at=2.0,
        )

        summary = trace.summary_ms()

        self.assertEqual(summary["wait_ms"], 100)
        self.assertEqual(summary["latency_mode"], "fast")
        self.assertEqual(summary["candidate_labels"], "candidate,short_segment")
        self.assertEqual(summary["segment_voice_ms"], 320)
        self.assertEqual(summary["segment_total_ms"], 580)
        self.assertEqual(summary["whisper_model_size"], "base.en")
        self.assertEqual(summary["whisper_device"], "cpu")
        self.assertEqual(summary["whisper_compute_type"], "int8")
        self.assertEqual(summary["whisper_cpu_threads"], 4)
        self.assertTrue(summary["fast_path_allowed"])
        self.assertTrue(summary["fast_path_ready"])

    def test_speech_pipeline_publishes_transcript_ready(self):
        config = AppConfig(
            audio=AudioConfig(min_segment_seconds=0.0),
            whisper=WhisperConfig(language="en"),
            translation=TranslationConfig(source_lang="en", target_lang="zh"),
        )
        bus = EventBus()
        seen = []
        stats = {
            "speech_detected": 0,
            "filtered_speech": 0,
            "dropped_speech": 0,
            "errors": 0,
        }
        latency_traces = {}
        next_ids = iter(["translation-1"])
        pipeline = SpeechPipeline(
            lambda: config,
            lambda: FakeRecognizer(),
            bus,
            stats,
            lambda: True,
            lambda: False,
            lambda: next(next_ids),
            latency_traces,
            lambda *args: None,
            lambda: 7,
        )
        bus.subscribe(TranscriptReady, seen.append)

        segment = SpeechSegment(
            audio_data=b"\x01\x00" * 1600,
            sample_rate=16000,
            duration_seconds=0.1,
            voice_duration_seconds=0.1,
            block_count=1,
            voice_blocks=1,
            peak_rms_dbfs=-20.0,
            energy_threshold_dbfs=-40.0,
            noise_floor_dbfs=None,
            reason="test",
        )
        pipeline._process(
            SpeechWorkItem(
                segment=segment,
                trace=LatencyTrace("translation-1", 1.0, 1.0),
            )
        )

        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].text, "hello there")
        self.assertEqual(seen[0].trace_id, "translation-1")
        self.assertEqual(seen[0].language_probability, 0.95)
        self.assertEqual(seen[0].source_lang, "en")
        self.assertEqual(seen[0].target_lang, "zh")
        self.assertEqual(seen[0].language_revision, 7)
        self.assertIn("translation-1", latency_traces)

    def test_translation_runtime_publishes_translation_ready(self):
        bus = EventBus()
        seen = []
        stats = {"errors": 0}
        latency_traces = {"translation-1": LatencyTrace("translation-1", 1.0, 1.0)}
        runtime = TranslationRuntime(bus, stats, latency_traces, lambda: None)
        runtime.client = FakeTranslator()
        bus.subscribe(TranslationReady, seen.append)

        asyncio.run(
            runtime._translate_and_publish(
                "translation-1",
                "hello",
                "en",
                latency_traces["translation-1"],
            )
        )

        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].translated, "translated")
        self.assertEqual(seen[0].source_lang, "en")
        self.assertGreater(latency_traces["translation-1"].translation_finished_at, 0)

    def test_translation_runtime_skips_high_confidence_language_mismatch(self):
        bus = EventBus()
        seen = []
        stats = {"errors": 0}
        latency_traces = {"translation-1": LatencyTrace("translation-1", 1.0, 1.0)}
        runtime = TranslationRuntime(bus, stats, latency_traces, lambda: None)
        translator = FakeTranslator()
        translator.config = TranslationConfig(source_lang="en", target_lang="zh")
        runtime.client = translator
        bus.subscribe(TranslationReady, seen.append)

        asyncio.run(
            runtime._translate_and_publish(
                "translation-1",
                "\u4f60\u597d",
                "zh",
                latency_traces["translation-1"],
                0.95,
            )
        )

        self.assertEqual(seen, [])
        self.assertEqual(translator.calls, [])
        self.assertEqual(stats["skipped_translations"], 1)
        self.assertNotIn("translation-1", latency_traces)

    def test_translation_runtime_allows_low_confidence_language_mismatch(self):
        bus = EventBus()
        seen = []
        stats = {"errors": 0}
        latency_traces = {"translation-1": LatencyTrace("translation-1", 1.0, 1.0)}
        runtime = TranslationRuntime(bus, stats, latency_traces, lambda: None)
        translator = FakeTranslator()
        translator.config = TranslationConfig(source_lang="en", target_lang="zh")
        runtime.client = translator
        bus.subscribe(TranslationReady, seen.append)

        asyncio.run(
            runtime._translate_and_publish(
                "translation-1",
                "rush B",
                "zh",
                latency_traces["translation-1"],
                0.50,
            )
        )

        self.assertEqual(len(seen), 1)
        self.assertEqual(translator.calls, [("rush B", "zh")])

    def test_translation_runtime_uses_language_snapshot(self):
        bus = EventBus()
        seen = []
        stats = {"errors": 0, "skipped_translations": 0}
        trace = LatencyTrace(
            "translation-1",
            1.0,
            1.0,
            source_lang="zh",
            target_lang="en",
            language_revision=3,
        )
        latency_traces = {"translation-1": trace}
        runtime = TranslationRuntime(bus, stats, latency_traces, lambda: None)
        runtime.set_language_revision_getter(lambda: 3)
        translator = FakeTranslator()
        runtime.client = translator
        bus.subscribe(TranslationReady, seen.append)

        asyncio.run(
            runtime._translate_and_publish(
                "translation-1",
                "\u4f60\u597d",
                "zh",
                trace,
                0.95,
                "zh",
                "en",
                3,
            )
        )

        self.assertEqual(translator.config_calls, [("\u4f60\u597d", "zh", "zh", "en")])
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].source_lang, "zh")
        self.assertEqual(seen[0].target_lang, "en")
        self.assertEqual(seen[0].language_revision, 3)

    def test_translation_runtime_snapshot_preserves_local_cache_settings(self):
        bus = EventBus()
        stats = {"errors": 0, "skipped_translations": 0}
        runtime = TranslationRuntime(bus, stats, {}, lambda: None)
        translator = FakeTranslator()
        translator.config = TranslationConfig(
            source_lang="en",
            target_lang="zh",
            enable_local_phrase_cache=False,
            local_phrase_cache={"en:zh": {"test": "x"}},
        )
        runtime.client = translator

        snapshot = runtime._config_snapshot("en", "zh")

        self.assertFalse(snapshot.enable_local_phrase_cache)
        self.assertEqual(snapshot.local_phrase_cache, {"en:zh": {"test": "x"}})

    def test_translation_runtime_drops_stale_language_revision(self):
        bus = EventBus()
        seen = []
        stats = {"errors": 0, "skipped_translations": 0}
        trace = LatencyTrace(
            "translation-1",
            1.0,
            1.0,
            source_lang="en",
            target_lang="zh",
            language_revision=1,
        )
        latency_traces = {"translation-1": trace}
        runtime = TranslationRuntime(bus, stats, latency_traces, lambda: None)
        runtime.set_language_revision_getter(lambda: 2)
        translator = FakeTranslator()
        runtime.client = translator
        bus.subscribe(TranslationReady, seen.append)

        asyncio.run(
            runtime._translate_and_publish(
                "translation-1",
                "hello",
                "en",
                trace,
                0.95,
                "en",
                "zh",
                1,
            )
        )

        self.assertEqual(seen, [])
        self.assertEqual(translator.calls, [])
        self.assertEqual(translator.config_calls, [])
        self.assertEqual(stats["skipped_translations"], 1)
        self.assertNotIn("translation-1", latency_traces)


if __name__ == "__main__":
    unittest.main()
