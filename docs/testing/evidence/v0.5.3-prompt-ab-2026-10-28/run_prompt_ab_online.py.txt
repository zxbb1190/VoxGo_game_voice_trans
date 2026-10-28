"""One separately authorized 24-call Prompt A/B. No formal runtime edits.

Reuse the bounded HTTP ledger and native Qt runner. Only an isolated outgoing
system message is augmented; all formal templates, user state and ASR stay put.
"""
import argparse
import copy
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_beta_blocker_online import BlockerClient, ENDPOINT, SETTINGS, run_cases
from scripts.run_five_language_online import (
    AttemptBudget, MeasuredClient, CURRENT, MODEL, atomic, claim_run, credentials, load, sha,
)
from voxgo.translation.prompt import translation_system_prompt

BASE_HEAD = "97d8bbfe"
FROZEN = ROOT / "docs/testing/evidence/v0.5.3-beta-final-2026-10-28"
PLAN_SHA = "01ea5cf1fee5dc62ec8baa8225f1ad70336fdaef3b66b80076c3546a3b8353a7"
APPEND_SHA = "741554e91528f34b7fb1ee4a9d51741b7e95dfd3b8575e7b1924a129f32c9f04"
OUTPUT = ROOT / "build/prompt-ab-live-20261028-24"


def compile_plan(path):
    if sha(path) != PLAN_SHA or sha(FROZEN / "semantic-guard-v1.append.txt") != APPEND_SHA:
        raise ValueError("Frozen 12-text/24-request scope or candidate changed")
    source = load(path)
    if (source.get("hard_cap") != 24 or source.get("planned_requests") != 24
            or source.get("retries") != 0 or source.get("model") != MODEL
            or len(source.get("cases", [])) != 12):
        raise ValueError("Only the authorized 24-call plan is allowed")
    snapshots = {(r["source"], r["target"]): r for r in load(FROZEN / "prompt-candidates-offline.json")["rendered"]}
    append = (FROZEN / "semantic-guard-v1.append.txt").read_text("utf-8")
    cases = []
    for index, case in enumerate(source["cases"]):
        base = translation_system_prompt(case["source"], case["target"])
        snapshot = snapshots[(case["source"], case["target"])]
        if base != snapshot["baseline"] or base + append != snapshot["candidate"]:
            raise ValueError("Formal prompt or frozen candidate differs")
        for profile in ("AB" if index % 2 == 0 else "BA"):
            cases.append(dict(id=case["id"] + "-" + profile, base_case_id=case["id"],
                source=case["source"], target=case["target"], input=case["text"],
                kind="prompt_ab_" + profile, profile=profile,
                prompt=base if profile == "A" else base + append,
                critical_meanings=case["critical_facts"], source_human_review=case["source_human_review"]))
    return dict(cases=cases, model=MODEL, config=SETTINGS, source_plan_sha256=PLAN_SHA,
                candidate_append_sha256=APPEND_SHA, automatic_retries=0)


def validate_approval(approval, plan_hash, price):
    today = datetime.now(timezone.utc).date().isoformat()
    if (approval.get("authorized") is not True or approval.get("plan_sha256") != plan_hash
            or approval.get("candidate_append_sha256") != APPEND_SHA
            or approval.get("model") != MODEL or approval.get("call_limit") != 24
            or approval.get("output_directory") != str(OUTPUT.relative_to(ROOT)).replace("\\", "/")
            or approval.get("confirmed_free_price_date_utc") != today
            or price.get("model") != MODEL or price.get("http_status") != 200
            or not price.get("checked_at_utc", "").startswith(today)
            or price.get("input_cny_per_million") != 0 or price.get("output_cny_per_million") != 0
            or price.get("url") != "https://www.siliconflow.cn/pricing"):
        raise ValueError("New matching 24-attempt authorization and current free pricing required")


