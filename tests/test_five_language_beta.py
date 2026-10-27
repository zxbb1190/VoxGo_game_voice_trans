import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.prepare_five_language_beta import BoundedArchiveReader,CorpusFetch,exclusion_names
from scripts.run_five_language_asr import resolved_config,make_schedule,cjk_units,LANGUAGES
from scripts.offline_russian_capture_ab import local_model
from scripts.native_five_language_protocol import loopback_connect
from scripts.review_five_language_asr import cues
from scripts.plan_five_language_online import build_plan,TEXTS


class FiveLanguageCorpusTest(unittest.TestCase):
    def test_native_smoke_can_connect_only_to_loopback(self):
        from unittest.mock import Mock
        original=Mock(return_value=0);guard=loopback_connect(original)
        self.assertEqual(guard('socket',('127.0.0.1',1234)),0)
        with self.assertRaises(RuntimeError):guard('socket',('8.8.8.8',443))
        original.assert_called_once()

    def test_archive_counts_unselected_compressed_bytes_and_stops_at_global_cap(self):
        with tempfile.TemporaryDirectory() as d:
            f=CorpusFetch(Path(d),limit=7);r=dict(bytes=0);reader=BoundedArchiveReader(io.BytesIO(b'123456789'),f,r)
            self.assertEqual(reader.read(4),b'1234')
            self.assertEqual(reader.read(4),b'567')
            with self.assertRaisesRegex(ValueError,'limit'):reader.read(1)
            self.assertEqual(f.data['bytes'],7);self.assertEqual(r['bytes'],7)

    def test_transient_windows_ledger_rename_failure_has_bounded_retry(self):
        with tempfile.TemporaryDirectory() as d:
            f=CorpusFetch(Path(d),limit=7)
            with patch('scripts.prepare_ru_continuous_corpus.Path.replace',side_effect=[PermissionError(),None]) as replace,patch('scripts.prepare_five_language_beta.time.sleep'):
                f.save();self.assertEqual(replace.call_count,2)

    def test_history_exclusion_is_original_file_not_old_holdout_label(self):
        self.assertEqual(exclusion_names(dict(ids=['test/123.wav','fleurs-ru-old-holdout','new/456.wav'])),{'123.wav','456.wav'})


class FiveLanguageAsrTest(unittest.TestCase):
    def test_online_plan_counts_all_stream_fragments_instead_of_claiming_120_complete_calls(self):
        manifest=dict(records=[dict(id=l+str(i),language=l,split='dev',reference_text='source reference',reference_status='pending_human_review') for l in LANGUAGES for i in range(3)])
        summary=dict(recordings=[dict(id=l+str(i),strategy='formal' if l in {'en','zh'} else 'language_aware',counts=dict(translation_ready=2)) for l in LANGUAGES for i in range(3)])
        selection=dict(records={l:[l+str(i) for i in range(3)] for l in LANGUAGES})
        provider=dict(provider='openai_compatible',model='tencent/Hunyuan-MT-7B',endpoint_host='api.siliconflow.cn')
        plan=build_plan(manifest,summary,selection,provider)
        self.assertEqual(plan['expected_calls'],dict(authored_text=60,standard_reference=60,streaming_asr=120,total=240))
        self.assertEqual(plan['planned_voice_direction_attempts'],60)
        self.assertEqual(plan['unique_voice_recordings'],15)
        self.assertFalse(plan['authorized']);self.assertEqual(plan['real_api_requests_so_far'],0)
        self.assertEqual(len({(r['source'],r['target']) for r in plan['text_cases']}),20)
        with self.assertRaises(ValueError):build_plan(manifest,summary,selection,dict(provider='google'))

    def test_semantic_cues_for_all_five_languages_are_suspicions_not_human_truth(self):
        for lang,ref,hyp in [('zh','不要开火','开火'),('en','Do not shoot','Shoot'),('ja','撃たないで','撃って'),('ko','쏘지 마','쏴'),('ru','не стреляй','стреляй')]:
            result=cues(lang,ref,hyp)
            self.assertTrue(result['negation_cue_difference'])
            self.assertIsNone(result['human_semantic_accuracy'])
            self.assertIsNone(result['tail_complete'])
        self.assertTrue(cues('en','fifteen seconds','15 seconds')['digit_surface_difference'])

    def test_schedule_is_136_fresh_jobs_from_85_unique_inputs_not_extra_samples(self):
        records=[dict(id=l+str(i),language=l,split='dev') for l in LANGUAGES for i in range(12)]
        records += [dict(id='negative'+str(i),language=None,split='negative') for i in range(25)]
        specs=make_schedule(records)
        self.assertEqual(len(specs),136)
        self.assertEqual(len({s['id'] for s in specs}),136)
        self.assertEqual(len({s['record_id'] for s in specs}),85)
        for l in LANGUAGES:
            self.assertEqual(sum(s['source_language']==l and s['record_id'].startswith('negative') for s in specs),5 if l in {'zh','en'} else 10)

    def test_non_dev_or_negative_never_enters_plan(self):
        self.assertEqual(make_schedule([dict(id='x',language='ru',split='locked_holdout')]),[])

    def test_cjk_unit_error_does_not_pretend_words_or_swallow_mixed_callouts(self):
        self.assertEqual(cjk_units('敌人在A点，不要开火。'),['敌','人','在','a','点','不','要','开','火'])
        self.assertEqual(cjk_units('右に2人です。'),['右','に','2','人','で','す'])

    def test_formal_models_are_cached_and_source_resolved_not_hardcoded_base(self):
        with patch('scripts.run_five_language_asr.local_model') as cached:
            for l,s,model in [('zh','formal','base'),('en','formal','base'),('ja','language_aware','base'),('ko','language_aware','small'),('ru','legacy','base')]:
                config=resolved_config(l,s,Path('.models'))
                self.assertEqual(config.whisper.active_model_size,model)
                self.assertEqual(config.whisper.language,'zh' if l=='zh' else 'auto')
                self.assertTrue(config.whisper.local_files_only)
                self.assertFalse(config.whisper.active_model_size.endswith('.en'))
                self.assertEqual(cached.call_args.args[1],model)

    def test_no_extra_asr_strategy_for_english_chinese_or_other_languages(self):
        for l,s in [('zh','legacy'),('en','language_aware'),('ru','formal'),('fr','legacy')]:
            with self.assertRaises(ValueError):resolved_config(l,s,Path('.models'))

    def test_unknown_or_missing_model_never_downloads_or_falls_back(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):local_model(Path(d),'remote/new-model')
            with self.assertRaises(FileNotFoundError):local_model(Path(d),'small')


if __name__=='__main__':unittest.main()
