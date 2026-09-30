import json
import threading
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from loguru import logger

from scripts.run_asr_benchmark import (
    capture_segments,
    load_manifest,
    render_html,
    score_record,
    summarize,
    word_errors,
    Case,
    main,
    run,
    _segment_diagnostic,
)


class RunAsrBenchmarkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logger.disable("voxgo.audio.capture")

    @classmethod
    def tearDownClass(cls):
        logger.enable("voxgo.audio.capture")

    def test_word_errors_counts_and_normalizes_punctuation(self):
        self.assertEqual(word_errors("I'm reloading, rotate B!", "im reloading rotate b"),
                         {"reference_words": 4, "substitutions": 0,
                          "deletions": 0, "insertions": 0, "errors": 0})
        self.assertEqual(word_errors("Two on B at 12 o'clock", "2 on B at twelve oclock")["errors"], 0)
        self.assertEqual(word_errors("one hp behind you", "one behind"),
                         {"reference_words": 4, "substitutions": 0,
                          "deletions": 2, "insertions": 0, "errors": 2})
        self.assertEqual(word_errors("[noise] rotate B [disfluency]", "rotate B")["errors"], 0)

    def test_report_separates_literal_and_normalized_wer_and_prompt_leakage(self):
        case = Case("numbers", "natural", Path("n.wav"), "two on B", "test")
        row = score_record(case, "base.en", "fast", "off", "whole",
                           "2 on B", 0.1, 1, "cpu", "int8")
        self.assertGreater(row["errors"], 0)
        self.assertEqual(row["normalized_errors"], 0)
        group = next(item for item in summarize([row]) if item["subset"] == "all")
        self.assertGreater(group["wer"], group["normalized_wer"])
        game = Case("game", "game", Path("g.wav"), "rotate B", "test")
        leaked = score_record(game, "small.en", "balanced", "game_en", "whole",
                              "rotate B HP GG NT WP mid", 0.1, 1, "cpu", "int8")
        self.assertTrue(leaked["prompt_leakage"])

    def test_manifest_rejects_missing_audio_and_duplicate_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "clip.wav"
            with wave.open(str(audio), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b"\0\0" * 100)
            row = {"id": "a", "category": "game", "audio": "clip.wav",
                   "reference": "rotate B", "source": "test"}
            manifest = root / "manifest.jsonl"
            manifest.write_text(json.dumps(row) + "\n", encoding="utf-8")
            self.assertEqual(load_manifest(manifest)[0].audio, audio.resolve())
            manifest.write_text(json.dumps(row) + "\n" + json.dumps(row), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_manifest(manifest)
            row["audio"] = "missing.wav"
            manifest.write_text(json.dumps(row), encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                load_manifest(manifest)

    def test_capture_replay_splits_at_current_max_duration(self):
        rate = 16000
        samples = (np.sin(np.arange(rate * 7) * 2 * np.pi * 330 / rate) * 12000).astype(np.int16)
        segments = capture_segments(samples, "fast")
        self.assertGreaterEqual(len(segments), 2)
        self.assertTrue(all(seg.sample_rate == rate for seg in segments))
        self.assertTrue(all(seg.duration_seconds <= 3.0 for seg in segments))

    def test_summary_weights_words_and_html_escapes_transcripts(self):
        case_a = Case("a", "game", Path("a.wav"), "one hp", "test")
        case_b = Case("b", "game", Path("b.wav"), "behind you now", "test")
        rows = [score_record(case_a, "base.en", "fast", "off", "whole", "one", 1, 1, "cpu", "int8"),
                score_record(case_b, "base.en", "fast", "off", "whole", "behind you now", 2, 1, "cpu", "int8")]
        summary = summarize(rows)
        self.assertEqual(summary[0]["wer"], 1 / 5)
        self.assertEqual(summary[0]["deletion_rate"], 1 / 5)
        self.assertEqual(summary[0]["exact_hit_rate"], 0.5)
        rows[1]["hypothesis"] = "behind you now<script>"
        page = render_html(summary, rows, [], {"created_at": "now", "cases": 2})
        self.assertNotIn("now<script>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_noise_summary_keeps_snr_levels_separate(self):
        rows = []
        for snr in (0, 10):
            case = Case(f"noise-{snr}", "noise", Path(f"{snr}.wav"),
                        "hold the point", "test", snr_db=snr)
            rows.append(score_record(case, "base.en", "fast", "off", "whole",
                                     "hold the point", 0.5, 1, "cpu", "int8"))
        self.assertEqual({row["snr_db"] for row in summarize(rows)}, {0, 10})

    def test_runaway_and_abnormal_output_metrics_use_raw_text(self):
        case = Case("loop", "game", Path("loop.wav"), "rotate B", "test")
        raw = " ".join(["one two three four five"] * 8)
        row = score_record(
            case, "base.en", "balanced", "game_en", "capture_cut", "",
            1.0, 1, "cpu", "int8", raw_hypothesis=raw, runaway_guarded=True,
            segment_diagnostics=[{"duration_seconds": 2.0}],
        )
        self.assertTrue(row["abnormal_length"])
        self.assertFalse(row["repetition_failure"])
        self.assertTrue(row["raw_repetition_failure"])
        self.assertTrue(row["runaway_guarded"])
        self.assertEqual(row["output_words"], 0)
        self.assertEqual(row["raw_output_words"], 40)
        self.assertEqual(row["output_reference_length_ratio"], 0)
        self.assertEqual(row["raw_output_reference_length_ratio"], 20)
        group = next(group for group in summarize([row]) if group["subset"] == "all")
        self.assertEqual(group["repetition_failure_count"], 0)
        self.assertEqual(group["repetition_failure_rate"], 0)
        self.assertEqual(group["raw_repetition_failure_count"], 1)
        self.assertEqual(group["abnormal_length_count"], 1)
        self.assertEqual(group["max_output_reference_length_ratio"], 20)
        self.assertEqual(group["p50_inference_seconds"], 1)
        self.assertEqual(group["p95_inference_seconds"], 1)
        self.assertEqual(group["average_segment_count"], 1)
        self.assertEqual(group["average_segment_duration_seconds"], 2)

    def test_segment_diagnostics_capture_audio_vad_prompt_and_whisper_stats(self):
        result = SimpleNamespace(text="rotate B", raw_text="rotate B raw",
                                 runaway_guarded=False, compression_ratio=1.2,
                                 avg_logprob=-0.1, no_speech_prob=0.03)
        capture_segment = SimpleNamespace(peak_rms_dbfs=-12.0,
                                          voice_duration_seconds=0.08,
                                          vad_confidence=0.5,
                                          energy_voice_blocks=1,
                                          block_count=2)
        config = SimpleNamespace(beam_size=1, vad_filter=False,
                                 condition_on_previous_text=False, temperature=0,
                                 compression_ratio_threshold=2.4,
                                 no_speech_threshold=0.6, log_prob_threshold=-1,
                                 prompt_profile="game_en")
        diagnostic = _segment_diagnostic(
            b"\x00\x00" * 1600, result, 2, 1.25, "game_en", config,
            capture_segment=capture_segment, inference_seconds=0.37,
        )
        self.assertEqual(diagnostic["emitted_start_seconds"], 1.25)
        self.assertEqual(diagnostic["emitted_end_seconds"], 1.35)
        self.assertEqual(diagnostic["duration_seconds"], 0.1)
        self.assertEqual(diagnostic["timing_basis"], "emitted_audio_cumulative")
        self.assertFalse(diagnostic["source_offset_available"])
        self.assertIsNotNone(diagnostic["rms_dbfs"])
        self.assertEqual(diagnostic["vad_speech_ratio"], 0.5)
        self.assertEqual(diagnostic["prompt"], "game_en")
        self.assertEqual(diagnostic["config"]["condition_on_previous_text"], False)
        self.assertEqual(diagnostic["raw_text"], "rotate B raw")
        self.assertEqual(diagnostic["guarded_text"], "rotate B")
        self.assertEqual(diagnostic["compression_ratio"], 1.2)
        self.assertEqual(diagnostic["avg_logprob"], -0.1)
        self.assertEqual(diagnostic["no_speech_prob"], 0.03)
        self.assertEqual(diagnostic["inference_seconds"], 0.37)

    def test_run_scores_whole_and_capture_cut_for_each_prompt(self):
        class FakeConfig(SimpleNamespace):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        class FakeRecognizer:
            def __init__(self, config):
                self.config = config
                self._loaded_model_size = ""
                self.runtime_device = "cpu"
                self.runtime_compute_type = "int8"

            def initialize(self):
                self._loaded_model_size = self.config.model_size

            def transcribe_audio_bytes_with_language(self, chunk, sample_rate, language_override):
                self_outer.assertEqual(sample_rate, 16000)
                self_outer.assertEqual(language_override, "en")
                return SimpleNamespace(text="rotate B")

            def cleanup(self):
                pass

        self_outer = self
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "clip.wav"
            pcm = (np.sin(np.arange(16000) * 2 * np.pi * 330 / 16000) * 12000).astype(np.int16)
            with wave.open(str(wav), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(pcm.tobytes())
            case = Case("a", "game", wav, "rotate B", "synthetic")
            records, failures = run([case], ["base.en"], ["fast"], ["off", "game_en"],
                                    "cpu", "int8", False, FakeRecognizer, FakeConfig, {"fast": 1},
                                    paths=("whole", "capture_cut"))
        self.assertEqual(failures, [])
        self.assertEqual(len(records), 4)
        self.assertEqual({row["path"] for row in records}, {"whole", "capture_cut"})
        self.assertEqual({row["prompt"] for row in records}, {"off", "game_en"})
        whole = next(row for row in records if row["path"] == "whole")
        self.assertEqual(len(whole["segment_diagnostics"]), 1)
        self.assertEqual(whole["segment_diagnostics"][0]["timing_basis"], "source_audio")
        self.assertTrue(whole["segment_diagnostics"][0]["source_offset_available"])
        self.assertEqual(whole["segment_diagnostics"][0]["guarded_text"], "rotate B")
        capture_cut = next(row for row in records if row["path"] == "capture_cut")
        self.assertGreaterEqual(capture_cut["segments"], 1)
        self.assertEqual(len(capture_cut["segment_diagnostics"]), capture_cut["segments"])

    def test_full_pipeline_uses_real_pipeline_and_records_post_filter_output(self):
        recognition_threads = []

        class FakeConfig(SimpleNamespace):
            pass

        class FakeRecognizer:
            def __init__(self, config):
                self.config = config
                self._loaded_model_size = ""
                self.runtime_device = "cpu"
                self.runtime_compute_type = "int8"

            def initialize(self):
                self._loaded_model_size = self.config.model_size

            def transcribe_audio_bytes_with_language(self, chunk, sample_rate, language_override):
                recognition_threads.append(threading.current_thread().name)
                return SimpleNamespace(
                    text="rotate B", raw_text="rotate B", language="en",
                    language_probability=0.99, avg_logprob=-0.1,
                    no_speech_prob=0.01, compression_ratio=1.0,
                    runaway_guarded=False,
                )

            def cleanup(self):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "clip.wav"
            pcm = (np.sin(np.arange(16000 * 2) * 2 * np.pi * 330 / 16000) * 12000).astype(np.int16)
            with wave.open(str(wav), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(pcm.tobytes())
            case = Case("a", "game", wav, "rotate B", "synthetic")
            records, failures = run(
                [case], ["base.en"], ["fast"], ["off"], "cpu", "int8", False,
                FakeRecognizer, FakeConfig, {"fast": 1},
                paths=("whole", "capture_cut", "full_pipeline"),
            )
        self.assertEqual(failures, [])
        self.assertEqual({row["path"] for row in records},
                         {"whole", "capture_cut", "full_pipeline"})
        full = next(row for row in records if row["path"] == "full_pipeline")
        self.assertGreaterEqual(full["capture_segment_count"], 1)
        self.assertEqual(full["pipeline_stats"]["speech_detected"], full["capture_segment_count"])
        self.assertEqual(full["hypothesis"], "rotate B")
        self.assertEqual(full["normalized_errors"], 0)
        self.assertEqual(full["segments"], len(full["segment_diagnostics"]))
        self.assertIn("speech-worker", recognition_threads)

    def test_summary_includes_balanced_corpus_and_four_subsets(self):
        rows = []
        for subset in ("normal", "game", "longer", "number_direction_place"):
            case = Case(subset, "game", Path(f"{subset}.wav"), "rotate B", "synthetic",
                        subset=subset)
            rows.append(score_record(case, "small.en", "fast", "game_en", "whole",
                                     "rotate B", 1.0, 1, "cpu", "int8"))
        groups = summarize(rows)
        self.assertEqual({group["subset"] for group in groups},
                         {"all", "normal", "game", "longer", "number_direction_place"})
        self.assertEqual(next(group for group in groups if group["subset"] == "all")["cases"], 4)

    def test_run_skips_matching_records_when_resuming(self):
        class FakeConfig(SimpleNamespace):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        calls = []

        class FakeRecognizer:
            def __init__(self, config):
                self.config = config
                self._loaded_model_size = ""
                self.runtime_device = "cpu"
                self.runtime_compute_type = "int8"

            def initialize(self):
                self._loaded_model_size = self.config.model_size

            def transcribe_audio_bytes_with_language(self, chunk, sample_rate, language_override):
                calls.append(1)
                return SimpleNamespace(text="rotate B")

            def cleanup(self):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "clip.wav"
            pcm = (np.sin(np.arange(16000) * 2 * np.pi * 330 / 16000) * 12000).astype(np.int16)
            with wave.open(str(wav), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(pcm.tobytes())
            case = Case("a", "game", wav, "rotate B", "synthetic")
            existing = [score_record(case, "base.en", "fast", "off", "whole",
                                     "rotate B", 0.5, 1, "cpu", "int8", cpu_threads=1)]
            records, failures = run([case], ["base.en"], ["fast"], ["off"],
                                    "cpu", "int8", False, FakeRecognizer, FakeConfig,
                                    {"fast": 1}, existing_records=existing,
                                    paths=("whole", "capture_cut"))
        self.assertEqual(failures, [])
        self.assertEqual(len(records), 2)
        self.assertEqual(len(calls), 1)

    def test_fast_and_balanced_use_distinct_cpu_thread_policies(self):
        class FakeConfig(SimpleNamespace):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        calls = []

        class FakeRecognizer:
            def __init__(self, config):
                self.config = config
                self._loaded_model_size = ""
                self.runtime_device = "cpu"
                self.runtime_compute_type = "int8"

            def initialize(self):
                self._loaded_model_size = self.config.model_size

            def transcribe_audio_bytes_with_language(self, chunk, sample_rate, language_override):
                calls.append(1)
                return SimpleNamespace(text="rotate B")

            def cleanup(self):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "clip.wav"
            pcm = (np.sin(np.arange(16000) * 2 * np.pi * 330 / 16000) * 12000).astype(np.int16)
            with wave.open(str(wav), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(pcm.tobytes())
            case = Case("a", "game", wav, "rotate B", "synthetic")
            records, failures = run([case], ["base.en"], ["fast", "balanced"], ["off"],
                                    "cpu", "int8", False, FakeRecognizer, FakeConfig,
                                    {"fast": 1, "balanced": 1}, paths=("whole", "capture_cut"))
        self.assertEqual(failures, [])
        self.assertEqual(len(records), 4)
        self.assertEqual(len(calls), 4)
        self.assertEqual({row["cpu_threads"] for row in records if row["preset"] == "fast"}, {1})
        self.assertEqual({row["cpu_threads"] for row in records if row["preset"] == "balanced"}, {2})

    def test_summary_separates_runtime_device_fallback(self):
        case = Case("a", "game", Path("a.wav"), "rotate B", "test")
        cpu = score_record(case, "base.en", "balanced", "off", "whole",
                           "rotate B", 2, 1, "cpu", "int8")
        gpu = score_record(case, "base.en", "balanced", "off", "whole",
                           "rotate B", 0.2, 1, "cuda", "float16")
        groups = summarize([cpu, gpu])
        self.assertEqual({row["device"] for row in groups}, {"cpu", "cuda"})
        self.assertTrue(all(row["cases"] == 1 for row in groups))

    def test_corrupt_audio_is_reported_and_other_cases_continue(self):
        class FakeConfig(SimpleNamespace):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        class FakeRecognizer:
            def __init__(self, config):
                self.config = config
                self._loaded_model_size = ""
                self.runtime_device = "cpu"
                self.runtime_compute_type = "int8"

            def initialize(self):
                self._loaded_model_size = self.config.model_size

            def transcribe_audio_bytes_with_language(self, chunk, sample_rate, language_override):
                return SimpleNamespace(text="rotate B")

            def cleanup(self):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = root / "bad.wav"
            bad.write_bytes(b"not audio")
            good = root / "good.wav"
            pcm = (np.sin(np.arange(16000) * 2 * np.pi * 330 / 16000) * 12000).astype(np.int16)
            with wave.open(str(good), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(pcm.tobytes())
            cases = [Case("bad", "game", bad, "rotate B", "test"),
                     Case("good", "game", good, "rotate B", "test")]
            records, failures = run(cases, ["base.en"], ["fast"], ["off"], "cpu", "int8",
                                    False, FakeRecognizer, FakeConfig, {"fast": 1},
                                    paths=("whole", "capture_cut"))
        self.assertEqual({row["id"] for row in records}, {"good"})
        self.assertEqual(len(records), 2)
        self.assertEqual(len(failures), 1)
        self.assertIn("bad: audio preparation failed", failures[0])

    def test_resume_rejects_changed_audio_and_case_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "first.wav"
            second = root / "second.wav"
            for wav in (first, second):
                with wave.open(str(wav), "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(b"\x01\x00" * 100)
            manifest = root / "manifest.jsonl"
            manifest.write_text("\n".join(json.dumps({"id": str(i), "category": "game",
                                                        "audio": str(path), "reference": "rotate B"})
                                          for i, path in enumerate((first, second))) + "\n",
                                encoding="utf-8")
            output = root / "report"
            args = ["--manifest", str(manifest), "--output-dir", str(output),
                    "--models", "base.en", "--presets", "fast", "--prompts", "off"]
            with patch("scripts.run_asr_benchmark.run", return_value=([], [])) as mocked:
                self.assertEqual(main(args), 1)
                with self.assertRaises(SystemExit):
                    main([*args, "--limit", "1", "--resume"])
                with wave.open(str(first), "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(b"\x02\x00" * 100)
                with self.assertRaises(SystemExit):
                    main([*args, "--resume"])
                self.assertEqual(mocked.call_count, 1)


if __name__ == "__main__":
    unittest.main()