class PromptABClient(BlockerClient):
    def __init__(self, config, budget, cases, *, fixture=False):
        super().__init__(config, budget, cases, fixture=fixture)
        self.phase = "prompt_ab_text"
        self.sent_cases = set()

    async def _get_session(self):
        # Keep the durable pre-POST counter, bypass only the old 20-case prompt
        # guard, replacing it with this stricter frozen-pair/profile guard.
        session = await MeasuredClient._get_session(self)
        if not getattr(session, "_prompt_ab_guard", False):
            original = session.post

            def post(url, *args, **kwargs):
                context = CURRENT.get() or {}
                case = self.allowed_cases.get(context.get("case_id"))
                payload = kwargs.get("json") or {}
                messages = payload.get("messages") or []
                if (not case or case["id"] in self.sent_cases
                        or context.get("source") != case["source"] or context.get("target") != case["target"]
                        or context.get("input") != case["input"] or payload.get("model") != MODEL
                        or payload.get("max_tokens") != 80 or payload.get("temperature") != 0
                        or payload.get("stream") is not False or len(messages) != 2
                        or messages[0] != {"role": "system", "content": translation_system_prompt(case["source"], case["target"])}
                        or messages[1] != {"role": "user", "content": (
                            f"请将 <source_text> 中的{self._language_name(case['source'])}"
                            f"翻译成{self._language_name(case['target'])}，只输出译文。\n"
                            f"<source_text>{case['input']}</source_text>")}
                        or (not self.fixture and str(url) != ENDPOINT)):
                    raise ValueError("Duplicate/unplanned A/B payload; no request sent")
                outgoing = copy.deepcopy(payload)
                outgoing["messages"][0]["content"] = case["prompt"]
                kwargs["json"] = outgoing
                context.update(prompt=case["prompt"], profile=case["profile"], base_case_id=case["base_case_id"])
                self.sent_cases.add(case["id"])
                return original(url, *args, **kwargs)

            session.post = post
            session._prompt_ab_guard = True
        return session

    @staticmethod
    def _language_name(language):
        return {"en": "英文", "zh": "中文", "ja": "日文", "ko": "韩文", "ru": "俄文"}[language]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("plan", "approval", "price", "settings", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--run-live", action="store_true")
    args = parser.parse_args()
    if not args.run_live:
        parser.error("Explicit --run-live required")
    plan = compile_plan(args.plan)
    approval, price = load(args.approval), load(args.price)
    validate_approval(approval, sha(args.plan), price)
    if approval.get("price_sha256") != sha(args.price):
        raise ValueError("Price evidence changed")
    if args.output.resolve() != OUTPUT.resolve() or args.output.exists():
        raise ValueError("Only the fresh fixed output directory is allowed")
    if subprocess.check_output(["git", "diff", BASE_HEAD, "--", "voxgo", "config.example.json"], cwd=ROOT):
        raise ValueError("Formal runtime/defaults differ from authorized baseline")
    config = credentials(args.settings)  # Strict fixed-provider read-only loader.
    for key, value in SETTINGS.items():
        if key != "local_phrase_cache":
            setattr(config, key, value)
    config.enable_local_phrase_cache = False
    before = sha(args.settings)
    budget = AttemptBudget(args.output / "attempt-ledger.json", approval, sha(args.plan))
    claim_run(args.approval, args.output, sha(args.plan))
    args.output.mkdir()
    for name, value in (("authorization.json", approval), ("plan.json", plan), ("price.json", price)):
        atomic(args.output / name, value)
    try:
        summary = run_cases(plan, budget, config, args.output, client_factory=PromptABClient)
        summary["scope"] = "24 text A/B -> fixed real Provider -> native Qt; no ASR/Full EXE"
        atomic(args.output / "summary.json", summary)
    finally:
        atomic(args.output / "provenance.json", dict(plan_sha256=sha(args.plan), append_sha256=APPEND_SHA,
            settings_sha256_before=before, settings_sha256_after=sha(args.settings), settings_unchanged=sha(args.settings)==before,
            base_head=BASE_HEAD, runtime_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
            script_sha256=sha(__file__), native_runner_sha256=sha(ROOT/"scripts/run_beta_blocker_online.py"),
            api_requests=len(budget.data["attempts"]), asr_runs=0, retries=0, formal_prompt_changed=False,
            source_human_review="pending", target_human_review="pending"))


if __name__ == "__main__":
    main()
