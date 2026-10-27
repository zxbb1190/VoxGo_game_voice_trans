import asyncio
import copy
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

from scripts.run_five_language_online import AttemptBudget,BudgetStop,MeasuredClient,TRACE,MODEL,load,claim_run
from voxgo.translation import TranslationConfig
from scripts.summarize_five_language_online import request_metrics,script_cue


def approval(limit=3):return dict(authorized=True,plan_sha256='plan',model=MODEL,call_limit=limit)


class AcceptanceBudgetTests(unittest.TestCase):
    def test_authorization_cannot_be_replayed_using_a_fresh_output_directory(self):
        with tempfile.TemporaryDirectory() as d:
            approval_path=Path(d)/'approval.json';output=Path(d)/'first'
            claim_run(approval_path,output,'plan')
            claim_run(approval_path,output,'plan',child=True)
            with self.assertRaises(FileExistsError):claim_run(approval_path,Path(d)/'second','plan')
            with self.assertRaises(ValueError):claim_run(approval_path,Path(d)/'second','plan',child=True)

    def test_summary_includes_failures_and_does_not_invent_human_language_accuracy(self):
        rows=[dict(attempt_id=1,http_status=200,complete_json_response=True,api_nonempty_success=True,translated='двое',target='ru',elapsed_ms=1000,queue_wait_ms=0),
              dict(attempt_id=2,http_status=None,failure_reason='timeout',elapsed_ms=15000,queue_wait_ms=3000)]
        metrics=request_metrics(rows,[dict(id=1,http_status=200),dict(id=2,http_status=None)])
        self.assertEqual(metrics['http_complete_success_rate'],.5)
        self.assertEqual(metrics['timeouts'],1)
        self.assertGreater(metrics['queue_subtracted_http_estimate_p95_ms'],10000)
        self.assertIsNone(metrics['human_intelligibility_rate'])
        self.assertEqual(script_cue('敵発見','ja'),'ambiguous_han_only_japanese')
        with self.assertRaises(ValueError):request_metrics(rows+[rows[0]],[])

    def test_authorization_model_scope_and_ceiling_are_mandatory(self):
        with tempfile.TemporaryDirectory() as d:
            for a in [dict(approval(),authorized=False),dict(approval(),call_limit=301),dict(approval(),model='other')]:
                with self.assertRaises(ValueError):AttemptBudget(Path(d)/'ledger.json',a,'plan')
            with self.assertRaises(ValueError):AttemptBudget(Path(d)/'ledger.json',approval(),'wrong-plan')

    def test_attempts_survive_new_process_owner_and_no_extra_reservation(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'ledger.json';b=AttemptBudget(path,approval(2),'plan')
            self.assertEqual(b.reserve(dict(phase='test')),1)
            b=AttemptBudget(path,approval(2),'plan');self.assertEqual(b.reserve(dict(phase='test')),2)
            with self.assertRaises(BudgetStop):b.reserve(dict(phase='test'))
            self.assertEqual(len(load(path)['attempts']),2)

    def test_limit_auth_payment_and_unsupported_http_stop_next_request(self):
        for status in [400,401,402,403,404,429]:
            with tempfile.TemporaryDirectory() as d:
                b=AttemptBudget(Path(d)/'ledger.json',approval(),'plan');id=b.reserve({});b.mark(id,http_status=status)
                with self.assertRaises(BudgetStop):b.reserve({})


class MeasuredTransportTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.requests=[];owner=self
        class Server(BaseHTTPRequestHandler):
            def log_message(self,*a):pass
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));owner.requests.append(body);time.sleep(.03)
                data=json.dumps(dict(choices=[dict(message=dict(content='fixture-only'),finish_reason='stop')],usage=dict(total_tokens=4))).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Server);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.budget=AttemptBudget(Path(self.tmp.name)/'ledger.json',approval(2),'plan')
        self.config=TranslationConfig(endpoint=f'http://127.0.0.1:{self.server.server_address[1]}/v1',source_lang='ja',target_lang='ru',api_key='',model=MODEL,enable_local_phrase_cache=False,max_concurrent_requests=1)
        self.client=MeasuredClient(self.config,self.budget,'fixture',allow_loopback_fixture=True)
    async def asyncTearDown(self):
        await self.client.close();self.server.shutdown();self.server.server_close();self.thread.join(2)
    async def test_real_loopback_protocol_is_counted_before_post_and_queue_is_separate(self):
        async def call(id):
            token=TRACE.set(id)
            try:return await self.client.translate_result_with_config('右に二人', 'ja',copy.deepcopy(self.config))
            finally:TRACE.reset(token)
        await asyncio.gather(call('one'),call('two'))
        self.assertEqual(len(self.requests),2)
        self.assertEqual({r['trace_id'] for r in self.client.rows},{'one','two'})
        self.assertTrue(all(r['http_status']==200 and r['api_nonempty_success'] for r in self.client.rows))
        self.assertGreater(max(r['queue_wait_ms'] for r in self.client.rows),10)
        await call('three')
        self.assertEqual(len(self.requests),2)
        self.assertIsNone(self.client.rows[-1]['attempt_id'])
        self.assertEqual(len(load(self.budget.path)['attempts']),2)
    async def test_production_transport_refuses_even_loopback_without_explicit_fixture_mode(self):
        self.client.fixture=False
        result=await self.client.translate_result_with_config('右に二人','ja',self.config)
        self.assertEqual(self.requests,[])
        self.assertIsNone(self.client.rows[-1]['attempt_id'])
        self.assertTrue(result.failure_reason)


if __name__=='__main__':unittest.main()
