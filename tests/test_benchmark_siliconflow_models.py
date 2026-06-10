import importlib.util
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "diagnostics" / "benchmark_siliconflow_models.py"


def _load_benchmark_module():
    spec = importlib.util.spec_from_file_location("benchmark_siliconflow_models", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


benchmark = _load_benchmark_module()


class BenchmarkSiliconFlowModelsTest(unittest.TestCase):
    def test_split_models_trims_and_falls_back_to_defaults(self):
        self.assertEqual(benchmark.split_models(" model-a, ,model-b "), ["model-a", "model-b"])
        self.assertEqual(benchmark.split_models(""), benchmark.CANDIDATES)

    def test_parse_args_accepts_models_texts_and_safe_minimums(self):
        args = benchmark.parse_args([
            "--models",
            "model-a,model-b",
            "--text",
            "rush B",
            "--text",
            "rotate now",
            "--source-lang",
            "en",
            "--target-lang",
            "zh",
            "--repeat",
            "0",
            "--timeout",
            "0",
            "--max-tokens",
            "0",
        ])

        self.assertEqual(args.models, ["model-a", "model-b"])
        self.assertEqual(args.text, ["rush B", "rotate now"])
        self.assertEqual(args.source_lang, "en")
        self.assertEqual(args.target_lang, "zh")
        self.assertEqual(args.repeat, 1)
        self.assertEqual(args.timeout, 1.0)
        self.assertEqual(args.max_tokens, 1)

    def test_build_payload_uses_requested_direction_and_generation_options(self):
        payload = benchmark.build_payload(
            "model-a",
            "rush B",
            source_lang="en",
            target_lang="zh",
            max_tokens=32,
            temperature=0.2,
        )

        self.assertEqual(payload["model"], "model-a")
        self.assertEqual(payload["max_tokens"], 32)
        self.assertEqual(payload["temperature"], 0.2)
        self.assertFalse(payload["stream"])
        self.assertFalse(payload["enable_thinking"])
        user_message = payload["messages"][1]["content"]
        self.assertIn("Translate from English to Chinese", user_message)
        self.assertIn("rush B", user_message)


if __name__ == "__main__":
    unittest.main()
