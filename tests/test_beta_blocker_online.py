import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from scripts.run_beta_blocker_online import validate_plan, validate_approval, run_cases
from scripts.run_five_language_online import AttemptBudget, MODEL, load
from voxgo.translation import TranslationConfig

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs/testing/evidence/v0.5.3-beta-blockers-2026-10-28/next-online-plan.json"


class BlockerPlanTests(unittest.TestCase):
    def test_only_frozen_twenty_text_scope_and_new_twenty_approval(self):
        plan = load(PLAN)
        validate_plan(plan)
        for field, value in (("hard_request_cap", 300), ("model", "other"), ("new_audio_api_runs", 1)):
            changed = copy.deepcopy(plan)
            changed[field] = value
            with self.assertRaises(ValueError):
                validate_plan(changed)
        changed = copy.deepcopy(plan)
        changed["cases"][1]["id"] = changed["cases"][0]["id"]
        with self.assertRaises(ValueError):
            validate_plan(changed)
        approval = dict(authorized=True, plan_sha256="new", model=MODEL, call_limit=20,
                        confirmed_free_price_date_utc=datetime.now(timezone.utc).date().isoformat())
        validate_approval(approval, "new")
        for kwargs in (dict(call_limit=300), dict(plan_sha256="old"), dict(authorized=False),
                       dict(confirmed_free_price_date_utc="2000-01-01")):
            with self.assertRaises(ValueError):
                validate_approval(dict(approval, **kwargs), "new")

    def exercise_loopback(self, stop_at=None):
        plan = load(PLAN)
        requests = []

        class Fixture(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests.append(payload)
                if len(requests) == stop_at:
                    self.send_error(429, "fixture only")
                    return
                length = len(requests) == 2
                wire = dict(choices=[dict(message=dict(content="fixture-only PARTIAL" if length else "fixture-only complete"),
                                          finish_reason="length" if length else "stop")])
                body = json.dumps(wire).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp)
                approval = dict(authorized=True, plan_sha256="fixture", model=MODEL, call_limit=20)
                budget = AttemptBudget(output / "attempt-ledger.json", approval, "fixture")
                config = TranslationConfig(model=MODEL, api_key="", max_tokens=80, max_concurrent_requests=1,
                    context_messages=0, enable_local_phrase_cache=False,
                    endpoint=f"http://127.0.0.1:{server.server_address[1]}/v1")
                result = run_cases(plan, budget, config, output, platform="offscreen", fixture=True)
                rows = load(output / "results.json")
                self.assertEqual(result["attempted"], len(requests))
                self.assertTrue(load(output / "cleanup.json")["thread_stopped"])
                self.assertTrue(rows[1]["truncation_guard_passed"])
                self.assertEqual(rows[1]["raw_output"], "fixture-only PARTIAL")
                self.assertFalse(rows[1]["ui"]["copyable"])
                self.assertNotIn("PARTIAL", rows[1]["ui"]["translated"])
                self.assertTrue(all(x["model"] == MODEL and x["max_tokens"] == 80 for x in requests))
                self.assertEqual(result["automatic_retries"], 0)
                return result
        finally:
            server.shutdown()
            server.server_close()
            thread.join(2)

    def test_exact_cap_is_complete_and_partial_is_not_a_subtitle(self):
        result = self.exercise_loopback()
        self.assertEqual(result["attempted"], 20)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["normal_copyable_subtitles"], 19)
        self.assertEqual(result["length"], 1)

    def test_rate_limit_preserved_and_stops_remainder_without_retry(self):
        result = self.exercise_loopback(stop_at=3)
        self.assertEqual(result["attempted"], 3)
        self.assertEqual(result["status"], "stopped_incomplete")
        self.assertEqual(result["stop_reason"], "http_429")


if __name__ == "__main__":
    unittest.main()
