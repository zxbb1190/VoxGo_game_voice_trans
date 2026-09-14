from .base import TRANSLATION_PROVIDERS, normalize_translation_provider
from .google import GoogleCloudProvider
from .local import LocalTranslationProvider
from .openai_compatible import OpenAICompatibleProvider


PROVIDER_CLASSES = {
    "openai_compatible": OpenAICompatibleProvider,
    "google": GoogleCloudProvider,
    "local": LocalTranslationProvider,
}


def create_provider(config):
    provider = normalize_translation_provider(getattr(config, "provider", "openai_compatible"))
    return PROVIDER_CLASSES.get(provider, OpenAICompatibleProvider)(config)

