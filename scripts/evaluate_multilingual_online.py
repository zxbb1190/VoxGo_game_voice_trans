"""Prepare bilingual review sheets or exercise in-process provider protocol mocks.

No mode reads user settings, environment API keys, or sends network requests.
Mock output is deliberately unrelated to reference meanings and is never quality evidence.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = PROJECT_ROOT / "tests/assets/multilingual_online/cases.json"
ALLOWED_DIRECTIONS = {("en", "zh"), ("zh", "en"), ("ja", "zh"), ("ko", "zh"), ("ru", "zh"), ("zh", "ja")}
CATEGORIES = {"direction", "number", "negation", "condition", "time", "terminology", "completeness"}


def load_cases(path: Path = DEFAULT_CORPUS) -> list[dict]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema_version") != 1 or document.get("human_review") != "pending":
        raise ValueError("Expected version 1 corpus awaiting independent human review")
    cases = document["cases"]
    identifiers, texts = set(), set()
    for case in cases:
        for field in ("id", "source_lang", "target_lang", "split", "scene", "text", "reference_meaning", "key_meanings", "categories"):
            if not case.get(field):
                raise ValueError(f"Missing {field}: {case.get('id')}")
        if case["id"] in identifiers or (case["source_lang"], case["target_lang"], case["text"]) in texts:
            raise ValueError(f"Duplicate case: {case['id']}")
        identifiers.add(case["id"])
        texts.add((case["source_lang"], case["target_lang"], case["text"]))
        if (case["source_lang"], case["target_lang"]) not in ALLOWED_DIRECTIONS:
            raise ValueError(f"Unsupported direction: {case['id']}")
        if case["split"] not in {"dev", "holdout"}:
            raise ValueError(f"Invalid split: {case['id']}")
        if case["scene"] not in {"party_callout", "game_voiceover", "story_dialogue"}:
            raise ValueError(f"Invalid scene: {case['id']}")
        if case.get("human_review") != "pending":
            raise ValueError(f"Source corpus must retain pending human review: {case['id']}")
        if not set(case["categories"]) <= CATEGORIES:
            raise ValueError(f"Invalid category: {case['id']}")
    return cases


class MockResponse:
    status = 200

    def __init__(self, provider: str, output: str):
        self.provider, self.output = provider, output

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def json(self):
        if self.provider == "google":
            return {"data": {"translations": [{"translatedText": self.output}]}}
        return {"choices": [{"message": {"content": self.output}, "finish_reason": "stop"}]}


class MockSession:
    """No sockets: capture only public request bodies, excluding all auth fields."""
    closed = False

    def __init__(self, provider: str, output: str):
        self.provider, self.output = provider, output
        self.requests = []

    def post(self, url, **kwargs):
        if self.provider == "google":
            request = {key: value for key, value in kwargs["params"].items() if key != "key"}
        else:
            request = kwargs["json"]
        self.requests.append(request)
        return MockResponse(self.provider, self.output)


async def mock_translate(case: dict, provider: str) -> tuple[str, dict]:
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from voxgo.translation import GameTranslator, TranslationConfig

    marker = f"MOCK PROTOCOL ONLY {case['id']}"
    session = MockSession(provider, marker)
    config = TranslationConfig(
        provider=provider, api_key="synthetic-mock-key-never-sent", model="mock-model",
        endpoint="https://provider.example.invalid/v1/chat/completions",
        source_lang=case["source_lang"], target_lang=case["target_lang"],
        enable_local_phrase_cache=False, context_messages=0,
    )
    client = GameTranslator(config)
    try:
        with patch.object(client, "_get_session", AsyncMock(return_value=session)):
            result = await client.translate_result(case["text"], case["source_lang"])
        if len(session.requests) != 1 or not result or result.translated != marker:
            raise RuntimeError(f"Mock did not traverse requested provider exactly once: {case['id']}")
        if (result.source_lang, result.target_lang, result.provider) != (case["source_lang"], case["target_lang"], provider):
            raise RuntimeError(f"Direction/provider mismatch: {case['id']}")
        return result.translated, session.requests[0]
    finally:
        await client.close()


async def prepare(cases: list[dict], mode: str, provider: str) -> list[dict]:
    records = []
    for case in cases:
        output, wire = (await mock_translate(case, provider)) if mode == "mock" else (None, None)
        records.append({
            **case,
            "evidence_kind": "in_process_protocol_mock" if mode == "mock" else "review_preparation_only",
            "requested_provider": provider,
            "request": {"text": case["text"], "source_lang": case["source_lang"], "target_lang": case["target_lang"]},
            "captured_public_payload": wire,
            "mock_output": output,
            "translation_output": None,
            "suspected_errors": None,
            "asr_transcript": None, "asr_error_notes": None,
            "asr_latency_ms": None, "translation_latency_ms": None, "e2e_latency_ms": None,
            "cpu_percent": None, "process_rss_mb": None, "game_fps_delta": None,
            "human_review": "pending", "human_key_meaning_verdict": None,
            "human_error_categories": [], "human_notes": None, "reviewer": None, "reviewed_at": None,
        })
    return records


def write_materials(records: list[dict], output: Path, corpus: Path, mode: str, provider: str) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    (output / "review.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8")
    fields = ["id", "source_lang", "target_lang", "split", "scene", "text", "reference_meaning", "key_meanings", "categories", "translation_output", "suspected_errors", "asr_transcript", "asr_error_notes", "asr_latency_ms", "translation_latency_ms", "e2e_latency_ms", "human_review", "human_key_meaning_verdict", "human_error_categories", "human_notes", "reviewer", "reviewed_at", "evidence_kind", "mock_output"]
    with (output / "review.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in records:
            writer.writerow({key: " / ".join(value) if isinstance(value, list) else value for key, value in row.items() if key in fields})
    counts = {}
    for row in records:
        key = f"{row['source_lang']}->{row['target_lang']}:{row['split']}"
        counts[key] = counts.get(key, 0) + 1
    summary = {
        "mode": mode, "provider": provider, "cases": len(records), "counts": counts,
        "corpus_sha256": hashlib.sha256(corpus.read_bytes()).hexdigest(),
        "human_reviewed": 0, "key_meaning_accuracy": None,
        "asr_quality": None, "translation_quality": None,
        "real_asr_p50_ms": None, "real_translation_p50_ms": None, "real_e2e_p50_ms": None,
        "real_e2e_p95_ms": None, "real_game_impact": None,
        "release_acceptance": "incomplete",
        "limitations": ["Authored text/reference meanings await bilingual review", "No recorded game audio", "No real API calls", "Mock output is only protocol/display evidence; no quality or real latency measurement"],
    }
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "build/multilingual-online/review")
    parser.add_argument("--mode", choices=("prep", "mock"), default="prep")
    parser.add_argument("--provider", choices=("openai_compatible", "google"), default="openai_compatible")
    parser.add_argument("--split", choices=("all", "dev", "holdout"), default="all")
    parser.add_argument("--source-lang", choices=("en", "zh", "ja", "ko", "ru"))
    args = parser.parse_args(argv)
    cases = [case for case in load_cases(args.corpus) if (args.split == "all" or case["split"] == args.split) and (not args.source_lang or case["source_lang"] == args.source_lang)]
    if not cases:
        parser.error("No matching evaluation cases")
    records = asyncio.run(prepare(cases, args.mode, args.provider))
    summary = write_materials(records, args.output, args.corpus, args.mode, args.provider)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
