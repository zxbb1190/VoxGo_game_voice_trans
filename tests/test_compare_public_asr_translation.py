import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from scripts.compare_public_asr_translation import (
    AttemptJournal, CountedTranslator, ENDPOINT, MODEL, SUMMARY,
    build_plan, load_config,
)
from voxgo.translation import GameTranslator, TranslationConfig


class ComparisonPlanTest(unittest.TestCase):
    def test_fixed_public_inputs_are_verbatim_and_replicates_are_balanced(self):
        summary = json.loads(SUMMARY.read_text(encoding='utf-8'))
        plan = build_plan(summary)
        self.assertEqual(len(plan['inputs']), 22)
        self.assertEqual(len(plan['schedule']), 44)
        actual = {(row['source_lang'], row['text']) for row in plan['inputs'] if row['arm']=='actual_fragment'}
        source = {(case['language'], entry['text']) for case in summary['cases'] for entry in case['asr']}
        self.assertEqual(actual, source)
        self.assertEqual({row['text'] for row in plan['inputs'] if row['arm']=='actual_joined'},
                         {' '.join(entry['text'] for entry in case['asr']) for case in summary['cases']})
        self.assertEqual([x['case_id'] for x in plan['schedule'][:22]],
                         list(reversed([x['case_id'] for x in plan['schedule'][22:]])))

    def test_missing_or_truncated_logs_do_not_invent_replay_inputs(self):
        summary = json.loads(SUMMARY.read_text(encoding='utf-8'))
        summary['cases'][0]['asr'][0]['text'] = 'x'*80
        with self.assertRaisesRegex(ValueError, 'log-truncated'):
            build_plan(summary)

    def test_exact_service_and_candidate_parameters_are_read_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            baseline={'app':{'telemetry_consent':'denied'},'translation':{'provider':'openai_compatible','model':MODEL,
                      'context_messages':0,'max_tokens':80,'temperature':0,'timeout_seconds':12,'max_concurrent_requests':1}}
            saved={'app':{'telemetry_consent':'denied'},'translation':{'max_tokens':80,'enable_local_phrase_cache':True}}
            credential={'translation':{'provider':'openai_compatible','model':MODEL,'endpoint':ENDPOINT,'api_key':'fixture-secret'}}
            for name,value in [('acceptance.config.json',baseline),('user_settings.json',saved),
                ('telemetry_consent.json',{'telemetry_consent':'denied'}),('credentials.json',credential)]:
                (root/name).write_text(json.dumps(value))
            before={p.name:p.read_bytes() for p in root.iterdir()}
            config=load_config(root,root/'credentials.json')
            self.assertEqual(config.max_tokens,80)
            self.assertEqual(config.context_messages,0)
            self.assertTrue(config.enable_local_phrase_cache)
            self.assertEqual(config.endpoint,ENDPOINT)
            self.assertEqual({p.name:p.read_bytes() for p in root.iterdir()},before)
            credential['translation']['model']='other'
            (root/'credentials.json').write_text(json.dumps(credential))
            with self.assertRaisesRegex(ValueError,'unavailable'):
                load_config(root,root/'credentials.json')

    def test_reservation_precedes_transport_and_guard_never_forwards_other_models(self):
        class Response:
            status=200
            async def json(self):
                return {'model':MODEL,'choices':[{'message':{'content':'<source_text>夹具译文</source_text>'},'finish_reason':'stop'}],
                        'usage':{'total_tokens':3}}
        class Context:
            async def __aenter__(self):return Response()
            async def __aexit__(self,*args):return False
        class Session:
            closed=False
            def post(self,url,*args,**kwargs):
                self.url,self.kwargs=url,kwargs
                if not (base/'attempts.jsonl').exists():raise AssertionError('Reservation must precede HTTP')
                return Context()
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder); journal=AttemptJournal(base/'attempts.jsonl'); session=Session()
            config=TranslationConfig(provider='openai_compatible',model=MODEL,endpoint=ENDPOINT,
                                     api_key='fixture-secret',source_lang='ja',target_lang='zh')
            client=CountedTranslator(config,journal);client.case_id='fixture';client.repeat=1
            async def run():
                with patch.object(GameTranslator,'_get_session',new=AsyncMock(return_value=session)):
                    result=await client.translate_result('まだ入らないで。','ja')
                self.assertEqual(result.translated,'<source_text>夹具译文</source_text>')
                self.assertEqual(client.http_status,200)
                self.assertEqual(journal.count,1)
                self.assertFalse(session.kwargs['allow_redirects'])
                self.assertEqual(session.kwargs['json']['max_tokens'],80)
                self.assertIn('日文翻译成中文',session.kwargs['json']['messages'][-1]['content'])
                with self.assertRaisesRegex(ValueError,'blocked'):
                    session.post(ENDPOINT,json={'model':'paid/other'})
            asyncio.run(run())
            text=(base/'attempts.jsonl').read_text()
            self.assertNotIn('fixture-secret',text)
            self.assertNotIn('まだ入らないで',text)
            with self.assertRaisesRegex(ValueError,'must not be overwritten'):
                AttemptJournal(base/'attempts.jsonl')


if __name__=='__main__':unittest.main()
