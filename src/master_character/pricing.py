from __future__ import annotations

import json

from pydantic import BaseModel, Field

from master_character.errors import UnknownModelPricingError

MTOK = 1_000_000


class ModelPricing(BaseModel):
    """USD per million tokens for each billable token category."""

    input_per_mtok: float = Field(ge=0)
    output_per_mtok: float = Field(ge=0)
    cache_write_per_mtok: float = Field(ge=0)
    cache_read_per_mtok: float = Field(ge=0)


# Anthropic list prices, USD per MTok, verified against the public pricing page.
# Unknown models are rejected: pricing must never be silently assumed.
DEFAULT_PRICING: dict[tuple[str, str], ModelPricing] = {
    ("anthropic", "claude-sonnet-4-20250514"): ModelPricing(
        input_per_mtok=3.00,
        output_per_mtok=15.00,
        cache_write_per_mtok=3.75,
        cache_read_per_mtok=0.30,
    ),
    ("anthropic", "claude-sonnet-4-5-20250929"): ModelPricing(
        input_per_mtok=3.00,
        output_per_mtok=15.00,
        cache_write_per_mtok=3.75,
        cache_read_per_mtok=0.30,
    ),
    ("anthropic", "claude-3-5-haiku-20241022"): ModelPricing(
        input_per_mtok=0.80,
        output_per_mtok=4.00,
        cache_write_per_mtok=1.00,
        cache_read_per_mtok=0.08,
    ),
    ("anthropic", "claude-haiku-4-5-20251001"): ModelPricing(
        input_per_mtok=1.00,
        output_per_mtok=5.00,
        cache_write_per_mtok=1.25,
        cache_read_per_mtok=0.10,
    ),
    ("anthropic", "claude-opus-4-1-20250805"): ModelPricing(
        input_per_mtok=15.00,
        output_per_mtok=75.00,
        cache_write_per_mtok=18.75,
        cache_read_per_mtok=1.50,
    ),
}


class PricingRegistry:
    def __init__(self, overrides_json: str | None = None):
        self._table: dict[tuple[str, str], ModelPricing] = dict(DEFAULT_PRICING)
        if overrides_json:
            try:
                raw = json.loads(overrides_json)
            except json.JSONDecodeError as exc:
                raise ValueError(f"MASTER_MODEL_PRICING_JSON is not valid JSON: {exc}") from exc
            if not isinstance(raw, dict):
                raise ValueError("MASTER_MODEL_PRICING_JSON must be a JSON object.")
            for key, value in raw.items():
                provider, _, model = key.partition(":")
                if not provider or not model:
                    raise ValueError(
                        f"Pricing override key {key!r} must look like 'provider:model-id'."
                    )
                self._table[(provider, model)] = ModelPricing.model_validate(value)

    def get(self, provider: str, model: str) -> ModelPricing:
        pricing = self._table.get((provider, model))
        if pricing is None:
            raise UnknownModelPricingError(
                f"No pricing configured for {provider}:{model}. "
                "Add it via MASTER_MODEL_PRICING_JSON; costs are never assumed to be zero."
            )
        return pricing

    def cost_usd(
        self,
        provider: str,
        model: str,
        *,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_creation_input_tokens: int = 0,
        cache_read_input_tokens: int = 0,
    ) -> float:
        p = self.get(provider, model)
        return (
            input_tokens * p.input_per_mtok
            + output_tokens * p.output_per_mtok
            + cache_creation_input_tokens * p.cache_write_per_mtok
            + cache_read_input_tokens * p.cache_read_per_mtok
        ) / MTOK
