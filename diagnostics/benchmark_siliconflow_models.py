"""
Compare SiliconFlow model latency for short translation prompts.
"""

import argparse
import asyncio
import json
import time


CANDIDATES = [
    "tencent/Hunyuan-MT-7B",
    "Qwen/Qwen3.5-4B",
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen2.5-3B-Instruct",
    "Qwen/Qwen2.5-1.5B-Instruct",
    "THUDM/glm-4-9b-chat",
    "deepseek-ai/DeepSeek-V3",
]
DEFAULT_TEXT = "我都搞不懂为什么要玩部落。"
LANGUAGE_NAMES = {
    "en": "English",
    "zh": "Chinese",
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Compare SiliconFlow/OpenAI-compatible model latency.")
    parser.add_argument(
        "--models",
        default=",".join(CANDIDATES),
        help="Comma-separated model names. Defaults to the built-in SiliconFlow candidate list.",
    )
    parser.add_argument(
        "--text",
        action="append",
        help="Text to translate. Can be passed multiple times. Defaults to a short Chinese game-chat sample.",
    )
    parser.add_argument("--source-lang", default="zh", choices=sorted(LANGUAGE_NAMES), help="Source language.")
    parser.add_argument("--target-lang", default="en", choices=sorted(LANGUAGE_NAMES), help="Target language.")
    parser.add_argument("--repeat", type=int, default=1, help="Runs per model/text pair.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds.")
    parser.add_argument("--max-tokens", type=int, default=80, help="Chat completion max_tokens.")
    parser.add_argument("--temperature", type=float, default=0.1, help="Chat completion temperature.")
    parser.add_argument("--endpoint", default="", help="Override translation endpoint from config.json.")
    parser.add_argument("--api-key", default="", help="Override API key from config.json.")
    args = parser.parse_args(argv)
    args.models = split_models(args.models)
    args.text = [text for text in (args.text or [DEFAULT_TEXT]) if str(text or "").strip()]
    args.repeat = max(1, int(args.repeat if args.repeat is not None else 1))
    args.timeout = max(1.0, float(args.timeout if args.timeout is not None else 10.0))
    args.max_tokens = max(1, int(args.max_tokens if args.max_tokens is not None else 80))
    return args


def split_models(value: str) -> list:
    models = [part.strip() for part in str(value or "").split(",") if part.strip()]
    return models or list(CANDIDATES)


def build_payload(model, text, source_lang="zh", target_lang="en", max_tokens=80, temperature=0.1):
    source = LANGUAGE_NAMES.get(source_lang, source_lang or "source language")
    target = LANGUAGE_NAMES.get(target_lang, target_lang or "target language")
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a realtime game subtitle translator. "
                    "Only output the translated text, with no notes or extra formatting."
                ),
            },
            {
                "role": "user",
                "content": f"Translate from {source} to {target}:\n{text}",
            },
        ],
        "max_tokens": max(1, int(max_tokens or 80)),
        "temperature": float(temperature or 0.0),
        "stream": False,
        "enable_thinking": False,
    }


async def try_model(
    session,
    endpoint,
    api_key,
    model,
    text,
    source_lang="zh",
    target_lang="en",
    max_tokens=80,
    temperature=0.1,
    run_index=1,
    total_runs=1,
):
    payload = build_payload(model, text, source_lang, target_lang, max_tokens, temperature)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    run_label = f" run {run_index}/{total_runs}" if total_runs > 1 else ""
    started = time.time()
    try:
        async with session.post(endpoint, headers=headers, json=payload) as response:
            body = await response.text()
            elapsed = time.time() - started
            if response.status != 200:
                print(f"{model}{run_label}: HTTP {response.status} in {elapsed:.2f}s {body[:180]}")
                return
            data = json.loads(body)
            content = data["choices"][0]["message"].get("content", "")
            print(f"{model}{run_label}: OK {elapsed:.2f}s -> {content[:80]}")
    except Exception as exc:
        elapsed = time.time() - started
        print(f"{model}{run_label}: FAIL {elapsed:.2f}s {type(exc).__name__}: {exc}")


async def main(argv=None):
    args = parse_args(argv)
    try:
        import aiohttp
    except ImportError as exc:
        raise SystemExit("Missing aiohttp. Run `pip install -r requirements.txt` first.") from exc

    from _helpers import load_translation_config, normalized_chat_endpoint, require_real_api_key

    overrides = {}
    if args.api_key:
        overrides["api_key"] = args.api_key
    if args.endpoint:
        overrides["endpoint"] = args.endpoint
    config = load_translation_config(**overrides)
    if config.provider != "openai_compatible":
        raise SystemExit("Set translation.provider to openai_compatible in config.json first.")
    require_real_api_key(config.api_key, "SiliconFlow/OpenAI-compatible")

    endpoint = normalized_chat_endpoint(config.endpoint)
    timeout = aiohttp.ClientTimeout(total=args.timeout)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for run_index in range(1, args.repeat + 1):
            for text in args.text:
                for model in args.models:
                    await try_model(
                        session,
                        endpoint,
                        config.api_key,
                        model,
                        text,
                        args.source_lang,
                        args.target_lang,
                        args.max_tokens,
                        args.temperature,
                        run_index,
                        args.repeat,
                    )


if __name__ == "__main__":
    asyncio.run(main())
