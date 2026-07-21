from __future__ import annotations

from master_character.config import Settings
from master_character.providers.anthropic import AnthropicProvider
from master_character.providers.base import CognitionProvider
from master_character.providers.mock import MockProvider


def create_provider(settings: Settings) -> CognitionProvider:
    provider = settings.provider.lower().strip()
    if provider == "mock":
        return MockProvider()
    if provider == "anthropic":
        return AnthropicProvider(settings)
    raise ValueError(f"Unsupported MASTER_PROVIDER: {settings.provider}")
