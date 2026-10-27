import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.prepare_ru_continuous_corpus import BudgetedFetch,convert_audio
from scripts.ru_benchmark_metrics import validate_manifest,evaluation_rows,text_metrics,lexical_suspicions,assess,ru_tokens
from scripts.run_ru_continuous_baseline import strategy_config,input_stream,schedule,require_frozen
from scripts.offline_asr_observer import write_wav


def row(identifier="sample",split="dev"):
    return dict(id=identifier,split=split,pcm_sha256=identifier+"-pcm",wav_sha256=identifier+"-wav",historical_match=False,
        license="CC-BY-4.0",license_source="https://example.test/license",source_revision="revision",
        speaker_id="speaker1",speaker_group="speaker1",source_group="recording1",speaker_isolation_status="verified",lock_eligible=True)


class DataSafetyTests(unittest.TestCase):
    def test_dataset_id_pcm_and_history_leakage_are_rejected(self):
        r=row()
        with self.assertRaisesRegex(ValueError,"duplicate"):
            validate_manifest(dict(records=[r,copy.deepcopy(r)]),check_audio=False)
        with self.assertRaisesRegex(ValueError,"historically used"):
            validate_manifest(dict(records=[r]),historical_hashes=[r["pcm_sha256"]],check_audio=False)

    def test_locked_split_requires_identity_and_source_separation(self):
        dev=row();locked=row("held","locked_holdout")
        with self.assertRaisesRegex(ValueError,"leakage"):
            validate_manifest(dict(records=[dev,locked]),check_audio=False)
        locked.update(speaker_group="speaker2",source_group="recording2",speaker_id=None)
        with self.assertRaisesRegex(ValueError,"unknown speakers"):
            validate_manifest(dict(records=[dev,locked]),check_audio=False)
        locked["speaker_id"]="speaker2"
        self.assertTrue(validate_manifest(dict(records=[dev,locked]),check_audio=False))
        dev["speaker_id"]=None
        with self.assertRaisesRegex(ValueError,"dev speaker identities"):
            validate_manifest(dict(records=[dev,locked]),check_audio=False)

    def test_unfrozen_or_unversioned_manifest_cannot_start_inference(self):
        for manifest in [{},dict(schema_version=1,frozen_before_asr=False)]:
            with self.assertRaisesRegex(ValueError,"frozen manifest"):
                require_frozen(manifest)
        require_frozen(dict(schema_version=1,frozen_before_asr=True))

    def test_quarantine_and_locked_audio_cannot_enter_inference(self):
        records=[row(str(i),split) for i,split in enumerate(["dev","locked_holdout","quarantine","negative"])]
        self.assertEqual([r["split"] for r in evaluation_rows(dict(records=records))],["dev","negative"])
        for r in records[1:3]:
            with self.assertRaisesRegex(ValueError,"forbidden"):
                input_stream(r)

    def test_file_hash_format_and_frames_are_checked(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"sample.wav";pcm=b"\1\0"*1600;write_wav(path,pcm)
            r=row();r.update(audio=str(path),frames=1600,wav_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),pcm_sha256=hashlib.sha256(pcm).hexdigest())
            self.assertTrue(validate_manifest(dict(records=[r])))
            r["frames"]=1601
            with self.assertRaisesRegex(ValueError,"format/frames"):
                validate_manifest(dict(records=[r]))
            path.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError,"WAV SHA256"):
                validate_manifest(dict(records=[r]))

    def test_global_download_budget_counts_all_completed_bodies(self):
        class Response(io.BytesIO):
            @property
            def headers(self):return {"Content-Length":str(len(self.getvalue()))}
        with tempfile.TemporaryDirectory() as d:
            fetch=BudgetedFetch(Path(d),limit=12)
            with patch("urllib.request.urlopen",side_effect=[Response(b"12345"),Response(b"123456"),Response(b"12")]):
                fetch.get("a","https://example.test/a","a.bin")
                fetch.get("b","https://example.test/b","b.bin")
                with self.assertRaisesRegex(ValueError,"budget"):
                    fetch.get("c","https://example.test/c","c.bin")
            self.assertEqual(fetch.data["bytes"],11)
            self.assertEqual(fetch.data["requests"][-1]["status"],"failed")
            self.assertFalse((Path(d)/"c.bin").exists())
            with self.assertRaises(ValueError):BudgetedFetch(Path(d),100_000_001)

    def test_existing_download_is_not_overwritten_or_signed_query_logged(self):
        class Response(io.BytesIO):
            headers={"Content-Length":"1"}
        with tempfile.TemporaryDirectory() as d:
            fetch=BudgetedFetch(Path(d),limit=10)
            with patch("urllib.request.urlopen",return_value=Response(b"x")):
                fetch.get("one","https://example.test/a?signature=not-a-real-secret","a.bin")
            self.assertNotIn("not-a-real-secret",fetch.path.read_text())
            with patch("urllib.request.urlopen") as network:
                with self.assertRaisesRegex(ValueError,"existing"):
                    fetch.get("again","https://example.test/a","a.bin")
                network.assert_not_called()

    def test_pcm_conversion_preserves_native_pcm_without_gain_and_declares_crop(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"source.wav";pcm=b"\1\0"*32000;write_wav(source,pcm)
            out=Path(d)/"copy.wav";meta=convert_audio(source,out,max_seconds=1)
            self.assertEqual(meta["selected_original_frames"],[0,16000])
            self.assertEqual(meta["pcm_sha256"],hashlib.sha256(pcm[:32000]).hexdigest())


class RuntimeAndMetricTests(unittest.TestCase):
    def test_production_strategies_are_resolved_without_experimental_overrides(self):
        from voxgo.config.loader import default_app_config
        base=default_app_config();before=copy.deepcopy(base)
        with patch("voxgo.config.loader.default_app_config",return_value=base):
            legacy=strategy_config(Path(".models"),"legacy")
            aware=strategy_config(Path(".models"),"language_aware")
        self.assertEqual(base,before)
        self.assertEqual((legacy.audio.max_speech_seconds,legacy.audio.pre_roll_ms,legacy.audio.speech_idle_timeout_ms,legacy.whisper.cpu_threads),(3.,300,350,1))
        self.assertEqual((aware.audio.max_speech_seconds,aware.audio.pre_roll_ms,aware.audio.speech_idle_timeout_ms,aware.whisper.cpu_threads),(4.5,450,450,2))
        for config in [legacy,aware]:
            self.assertEqual((config.whisper.active_model_size,config.whisper.beam_size,config.whisper.language),("base",1,"auto"))
            self.assertTrue(config.whisper.local_files_only)

    def test_schedule_has_no_repeats_and_balances_arm_order(self):
        plan=schedule([row("first"),row("second")])
        self.assertEqual([p["strategy"] for p in plan],["legacy","language_aware","language_aware","legacy"])
        self.assertEqual(len({p["id"] for p in plan}),4)

    def test_russian_wer_does_not_discard_cyrillic_or_translate_numbers_to_english(self):
        self.assertEqual(ru_tokens("У меня нет 20 рублей."),["у","меня","нет","20","рублей"])
        metrics=text_metrics("У меня нет 20 рублей.","У меня 20 рублей",alignment_valid=True,reference_status="pending_human_review")
        self.assertEqual(metrics["proxy_wer"],.2)
        self.assertIsNone(metrics["accepted_wer"])
        self.assertTrue(lexical_suspicions("у меня нет 20 рублей","у меня 20 рублей")["negation_token_counts_changed"])

    def test_ambiguous_alignment_and_noise_have_no_fabricated_cer(self):
        self.assertIsNone(text_metrics("текст","другой",alignment_valid=False,reference_status="pending")["proxy_cer"])
        self.assertIsNone(text_metrics("","шум",alignment_valid=True,reference_status="pending_absence_review")["proxy_wer"])

    def test_filtered_inferences_remain_in_timing_and_pre_drops_have_no_fake_asr_time(self):
        completed=dict(segment_id="s1",captured=True,status="dropped",spans=[[48000,50000]],pcm_sha256="a",asr_ms=1000,
            filter_reason="weak_candidate_low_asr_confidence",asr=dict(text="текст",raw_text="текст",language="ru",language_probability=.8))
        pre=dict(segment_id="s2",captured=True,status="dropped",spans=[[50000,52000]],pcm_sha256="b",filter_reason="asr_budget_weak_drop")
        result=dict(segments=[completed,pre],clips=[{}],spec=dict(strategy="legacy"),work_items=[dict(status="dropped",queue_wait_ms=25)],
                    replay_cpu_seconds=2.,peak_sampled_rss_bytes=100,replay_wall_seconds=4.)
        record=dict(id="test",split="dev",seconds=2.,reference_text="текст конец",reference_status="pending")
        events=[dict(kind="whisper_start"),dict(kind="drop",segment_id="s2",reason="asr_budget_weak_drop",elapsed_ms=2000)]
        metrics=assess(result,record,events)
        self.assertEqual(metrics["performance"]["asr_p95_ms"],1000)
        self.assertEqual(metrics["counts"]["pre_asr_drops"],1)
        self.assertEqual(metrics["counts"]["post_asr_drops"],1)
        self.assertEqual(len(metrics["performance"]["asr_all_completed_ms"]),1)
        self.assertEqual(metrics["issues"][0]["first_observed_stage"],"Pipeline.pre_asr")


if __name__=="__main__":unittest.main()
