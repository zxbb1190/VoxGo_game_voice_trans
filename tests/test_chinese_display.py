import copy
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from voxgo.app import VoxGoApp
from voxgo.config.schema import AppConfig, RuntimeConfig
from voxgo.runtime.events import TranscriptReady, TranslationReady
from voxgo.translation import TranslationConfig
from voxgo.ui.chinese_text import recognition_display_text

ROOT = Path(__file__).resolve().parents[1]


class ChineseDisplayTests(unittest.TestCase):
    def test_chinese_script_conversion_keeps_typos_numbers_names_and_unicode(self):
        cases = (
            ('這並不是告別。', '这并不是告别。'),
            ('這是一個偏章的結束，也是新偏章的開始。', '这是一个偏章的结束，也是新偏章的开始。'),
            ('後衛在後門，還有15秒，不是50秒，不要開槍！', '后卫在后门，还有15秒，不是50秒，不要开枪！'),
            ('乾隆與乾淨的頭髮，臺灣與颱風。', '乾隆与干净的头发，台湾与台风。'),
            ('Discord A12🙂 <tag> 軟體與伺服器', 'Discord A12🙂 <tag> 软体与伺服器'),
            ('已经是简体，CPU / GPU 2.5s', '已经是简体，CPU / GPU 2.5s'),
        )
        for raw,expected in cases:
            self.assertEqual(recognition_display_text(raw,'zh'),expected)
        self.assertEqual(recognition_display_text('','zh'),'')

    def test_other_sources_do_not_load_converter_or_change_japanese_kanji(self):
        text='後ろに移動、開始！ Traditional 體 ABC 123'
        with patch('voxgo.ui.chinese_text._converter',side_effect=AssertionError('must stay lazy')):
            for source in ('en','ja','ko','ru',''):
                self.assertEqual(recognition_display_text(text,source),text)

    def make_app(self,target):
        app=VoxGoApp.__new__(VoxGoApp)
        app.config=AppConfig(app=RuntimeConfig(language='ja-JP'),
            translation=TranslationConfig(source_lang='zh',target_lang=target))
        app._stopping=False
        app._language_flow_revision=1
        app._stats=defaultdict(int)
        app._latency_traces={}
        app._speech_pipeline=SimpleNamespace(remember_transcript=Mock())
        app._overlay=Mock()
        app._start_async_translation=Mock()
        return app

    def test_all_four_directions_change_display_but_send_raw_asr_to_translation(self):
        raw='後衛在後門，還有15秒，不要開槍。'
        simplified='后卫在后门，还有15秒，不要开枪。'
        for target in ('en','ja','ko','ru'):
            app=self.make_app(target)
            event=TranscriptReady(text=raw,language='zh',trace_id='display',language_probability=1.,source_lang='zh',target_lang=target,language_revision=1)
            before=copy.deepcopy(event.__dict__)
            app._handle_transcript_ready(event)
            app._speech_pipeline.remember_transcript.assert_called_once_with(raw)
            app._overlay.add_translation_with_id.assert_called_once_with('display',simplified,'...正在翻译')
            args=app._start_async_translation.call_args.args
            self.assertEqual(args[1],raw)
            self.assertEqual(args[4:7],('zh',target,1))
            self.assertEqual(event.__dict__,before)

    def test_mobile_mirror_uses_event_source_and_keeps_real_translation_unchanged(self):
        app=self.make_app('en')
        app.config.translation.source_lang='ja'
        app._mobile=SimpleNamespace(server=object())
        app._broadcast_to_mobile=Mock()
        raw='這並不是告別。';translation='It is not goodbye.'
        event=TranslationReady(raw,translation,'zh','en','display',1)
        app._handle_translation_ready(event)
        app._overlay.update_translation.assert_called_once_with('display',translation,copyable=True)
        app._broadcast_to_mobile.assert_called_once_with('这并不是告别。',translation)
        self.assertEqual(event.original,raw)
        self.assertEqual(event.translated,translation)

    def test_bad_display_resource_never_blocks_translation(self):
        app=self.make_app('en');raw='後門'
        with (patch('voxgo.ui.chinese_text._simplified',side_effect=RuntimeError('fixture only')),
              patch('voxgo.ui.chinese_text._warned',False), patch('loguru.logger.warning') as warning):
            app._handle_transcript_ready(TranscriptReady(raw,'zh','failure',1.,'zh','en',language_revision=1))
            self.assertEqual(app._start_async_translation.call_args.args[1],raw)
            self.assertNotIn(raw,str(warning.call_args))

    def test_upstream_bytes_and_packaging_resources_are_pinned(self):
        vendor=ROOT/'voxgo/ui/_opencc'
        provenance=json.loads((vendor/'UPSTREAM.json').read_text('utf-8'))
        self.assertEqual(provenance['version'],'0.1.7')
        self.assertEqual(provenance['license'],'Apache-2.0')
        for file in provenance['files']:
            self.assertEqual(hashlib.sha256((vendor/file['path']).read_bytes()).hexdigest(),file['sha256'])
        self.assertEqual({p.name for p in (vendor/'dictionary').iterdir()},{'TSCharacters.txt','TSPhrases.txt'})
        spec=(ROOT/'VoxGo.spec').read_text('utf-8')
        for entry in ('config','dictionary','LICENSE.txt','NOTICE.txt','UPSTREAM.json'):
            self.assertIn('voxgo/ui/_opencc/'+entry,spec)
