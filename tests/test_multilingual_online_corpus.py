import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.evaluate_multilingual_online import CATEGORIES, DEFAULT_CORPUS, load_cases, prepare, write_materials


class MultilingualOnlineCorpusTest(unittest.TestCase):
    def test_fixed_directions_splits_and_critical_coverage(self):
        cases = load_cases()
        expected = {("en", "zh"): 12, ("zh", "en"): 12, ("ja", "zh"): 20, ("ko", "zh"): 20, ("ru", "zh"): 20, ("zh", "ja"): 12}
        self.assertEqual(len(cases), 96)
        for direction, count in expected.items():
            selected = [row for row in cases if (row["source_lang"], row["target_lang"]) == direction]
            self.assertEqual(len(selected), count)
            dev = [row for row in selected if row["split"] == "dev"]
            holdout = [row for row in selected if row["split"] == "holdout"]
            self.assertEqual(len(dev), count // 2)
            self.assertEqual(len(holdout), count // 2)
            self.assertFalse({row["text"] for row in dev} & {row["text"] for row in holdout})
            for split in (dev, holdout):
                self.assertEqual(set().union(*(set(row["categories"]) for row in split)), CATEGORIES)
        japanese = [row for row in cases if row["source_lang"] == "ja"]
        self.assertEqual({row["scene"] for row in japanese}, {"party_callout", "game_voiceover", "story_dialogue"})
        for language in ("ko", "ru"):
            self.assertTrue(all(row["scene"] == "party_callout" for row in cases if row["source_lang"] == language))

    def test_reject_duplicate_across_splits(self):
        document = json.loads(DEFAULT_CORPUS.read_text(encoding="utf-8"))
        document["cases"][1]["text"] = document["cases"][0]["text"]
        document["cases"][1]["split"] = "holdout"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                load_cases(path)

    def test_preparation_makes_no_requests_and_no_quality_claims(self):
        with patch("aiohttp.ClientSession", side_effect=AssertionError("No network allowed")):
            records = asyncio.run(prepare(load_cases()[:2], "prep", "google"))
        with tempfile.TemporaryDirectory() as directory:
            summary = write_materials(records, Path(directory), DEFAULT_CORPUS, "prep", "google")
            self.assertTrue((Path(directory) / "review.csv").is_file())
        self.assertIsNone(summary["key_meaning_accuracy"])
        self.assertIsNone(summary["real_e2e_p95_ms"])
        self.assertEqual(summary["human_reviewed"], 0)
        self.assertEqual(summary["release_acceptance"], "incomplete")
        self.assertTrue(all(row["translation_output"] is None and row["human_review"] == "pending" for row in records))

    def test_mock_traverses_both_real_provider_paths_without_network(self):
        cases = load_cases()
        selected = [next(row for row in cases if (row["source_lang"], row["target_lang"]) == pair) for pair in (("en", "zh"), ("zh", "en"), ("ja", "zh"), ("ko", "zh"), ("ru", "zh"), ("zh", "ja"))]
        for provider in ("google", "openai_compatible"):
            with self.subTest(provider=provider), patch("aiohttp.ClientSession", side_effect=AssertionError("No network allowed")):
                rows = asyncio.run(prepare(selected, "mock", provider))
            for row in rows:
                self.assertTrue(row["mock_output"].startswith("MOCK PROTOCOL ONLY"))
                self.assertIsNone(row["translation_output"])
                self.assertIsNone(row["translation_latency_ms"])
                self.assertIsNone(row["e2e_latency_ms"])
                self.assertIsNone(row["human_key_meaning_verdict"])
                self.assertNotIn("synthetic-mock-key", json.dumps(row))
                if provider == "google":
                    self.assertEqual(row["captured_public_payload"]["source"], "zh-CN" if row["source_lang"] == "zh" else row["source_lang"])
                    self.assertEqual(row["captured_public_payload"]["target"], "zh-CN" if row["target_lang"] == "zh" else row["target_lang"])
                    self.assertEqual(row["captured_public_payload"]["q"], row["text"])
                else:
                    message = row["captured_public_payload"]["messages"][-1]["content"]
                    self.assertIn(f"<source_text>{row['text']}</source_text>", message)


if __name__ == "__main__":
    unittest.main()
