import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from scripts.run_prompt_ab_online import (
    APPEND_SHA, FROZEN, MODEL, OUTPUT, PLAN_SHA, PromptABClient, compile_plan, validate_approval,
)
from scripts.run_beta_blocker_online import run_cases
from scripts.run_five_language_online import AttemptBudget, load
from voxgo.translation import TranslationConfig
from voxgo.translation.prompt import translation_system_prompt

PLAN = FROZEN / "next-prompt-ab-plan.json"


class PromptABTests(unittest.TestCase):
    def test_frozen_24_calls_pairs_order_and_no_scope_changes(self):
        plan = compile_plan(PLAN)
        self.assertEqual(len(plan["cases"]), 24)
        for index in range(12):
            a, b = plan["cases"][index*2:index*2+2]
            self.assertEqual(a["input"], b["input"])
            self.assertEqual(a["base_case_id"], b["base_case_id"])
            self.assertEqual(a["profile"]+b["profile"], "AB" if index%2==0 else "BA")
        with tempfile.TemporaryDirectory() as tmp:
            altered = Path(tmp)/"changed.json"
            data=load(PLAN);data["hard_cap"]=25
            altered.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaises(ValueError):compile_plan(altered)

    def test_new_exact_authorization_and_price_required(self):
        today=datetime.now(timezone.utc).date().isoformat()
        price=dict(model=MODEL,http_status=200,checked_at_utc=today+"T00:00:00Z",
                   input_cny_per_million=0,output_cny_per_million=0,url="https://www.siliconflow.cn/pricing")
        approval=dict(authorized=True,plan_sha256=PLAN_SHA,candidate_append_sha256=APPEND_SHA,model=MODEL,
            call_limit=24,output_directory="build/prompt-ab-live-20261028-24",confirmed_free_price_date_utc=today)
        validate_approval(approval,PLAN_SHA,price)
        for patch in (dict(call_limit=25),dict(call_limit=20),dict(model="other"),dict(authorized=False),dict(plan_sha256="old")):
            with self.assertRaises(ValueError):validate_approval(dict(approval,**patch),PLAN_SHA,price)
        for patch in (dict(output_cny_per_million=1),dict(checked_at_utc="2000-01-01T00:00:00Z"),dict(model="other")):
            with self.assertRaises(ValueError):validate_approval(approval,PLAN_SHA,dict(price,**patch))

    def exercise(self, *, status_at=None, tamper=False, duplicate=False):
        plan=compile_plan(PLAN); requests=[]
        class Fixture(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                payload=json.loads(self.rfile.read(int(self.headers["Content-Length"])));requests.append(payload)
                if status_at and len(requests)==status_at:
                    self.send_error(429,"fixture only");return
                body=json.dumps(dict(choices=[dict(message=dict(content="fixture PARTIAL" if len(requests)==2 else "fixture complete"),
                    finish_reason="length" if len(requests)==2 else "stop")])).encode()
                self.send_response(200);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
        server=ThreadingHTTPServer(("127.0.0.1",0),Fixture)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        class TamperedClient(PromptABClient):
            async def translate_result_with_config(self,text,detected_language="",config=None):
                if tamper:self.case_id="not-approved"
                if duplicate and len(self.rows)==1:self.sent_cases.add(self.case_id)
                return await super().translate_result_with_config(text,detected_language,config)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp); approval=dict(authorized=True,plan_sha256="fixture",model=MODEL,call_limit=24)
                budget=AttemptBudget(out/"attempt-ledger.json",approval,"fixture")
                config=TranslationConfig(model=MODEL,api_key="",max_tokens=80,temperature=0,context_messages=0,max_concurrent_requests=1,
                    enable_local_phrase_cache=False,endpoint=f"http://127.0.0.1:{server.server_address[1]}/v1")
                result=run_cases(plan,budget,config,out,platform="offscreen",fixture=True,
                    client_factory=TamperedClient if tamper or duplicate else PromptABClient)
                self.assertEqual(result["attempted"],len(requests))
                self.assertTrue(load(out/"cleanup.json")["thread_stopped"])
                rows=load(out/"results.json")
                for index,payload in enumerate(requests):
                    case=plan["cases"][index]
                    self.assertEqual(payload["messages"][0]["content"],case["prompt"])
                    self.assertEqual(rows[index]["prompt"],case["prompt"])
                    self.assertEqual(rows[index]["profile"],case["profile"])
                if not tamper and not duplicate and len(rows)>1:
                    self.assertTrue(rows[1]["truncation_guard_passed"])
                    self.assertNotIn("PARTIAL",rows[1]["ui"]["translated"])
                self.assertEqual(translation_system_prompt("en","zh"),
                    next(c["prompt"] for c in plan["cases"] if c["source"]=="en" and c["profile"]=="A"))
                return result
        finally:
            server.shutdown();server.server_close();thread.join(2)

    def test_exact_24_profile_payloads_and_partial_not_displayed(self):
        r=self.exercise();self.assertEqual(r["attempted"],24);self.assertEqual(r["status"],"complete")
        self.assertEqual(r["normal_copyable_subtitles"],23)

    def test_rate_limit_stops_without_retry(self):
        r=self.exercise(status_at=3);self.assertEqual(r["attempted"],3);self.assertEqual(r["stop_reason"],"http_429")

    def test_unplanned_case_never_sends_http(self):
        # BlockerClient's post-result route lookup also rejects the unknown id;
        # bounded runner records it and stops with zero HTTP attempts.
        r=self.exercise(tamper=True);self.assertEqual(r["attempted"],0);self.assertEqual(r["status"],"stopped_incomplete")

    def test_duplicate_profile_cannot_retry(self):
        r=self.exercise(duplicate=True);self.assertEqual(r["attempted"],1);self.assertEqual(r["status"],"stopped_incomplete")


if __name__=="__main__":unittest.main()
