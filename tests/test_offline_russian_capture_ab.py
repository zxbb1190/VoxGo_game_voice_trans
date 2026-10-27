from collections import defaultdict
from dataclasses import asdict
import copy
import hashlib
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import Mock, patch
import numpy as np

from scripts.offline_russian_capture_ab import (
    IDS, RADIATION, MOSQUITO, create_output, load_pcm, local_base,
    make_config, offline_guard, schedule, semantic_flags, validate_output,
)
from scripts.offline_asr_observer import (
    Journal, ObservedCapture, ObservedPipeline, coalesce, observe_merge, write_wav,
)
from voxgo.audio.capture import SpeechSegment, SystemAudioCapture
from voxgo.asr.pipeline import SpeechPipeline, merge_speech_work_items
from voxgo.asr.whisper_engine import TranscriptionResult
from voxgo.runtime.events import EventBus, TranscriptReady
from voxgo.runtime.work_items import LatencyTrace, SpeechWorkItem


class OfflineCaptureSafetyTest(unittest.TestCase):
    def test_effective_overrides_survive_item_snapshot_and_source_is_unmodified(self):
        from voxgo.config.loader import default_app_config
        source = default_app_config()
        source.translation.source_lang = "ru"
        before = copy.deepcopy(source)
        with patch("voxgo.config.loader.default_app_config", return_value=source):
            config = make_config(Path(".models"), 3.5, 300, 350)
        self.assertEqual(source, before)
        effective = asdict(config.whisper)
        pipeline = SpeechPipeline(lambda: config, lambda: None, EventBus(), defaultdict(int), lambda: True,
                                  lambda: False, lambda: "id", {}, lambda *a: None)
        segment = SpeechSegment(audio_data=b"\1\0"*16000, sample_rate=16000, duration_seconds=1.,
                                voice_duration_seconds=1.,block_count=8,voice_blocks=8,peak_rms_dbfs=-20.,
                                energy_threshold_dbfs=-45.,noise_floor_dbfs=None,reason="fixture")
        item = SpeechWorkItem(segment, LatencyTrace(item_id="id", speech_detected_at=1., queued_at=1.))
        pipeline._apply_language_snapshot(item, config)
        self.assertEqual(asdict(item.whisper_config_snapshot), effective)
        self.assertEqual((config.audio.max_speech_seconds, config.audio.pre_roll_ms, config.audio.speech_idle_timeout_ms), (3.5,300,350))
        self.assertEqual((item.whisper_config_snapshot.active_model_size, item.whisper_config_snapshot.beam_size,
                          item.whisper_config_snapshot.cpu_threads, item.whisper_config_snapshot.language), ("base",1,2,"auto"))
        self.assertFalse(item.whisper_config_snapshot.condition_on_previous_text)
        self.assertEqual(before.translation.api_key, source.translation.api_key)

    def test_only_maximum_varies_and_en_zh_defaults_unchanged(self):
        from voxgo.config.loader import default_app_config
        baseline = asdict(default_app_config())
        configs = [make_config(Path(".models"), m,450,450) for m in (4.5,3.,3.5,4.)]
        for config in configs:
            self.assertEqual(asdict(config.whisper), asdict(configs[0].whisper))
            audio = asdict(config.audio)
            audio["max_speech_seconds"] = 4.5
            self.assertEqual(audio, asdict(configs[0].audio))
        self.assertEqual(asdict(default_app_config()), baseline)

    def test_reverse_crossover_includes_both_cadences_and_all_arms(self):
        rows = schedule([4.5,3.,3.5,4.],[5,100],450,450,2)
        self.assertEqual(len(rows),16)
        self.assertEqual([(r["cadence_ms"],r["max_speech_seconds"]) for r in rows[:8]],
                         [(r["cadence_ms"],r["max_speech_seconds"]) for r in rows[8:]][::-1])

    def test_sha_and_paired_stream_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = []
            for i, clip_id in enumerate(IDS):
                path = root/f"{i}.wav"
                write_wav(path, b"\1\0"*(16000+i*1600))
                rows.append(dict(id=clip_id, audio=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
            manifest = root/"manifest.json"
            manifest.write_text(json.dumps(rows))
            clips, stream, frames = load_pcm(manifest)
            self.assertEqual(clips[0]["stream_start_frame"],48000)
            self.assertEqual(clips[1]["stream_start_frame"],96000)
            self.assertEqual(len(stream) % 3840, 0)
            self.assertLess(len(stream)//2-frames,1920)
            (root/"0.wav").write_bytes(b"corrupt")
            with self.assertRaisesRegex(ValueError,"SHA256"):
                load_pcm(manifest)

    def test_existing_and_protected_output_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(FileExistsError):
                create_output(root)
            with self.assertRaisesRegex(ValueError,"outside"):
                validate_output(root/"new",root/"manifest.json",Path(".models"))

    def test_missing_models_stop_without_cache_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)/"missing"
            with self.assertRaises(FileNotFoundError):
                local_base(root)
            self.assertFalse(root.exists())

    def test_network_is_blocked_before_dns_and_counted(self):
        with offline_guard() as safety:
            with self.assertRaisesRegex(RuntimeError,"network disabled"):
                socket.getaddrinfo("must-not-resolve.invalid",443)
            self.assertEqual(safety["blocked_network_attempts"],1)

    def test_semantic_detection_is_suspicion_only_and_capitalization_preserved(self):
        text = "радиоактивный цизи и йод"
        result = semantic_flags(RADIATION,text,"", "",["ru","nl"])
        self.assertTrue(result["raw"]["cesium_suspected"])
        self.assertFalse(result["retained"]["cesium_suspected"])
        self.assertEqual(result["non_russian_detected"],["nl"])
        result = semantic_flags(MOSQUITO,"через Комаров болезнь передается человеку", "", "",["ru"])
        self.assertTrue(result["raw"]["person_capitalization_suspected"])
        self.assertEqual(result["semantic_correctness"],"pending_bilingual_review")


class OfflineObserverTest(unittest.TestCase):
    def test_coalescing_preserves_discontinuity_and_overlap(self):
        self.assertEqual(coalesce([[0,4],[4,8],[7,9],[12,14]]),[[0,8],[7,9],[12,14]])

    def test_actual_queue_join_frames_and_force_split_are_tracked(self):
        config = make_config(Path(".models"),.24,0,450)
        stream = b"\1\0"*7680
        with tempfile.TemporaryDirectory() as directory, Journal(Path(directory),stream,[]) as journal:
            with patch("voxgo.audio.capture.pyaudio.PyAudio"), patch.object(SystemAudioCapture,"_is_vad_speech",return_value=(True,1.)):
                capture = ObservedCapture(config.audio,journal)
                capture.set_speech_callback(capture.observe_segment)
                try:
                    for start in (0,3840):
                        capture._energy_threshold = np.float64(-40.)
                        for offset in (start,start+1920):
                            capture.feed(stream[offset*2:(offset+1920)*2],offset,offset+1920,0.)
                        capture.process_audio()
                    self.assertEqual([r["spans"] for r in journal.segments.values()],[[[0,3840]],[[3840,7680]]])
                    self.assertEqual([r["joined_blocks"] for r in journal.windows],[2,2])
                finally:
                    capture._audio.terminate()
                    journal.handle.close()

    def test_identical_silence_provenance_and_raw_queue_overflow_are_unambiguous(self):
        config = make_config(Path(".models"),.24,0,450)
        stream = b"\0\0"*(1920*6)
        with tempfile.TemporaryDirectory() as directory, Journal(Path(directory),stream,[]) as journal:
            with patch("voxgo.audio.capture.pyaudio.PyAudio"), patch.object(SystemAudioCapture,"_is_vad_speech",return_value=(True,1.)):
                capture = ObservedCapture(config.audio,journal)
                capture.set_speech_callback(capture.observe_segment)
                try:
                    for offset in range(0,1920*6,1920):
                        capture.feed(stream[offset*2:(offset+1920)*2],offset,offset+1920,0.)
                    capture.process_audio()
                    drops = [e for e in journal.events if e["kind"]=="raw_queue_drop"]
                    self.assertEqual([e["spans"] for e in drops],[[[0,1920]]])
                    self.assertEqual(next(iter(journal.segments.values()))["spans"],[[1920,11520]])
                    self.assertEqual(journal.windows[0]["joined_blocks"],5)
                finally:
                    capture._audio.terminate()

    def test_actual_pre_roll_frames_are_distinct_from_nominal_setting(self):
        config = make_config(Path(".models"),4.5,450,450)
        stream = b"\0\0"*(1920*3)+b"\1\0"*(1920*2)
        with tempfile.TemporaryDirectory() as directory, Journal(Path(directory),stream,[]) as journal:
            with patch("voxgo.audio.capture.pyaudio.PyAudio"), patch.object(SystemAudioCapture,"_is_vad_speech",side_effect=[(False,0.)]*3+[(True,1.)]*2):
                capture = ObservedCapture(config.audio,journal)
                capture.set_speech_callback(capture.observe_segment)
                try:
                    for offset in range(0,1920*5,1920):
                        capture.feed(stream[offset*2:(offset+1920)*2],offset,offset+1920,0.)
                        capture.process_audio()
                    capture._emit_speech_buffer("unit_test_flush")
                    row = next(iter(journal.segments.values()))
                    self.assertEqual(row["pre_roll_actual_frames"],5760)
                    self.assertEqual(row["pre_roll_spans"],[[0,5760]])
                    self.assertEqual(row["spans"],[[0,9600]])
                finally:
                    capture._audio.terminate()

    def test_worker_stop_acknowledges_empty_queue_without_model(self):
        config = make_config(Path(".models"),4.5,450,450)
        with tempfile.TemporaryDirectory() as directory, Journal(Path(directory),b"",[]) as journal:
            pipeline = ObservedPipeline(lambda:config,lambda:None,EventBus(),defaultdict(int),lambda:True,lambda:False,
                                        lambda:"id",{},lambda *a:None,lambda:1,journal=journal)
            pipeline.start()
            self.assertTrue(pipeline.stop())
            self.assertIsNone(pipeline._worker_thread)
            self.assertTrue(pipeline._queue.empty())

    def test_same_production_filter_drops_nl_and_preserves_raw_without_translation(self):
        config = make_config(Path(".models"),4.5,450,450)
        pcm = b"\1\0"*24960
        with tempfile.TemporaryDirectory() as directory, Journal(Path(directory),pcm,[]) as journal:
            recognizer = Mock()
            recognizer.config = config.whisper
            recognizer.runtime_device = "cpu"
            recognizer.runtime_compute_type = "int8"
            recognizer.transcribe_audio_bytes_with_language.return_value = TranscriptionResult(
                text="het seise ijoud.",raw_text="het seise ijoud.",language="nl",language_probability=.19184,
                avg_logprob=-1.33,no_speech_prob=.41)
            bus, received = EventBus(), []
            bus.subscribe(TranscriptReady,received.append)
            pipeline = ObservedPipeline(lambda:config,lambda:recognizer,bus,defaultdict(int),lambda:True,lambda:False,
                                        lambda:"id",{},lambda *a:None,lambda:1,journal=journal)
            segment = SpeechSegment(audio_data=pcm,sample_rate=16000,duration_seconds=1.56,voice_duration_seconds=.96,
                                    voice_blocks=8,vad_voice_blocks=8,block_count=13,vad_confidence=8/13,
                                    peak_rms_dbfs=-20.,energy_threshold_dbfs=-45.,noise_floor_dbfs=None,reason="fixture")
            journal.segment(segment,[[0,24960]])
            pipeline.on_speech_detected(segment)
            item = pipeline._queue.get_nowait()
            pipeline._process(item)
            self.assertEqual(received,[])
            row = journal.segment(segment)
            self.assertEqual(row["status"],"dropped")
            self.assertIn("语言置信度",row["filter_reason"])
            self.assertEqual(pipeline._process.__func__.__qualname__,"ObservedPipeline._process")
            journal.handle.close()

    def test_merge_retains_parents_and_exact_noncontiguous_provenance(self):
        stream = b"\1\0"*10+b"\2\0"*10+b"\3\0"*10
        with tempfile.TemporaryDirectory() as directory, Journal(Path(directory),stream,[]) as journal:
            items = []
            for a,b in ((0,10),(20,30)):
                segment = SpeechSegment(audio_data=stream[a*2:b*2],sample_rate=16000,duration_seconds=(b-a)/16000,
                                        voice_duration_seconds=(b-a)/16000,block_count=1,voice_blocks=1,
                                        peak_rms_dbfs=-20.,energy_threshold_dbfs=-45.,noise_floor_dbfs=None,reason="fixture")
                journal.segment(segment,[[a,b]])
                items.append(SpeechWorkItem(segment,LatencyTrace(item_id="",speech_detected_at=1.,queued_at=1.)))
            merged = observe_merge(journal,merge_speech_work_items)(*items)
            row = journal.segment(merged.segment)
            self.assertEqual(row["spans"],[[0,10],[20,30]])
            self.assertEqual(len(row["parents"]),2)
            self.assertTrue(all(journal.segment(i.segment)["status"]=="merged_into" for i in items))
            journal.handle.close()


if __name__ == "__main__":
    unittest.main()
