import json
from pathlib import Path
import tempfile
import unittest

from scripts.validate_multilingual_live import CallBudget, load_config


class LiveEvaluationBudgetTest(unittest.TestCase):
    def test_attempts_persist_before_http_and_cannot_exceed_cap_on_resume(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"budget.json"
            budget = CallBudget(path, limit=2)
            budget.reserve("timeout-still-counts")
            budget = CallBudget(path, limit=2)
            budget.reserve("second")
            with self.assertRaisesRegex(RuntimeError, "cap reached"):
                budget.reserve("must-not-send")
            self.assertEqual(len(json.loads(path.read_text())["attempts"]), 2)
            with self.assertRaises(ValueError):
                CallBudget(path, limit=61)

    def test_uncertain_cost_stops_without_resetting_existing_ledger(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"budget.json"
            write = {"model": "tencent/Hunyuan-MT-7B", "estimated_cost_cny": 5, "attempts": []}
            path.write_text(json.dumps(write))
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "cannot be confirmed"):
                CallBudget(path)
            self.assertEqual(path.read_bytes(), before)

    def test_no_provider_model_or_host_substitution(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"settings.json"
            for extra in ({"model":"another-model"}, {"endpoint":"https://another-host/v1"}, {"provider":"google"}):
                data = {"provider":"openai_compatible", "model":"tencent/Hunyuan-MT-7B", "endpoint":"https://api.siliconflow.cn/v1/chat/completions", "api_key":"fixture", **extra}
                path.write_text(json.dumps({"translation":data}))
                before = path.read_bytes()
                with self.assertRaisesRegex(ValueError, "unavailable"):
                    load_config(path)
                self.assertEqual(path.read_bytes(), before)
