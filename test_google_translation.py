"""
Smoke tests for the Google Cloud Translation provider without a real API call.
"""

import asyncio

from translator import (
    GOOGLE_TRANSLATE_ENDPOINT,
    GameTranslator,
    TranslationConfig,
    normalize_translation_provider,
)


class FakeResponse:
    status = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        return {
            "data": {
                "translations": [
                    {"translatedText": "敌人 &amp; 队友"},
                ]
            }
        }

    async def text(self):
        return ""


class FakeSession:
    closed = False

    def __init__(self):
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return FakeResponse()


async def main():
    assert normalize_translation_provider("google-cloud-translation") == "google"
    assert normalize_translation_provider("openai") == "openai_compatible"

    missing_key = GameTranslator(TranslationConfig(provider="google", api_key=""))
    missing_result = await missing_key.translate("Are they pushing B site now?", "en")
    assert "Google Cloud Translation API Key" in missing_result

    translator = GameTranslator(
        TranslationConfig(
            provider="google",
            api_key="TEST_GOOGLE_KEY",
            source_lang="en",
            target_lang="zh",
        )
    )
    fake_session = FakeSession()
    translator._session = fake_session

    result = await translator.translate("Are they pushing B site now?", "en")
    assert result == "敌人 & 队友"
    assert len(fake_session.calls) == 1

    call = fake_session.calls[0]
    assert call["url"] == GOOGLE_TRANSLATE_ENDPOINT
    assert call["params"] == {
        "key": "TEST_GOOGLE_KEY",
        "q": "Are they pushing B site now?",
        "source": "en",
        "target": "zh-CN",
        "format": "text",
    }
    assert call["headers"]["Content-Type"].startswith("application/json")
    print("google translation provider smoke test passed")


if __name__ == "__main__":
    asyncio.run(main())
