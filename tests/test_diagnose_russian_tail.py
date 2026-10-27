from collections import defaultdict
import copy
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts import diagnose_russian_tail as tool
from scripts.offline_asr_observer import Journal, ObservedPipeline, write_wav
from scripts.offline_russian_capture_ab import make_config, digest
from voxgo.audio.capture import SpeechSegment
from voxgo.asr.whisper_engine import TranscriptionResult, should_drop_transcription_result
from voxgo.runtime.events import EventBus, TranscriptReady
from voxgo.runtime.work_items import SpeechWorkItem
from voxgo.translation.base import should_skip_translation_for_language


def segment(pcm):
    return SpeechSegment(audio_data=pcm,sample_rate=16000,duration_seconds=.84,voice_duration_seconds=.36,
        block_count=7,voice_blocks=3,peak_rms_dbfs=-52.27957152650901,energy_threshold_dbfs=-45.,
        noise_floor_dbfs=-200.,reason="静音结束/尾音下降",vad_voice_blocks=3,energy_voice_blocks=0,
        vad_confidence=3/7,activity_source="vad",latency_mode="custom")


class TailProvenanceTests(unittest.TestCase):
    def fixture(self, root):
        pcm=b"\1\0"*13440
        source=root/"source.wav"
        write_wav(source,b"\0\0"*98560+pcm+b"\0\0"*100)
        run=root/"run";run.mkdir()
        saved=run/"s005.wav";write_wav(saved,pcm)
        stream=b"\0\0"*293760+pcm
        row={k:v for k,v in vars(segment(pcm)).items() if k!="audio_data"}
        row.update(segment_id="s005",spans=[tool.STREAM_SPAN],pcm_sha256=digest(pcm),filter_reason="asr_budget_weak_drop",
            sources=[dict(id=tool.MOSQUITO,wav_start_frame=98560,wav_end_frame=112000)])
        record=dict(segments=[row],clips=[dict(id=tool.MOSQUITO,audio=str(source),sha256=digest(source.read_bytes()))],replay_stream_sha256=digest(stream))
        (run/"result.json").write_text(json.dumps(record),encoding="utf-8")
        index=root/"index.json"
        index.write_text(json.dumps([dict(path=str(p),sha256=digest(p.read_bytes())) for p in [saved,run/"result.json"]]),encoding="utf-8")
        return pcm,stream,run,index

    def test_saved_bytes_sha_format_frames_and_original_interval_are_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            pcm,stream,run,index=self.fixture(Path(directory))
            with patch.object(tool,"PCM_SHA",digest(pcm)),patch.object(tool,"load_pcm",return_value=([],stream,len(stream)//2)):
                actual,row,old,clips,playback,provenance=tool.load_tail(run,index)
            self.assertEqual(actual,pcm)
            self.assertEqual(provenance["frames"],13440)
            self.assertEqual(provenance["replay_padding_frames"],0)
            self.assertEqual(row["voice_duration_seconds"],.36)

    def test_tampered_saved_wav_fails_before_inference(self):
        with tempfile.TemporaryDirectory() as directory:
            pcm,stream,run,index=self.fixture(Path(directory))
            path=run/"s005.wav";path.write_bytes(path.read_bytes()+b"tampered")
            with self.assertRaisesRegex(ValueError,"artifact SHA256"):
                tool.load_tail(run,index)


class TailExecutionTests(unittest.TestCase):
    def setup_pipeline(self,journal,pcm,result):
        config=make_config(Path(".models"),3.,450,450)
        recognizer=SimpleNamespace(config=copy.deepcopy(config.whisper),runtime_device="cpu",runtime_compute_type="int8",
                                  transcribe_audio_bytes_with_language=Mock(return_value=result))
        holder=[recognizer];stats=defaultdict(int);bus=EventBus()
        pipeline=ObservedPipeline(lambda:config,lambda:holder[0],bus,stats,lambda:True,lambda:False,lambda:"id",{},lambda *a:None,lambda:1,journal=journal)
        speech=segment(pcm);journal.segment(speech,[[0,len(pcm)//2]])
        def accepted(event):
            reason=should_skip_translation_for_language(event.text,event.source_lang,event.language,event.language_probability,config.translation)
            journal.segment(speech).update(retained_text=event.text,translation_input="" if reason else event.text,
                status="language_gate_dropped" if reason else "translation_ready")
        bus.subscribe(TranscriptReady,accepted)
        return config,recognizer,holder,pipeline,speech

    def test_direct_calls_recognizer_once_and_uses_production_filters_unchanged(self):
        pcm=b"\1\0"*13440
        result=TranscriptionResult(text="Человеку.",raw_text="Человеку.",language="ru",language_probability=.97,avg_logprob=-.1,no_speech_prob=.01)
        with tempfile.TemporaryDirectory() as d,Journal(Path(d),pcm,[]) as journal:
            config,recognizer,holder,pipeline,speech=self.setup_pipeline(journal,pcm,result)
            policy=pipeline._candidate_policy.classify(speech,config.audio)
            item=SpeechWorkItem(speech,pipeline._make_latency_trace(time.time(),config),candidate_labels=policy.labels,
                               low_confidence=policy.low_confidence,short_segment=policy.short_segment)
            pipeline._apply_language_snapshot(item,config)
            before=asdict(config)
            details=tool.direct_then_filter(pipeline,recognizer,item,holder,journal)
            self.assertEqual(recognizer.transcribe_audio_bytes_with_language.call_count,1)
            self.assertEqual(details["cached_result_consumptions"],1)
            self.assertEqual(details["weak_pre_check"],"")
            self.assertEqual(journal.segment(speech)["translation_input"],result.text)
            self.assertEqual(asdict(config),before)
            self.assertTrue(pipeline.stop())

    def test_fresh_pipeline_preserves_weak_pending_admission_and_stops(self):
        pcm=b"\1\0"*13440
        result=TranscriptionResult(text="Человеку.",raw_text="Человеку.",language="ru",language_probability=.97,avg_logprob=-.1,no_speech_prob=.01)
        with tempfile.TemporaryDirectory() as d,Journal(Path(d),pcm,[]) as journal:
            config,recognizer,holder,pipeline,speech=self.setup_pipeline(journal,pcm,result)
            try:
                output=tool.run_idle(pipeline,speech,journal,timeout=3.)
                self.assertTrue(output["completed"])
                self.assertEqual(output["initial_state"]["last_transcription_finished_at"],0.)
                self.assertIn("short_segment",journal.items[next(iter(journal.items))]["candidate_labels"])
                self.assertGreaterEqual(next(e["elapsed_ms"] for e in journal.events if e["kind"]=="process_start"),290.)
                self.assertEqual(recognizer.transcribe_audio_bytes_with_language.call_count,1)
            finally:
                self.assertTrue(pipeline.stop())
            self.assertTrue(pipeline._queue.empty())

    def test_nonidle_state_is_rejected_without_reset(self):
        pcm=b"\1\0"*13440
        with tempfile.TemporaryDirectory() as d,Journal(Path(d),pcm,[]) as journal:
            _,_,_,pipeline,speech=self.setup_pipeline(journal,pcm,TranscriptionResult(""))
            pipeline._last_transcription_finished_at=123.
            with self.assertRaisesRegex(ValueError,"naturally fresh"):
                tool.run_idle(pipeline,speech,journal)
            self.assertEqual(pipeline._last_transcription_finished_at,123.)

    def test_both_arms_keep_actual_low_confidence_russian_result_and_drop_reason(self):
        pcm=b"\1\0"*13440
        result=TranscriptionResult(text="человеку.",raw_text="человеку.",language="ru",
            language_probability=.7165970802307129,avg_logprob=-1.1982613801956177,
            no_speech_prob=.4966069459915161,compression_ratio=.68)
        reasons=[]
        for arm in ("A","B"):
            with tempfile.TemporaryDirectory() as d,Journal(Path(d),pcm,[]) as journal:
                config,recognizer,holder,pipeline,speech=self.setup_pipeline(journal,pcm,result)
                try:
                    if arm=="A":
                        decision=pipeline._candidate_policy.classify(speech,config.audio)
                        item=SpeechWorkItem(speech,pipeline._make_latency_trace(time.time(),config),
                            candidate_labels=decision.labels,low_confidence=decision.low_confidence,short_segment=decision.short_segment)
                        pipeline._apply_language_snapshot(item,config)
                        tool.direct_then_filter(pipeline,recognizer,item,holder,journal)
                    else:
                        self.assertTrue(tool.run_idle(pipeline,speech,journal,timeout=3.)["completed"])
                    observed=journal.segment(speech)
                    self.assertEqual(observed["status"],"dropped")
                    self.assertNotIn("translation_input",observed)
                    self.assertEqual(recognizer.transcribe_audio_bytes_with_language.call_count,1)
                    reasons.append(observed["filter_reason"])
                finally:
                    if pipeline._worker_thread is not None:
                        self.assertTrue(pipeline.stop())
        self.assertEqual(reasons[0],reasons[1])
        self.assertTrue(reasons[0].startswith("weak_candidate_low_asr_confidence"))
        # Separate diagnostic, NOT the executed Pipeline path after its early return.
        global_reason=should_drop_transcription_result(result,expected_language="auto",recent_texts=[],config=config.whisper)
        self.assertTrue(global_reason.startswith("global_asr_low_logprob_short"))
        self.assertEqual(should_skip_translation_for_language(result.text,"ru","ru",result.language_probability,config.translation),"")

    def test_cached_adapter_cannot_hide_second_recognition(self):
        result=TranscriptionResult("fixture")
        adapter=tool.CachedResultRecognizer(SimpleNamespace(),result)
        self.assertIs(adapter.transcribe_audio_bytes_with_language(),result)
        with self.assertRaisesRegex(RuntimeError,"second cached"):
            adapter.transcribe_audio_bytes_with_language()

    def test_keyword_flag_does_not_invent_retained_text(self):
        flags=tool.recipient_flags(dict(raw_text="Человеку.",language="ru"),"","")
        self.assertTrue(flags["raw_recipient_suspected"])
        self.assertFalse(flags["retained_recipient_suspected"])
        self.assertEqual(flags["human_semantic_review"],"pending")


if __name__=="__main__":
    unittest.main()
