from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest
from pydantic import BaseModel

from master_character.config import Settings
from master_character.domain import ModelTier, ModelUsage
from master_character.errors import (
    MaxTurnsExceededError,
    ProviderHTTPError,
    ProviderResponseError,
    ProviderTimeoutError,
    TaskBudgetExceededError,
    UnknownModelPricingError,
    ZeroCostUsageError,
)
from master_character.pricing import PricingRegistry
from master_character.providers.anthropic import AnthropicProvider
from master_character.store import Store

HAIKU = "claude-3-5-haiku-20241022"


class Out(BaseModel):
    message: str


def make_settings(tmp_path: Path, **overrides) -> Settings:
    defaults = dict(
        MASTER_PROVIDER="anthropic",
        ANTHROPIC_API_KEY="sk-test-secret-key-000",
        MASTER_DB_PATH=tmp_path / "provider.db",
        MASTER_WORKSPACE=tmp_path / "workspace",
        MASTER_WORKER_MODEL=HAIKU,
        MASTER_PROMPT_CACHE=False,
        MASTER_PROVIDER_MAX_TOKENS=100,
        MASTER_PROVIDER_MAX_RETRIES=3,
    )
    defaults.update(overrides)
    return Settings(**defaults)


def api_json(
    content: list[dict],
    stop_reason: str = "end_turn",
    usage: dict | None = None,
) -> dict:
    return {
        "content": content,
        "stop_reason": stop_reason,
        "usage": usage or {"input_tokens": 1000, "output_tokens": 50},
    }


def final_block(payload: dict, block_id: str = "tu_final") -> dict:
    return {
        "type": "tool_use",
        "id": block_id,
        "name": "emit_structured_result",
        "input": payload,
    }


class ScriptedTransport(httpx.AsyncBaseTransport):
    """Returns scripted responses in order; records request bodies."""

    def __init__(self, script):
        self.script = list(script)
        self.requests: list[dict] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(json.loads(request.content.decode()))
        step = self.script.pop(0) if len(self.script) > 1 else self.script[0]
        if isinstance(step, Exception):
            raise step
        if callable(step):
            return step()
        return step


async def no_sleep(_delay: float) -> None:
    return None


def build_provider(settings: Settings, transport, store: Store | None = None) -> AnthropicProvider:
    return AnthropicProvider(
        settings, store=store, transport=transport, sleep=no_sleep, rng=lambda: 0.5
    )


def build_store(settings: Settings) -> Store:
    store = Store(settings.db_path)
    store.initialize()
    return store


async def call(provider: AnthropicProvider, **kwargs):
    params = dict(
        system="s",
        prompt="p",
        response_model=Out,
        tier=ModelTier.WORKER,
        max_turns=4,
        cost_budget_usd=0.05,
    )
    params.update(kwargs)
    return await provider.structured(**params)


# --- pricing -----------------------------------------------------------------


def test_cost_calculation_is_accurate():
    registry = PricingRegistry()
    cost = registry.cost_usd("anthropic", HAIKU, input_tokens=1000, output_tokens=500)
    assert cost == pytest.approx((1000 * 0.80 + 500 * 4.00) / 1_000_000)


def test_cache_tokens_are_billed():
    registry = PricingRegistry()
    cost = registry.cost_usd(
        "anthropic",
        HAIKU,
        cache_creation_input_tokens=1000,
        cache_read_input_tokens=2000,
    )
    assert cost == pytest.approx((1000 * 1.00 + 2000 * 0.08) / 1_000_000)


def test_unknown_model_pricing_fails_closed():
    registry = PricingRegistry()
    with pytest.raises(UnknownModelPricingError):
        registry.get("anthropic", "claude-imaginary-9")


def test_pricing_overrides_are_applied():
    registry = PricingRegistry(
        '{"anthropic:custom-model": {"input_per_mtok": 1, "output_per_mtok": 2, '
        '"cache_write_per_mtok": 1.25, "cache_read_per_mtok": 0.1}}'
    )
    cost = registry.cost_usd("anthropic", "custom-model", input_tokens=1_000_000)
    assert cost == pytest.approx(1.0)


# --- happy path and accounting ------------------------------------------------


async def test_success_accumulates_all_token_categories(tmp_path):
    settings = make_settings(tmp_path)
    usage = {
        "input_tokens": 1000,
        "output_tokens": 500,
        "cache_creation_input_tokens": 300,
        "cache_read_input_tokens": 700,
    }
    transport = ScriptedTransport(
        [httpx.Response(200, json=api_json([final_block({"message": "ok"})], "tool_use", usage))]
    )
    provider = build_provider(settings, transport)
    result, recorded = await call(provider)
    assert result.message == "ok"
    assert recorded.input_tokens == 1000
    assert recorded.output_tokens == 500
    assert recorded.cache_creation_input_tokens == 300
    assert recorded.cache_read_input_tokens == 700
    assert recorded.calls == 1
    expected = (1000 * 0.80 + 500 * 4.00 + 300 * 1.00 + 700 * 0.08) / 1_000_000
    assert recorded.estimated_cost_usd == pytest.approx(expected)


async def test_unknown_model_refuses_before_any_call(tmp_path):
    settings = make_settings(tmp_path, MASTER_WORKER_MODEL="claude-imaginary-9")
    transport = ScriptedTransport([httpx.Response(200, json=api_json([]))])
    provider = build_provider(settings, transport)
    with pytest.raises(UnknownModelPricingError):
        await call(provider)
    assert transport.requests == []


async def test_zero_cost_success_is_rejected_in_live_mode(tmp_path):
    settings = make_settings(tmp_path)
    usage = {"input_tokens": 0, "output_tokens": 0}
    transport = ScriptedTransport(
        [httpx.Response(200, json=api_json([final_block({"message": "ok"})], "tool_use", usage))]
    )
    store = build_store(settings)
    provider = build_provider(settings, transport, store)
    with pytest.raises(ZeroCostUsageError):
        await call(provider)
    failures = store.list_provider_failures()
    assert failures and failures[0].exception_category == "zero_cost_usage"


# --- budget enforcement --------------------------------------------------------


async def test_budget_refusal_before_first_call(tmp_path):
    settings = make_settings(tmp_path)
    transport = ScriptedTransport([httpx.Response(200, json=api_json([]))])
    store = build_store(settings)
    provider = build_provider(settings, transport, store)
    with pytest.raises(TaskBudgetExceededError):
        await call(provider, cost_budget_usd=0.0000001)
    assert transport.requests == []
    failures = store.list_provider_failures()
    assert failures and failures[0].retry_decision == "refused_before_call"


async def test_budget_refusal_before_continuation(tmp_path):
    settings = make_settings(tmp_path)
    # First call is affordable but consumes nearly the whole budget; the
    # continuation must be refused before it is sent.
    usage = {"input_tokens": 12000, "output_tokens": 100}
    tool_use = {"type": "tool_use", "id": "tu_1", "name": "some_tool", "input": {}}
    transport = ScriptedTransport(
        [httpx.Response(200, json=api_json([tool_use], "tool_use", usage))]
    )
    store = build_store(settings)
    provider = build_provider(settings, transport, store)

    async def executor(name, args):
        return {"ok": True}

    with pytest.raises(TaskBudgetExceededError):
        await call(
            provider,
            cost_budget_usd=0.0105,
            tools=[{"name": "some_tool", "description": "d", "input_schema": {"type": "object"}}],
            tool_executor=executor,
        )
    assert len(transport.requests) == 1
    # spend on the first call was still persisted with the failure
    assert store.task_cost("") == 0.0
    rows = store.list_provider_failures()
    assert rows[0].retry_decision == "refused_before_call"
    assert rows[0].input_tokens == 12000


async def test_prior_task_cost_counts_against_budget(tmp_path):
    settings = make_settings(tmp_path)
    store = build_store(settings)
    store.record_usage(
        ModelUsage(
            provider="anthropic",
            model=HAIKU,
            input_tokens=1,
            estimated_cost_usd=0.049,
            correlation_id="task_1",
        )
    )
    transport = ScriptedTransport([httpx.Response(200, json=api_json([]))])
    provider = build_provider(settings, transport, store)
    with pytest.raises(TaskBudgetExceededError):
        await call(provider, cost_budget_usd=0.049, correlation_id="task_1")
    assert transport.requests == []


# --- retries -------------------------------------------------------------------


def ok_response():
    return httpx.Response(
        200, json=api_json([final_block({"message": "ok"})], "tool_use")
    )


async def test_429_retries_then_succeeds(tmp_path):
    settings = make_settings(tmp_path)
    transport = ScriptedTransport(
        [httpx.Response(429, json={}), httpx.Response(429, json={}), ok_response()]
    )
    provider = build_provider(settings, transport)
    result, usage = await call(provider)
    assert result.message == "ok"
    assert usage.retries == 2
    assert len(transport.requests) == 3


async def test_429_exhaustion_raises_and_persists(tmp_path):
    settings = make_settings(tmp_path)
    transport = ScriptedTransport([httpx.Response(429, json={})])
    store = build_store(settings)
    provider = build_provider(settings, transport, store)
    with pytest.raises(ProviderHTTPError) as info:
        await call(provider)
    assert info.value.status_code == 429
    assert info.value.retryable is True
    assert len(transport.requests) == settings.provider_max_retries + 1
    failures = store.list_provider_failures()
    assert failures[0].http_status == 429
    assert failures[0].retry_decision == "retries_exhausted"


async def test_retryable_5xx_recovers(tmp_path):
    settings = make_settings(tmp_path)
    transport = ScriptedTransport([httpx.Response(500, json={}), ok_response()])
    provider = build_provider(settings, transport)
    result, usage = await call(provider)
    assert result.message == "ok"
    assert usage.retries == 1


async def test_non_retryable_4xx_fails_immediately(tmp_path):
    settings = make_settings(tmp_path)
    transport = ScriptedTransport([httpx.Response(400, json={"error": "bad request"})])
    store = build_store(settings)
    provider = build_provider(settings, transport, store)
    with pytest.raises(ProviderHTTPError) as info:
        await call(provider)
    assert info.value.retryable is False
    assert len(transport.requests) == 1
    assert store.list_provider_failures()[0].retry_decision == "not_retryable"


async def test_timeout_is_retried_then_raised(tmp_path):
    settings = make_settings(tmp_path)
    transport = ScriptedTransport([httpx.ReadTimeout("slow")])
    store = build_store(settings)
    provider = build_provider(settings, transport, store)
    with pytest.raises(ProviderTimeoutError):
        await call(provider)
    assert len(transport.requests) == settings.provider_max_retries + 1
    assert store.list_provider_failures()[0].exception_category == "timeout"


async def test_malformed_json_is_classified(tmp_path):
    settings = make_settings(tmp_path)
    transport = ScriptedTransport([httpx.Response(200, text="not-json{{{")])
    provider = build_provider(settings, transport)
    with pytest.raises(ProviderResponseError):
        await call(provider)
    assert len(transport.requests) == settings.provider_max_retries + 1


# --- stop reasons and tool discipline -------------------------------------------


async def test_max_tokens_truncation_gets_a_bounded_continuation(tmp_path):
    settings = make_settings(tmp_path)
    truncated = httpx.Response(
        200, json=api_json([{"type": "text", "text": "partial"}], "max_tokens")
    )
    transport = ScriptedTransport([truncated, ok_response()])
    provider = build_provider(settings, transport)
    result, usage = await call(provider)
    assert result.message == "ok"
    assert usage.calls == 2
    nudge = transport.requests[1]["messages"][-1]
    assert "truncated" in nudge["content"]


async def test_pause_turn_continues_without_injected_user_message(tmp_path):
    settings = make_settings(tmp_path)
    paused = httpx.Response(
        200, json=api_json([{"type": "text", "text": "thinking..."}], "pause_turn")
    )
    transport = ScriptedTransport([paused, ok_response()])
    provider = build_provider(settings, transport)
    result, usage = await call(provider)
    assert result.message == "ok"
    assert usage.calls == 2
    assert transport.requests[1]["messages"][-1]["role"] == "assistant"


async def test_malformed_tool_input_returns_error_result(tmp_path):
    settings = make_settings(tmp_path)
    bad_tool = {"type": "tool_use", "id": "tu_bad", "name": "some_tool", "input": "not-an-object"}
    transport = ScriptedTransport(
        [httpx.Response(200, json=api_json([bad_tool], "tool_use")), ok_response()]
    )
    provider = build_provider(settings, transport)

    async def executor(name, args):
        raise AssertionError("executor must not be called with malformed input")

    result, _ = await call(
        provider,
        tools=[{"name": "some_tool", "description": "d", "input_schema": {"type": "object"}}],
        tool_executor=executor,
    )
    assert result.message == "ok"
    follow_up = transport.requests[1]["messages"][-1]["content"][0]
    assert follow_up["is_error"] is True
    assert follow_up["tool_use_id"] == "tu_bad"


async def test_unknown_tool_name_returns_error_result(tmp_path):
    settings = make_settings(tmp_path)
    ghost = {"type": "tool_use", "id": "tu_ghost", "name": "bogus_tool", "input": {}}
    transport = ScriptedTransport(
        [httpx.Response(200, json=api_json([ghost], "tool_use")), ok_response()]
    )
    provider = build_provider(settings, transport)
    result, _ = await call(provider)
    assert result.message == "ok"
    follow_up = transport.requests[1]["messages"][-1]["content"][0]
    assert follow_up["is_error"] is True
    assert "Unknown tool" in follow_up["content"]


async def test_missing_tool_use_id_is_a_protocol_error(tmp_path):
    settings = make_settings(tmp_path)
    no_id = {"type": "tool_use", "name": "some_tool", "input": {}}
    transport = ScriptedTransport([httpx.Response(200, json=api_json([no_id], "tool_use"))])
    provider = build_provider(settings, transport)
    with pytest.raises(ProviderResponseError):
        await call(provider)


async def test_invalid_structured_output_is_fed_back_then_recovers(tmp_path):
    settings = make_settings(tmp_path)
    invalid = httpx.Response(
        200, json=api_json([final_block({"wrong_field": 1})], "tool_use")
    )
    transport = ScriptedTransport([invalid, ok_response()])
    provider = build_provider(settings, transport)
    result, usage = await call(provider)
    assert result.message == "ok"
    assert usage.calls == 2
    follow_up = transport.requests[1]["messages"][-1]["content"][0]
    assert follow_up["is_error"] is True
    assert "Invalid Out" in follow_up["content"]


async def test_max_turn_exhaustion_is_typed_and_persisted(tmp_path):
    settings = make_settings(tmp_path)
    chatty = httpx.Response(200, json=api_json([{"type": "text", "text": "hello"}], "end_turn"))
    transport = ScriptedTransport([chatty])
    store = build_store(settings)
    provider = build_provider(settings, transport, store)
    with pytest.raises(MaxTurnsExceededError):
        await call(provider, max_turns=2)
    assert len(transport.requests) == 2
    failures = store.list_provider_failures()
    assert failures[0].exception_category == "max_turns_exceeded"
    # spend from the failed exchange is still in the ledger
    assert store.daily_cost() > 0


async def test_cancellation_persists_partial_usage(tmp_path):
    settings = make_settings(tmp_path)
    tool_use = {"type": "tool_use", "id": "tu_1", "name": "some_tool", "input": {}}
    transport = ScriptedTransport(
        [httpx.Response(200, json=api_json([tool_use], "tool_use"))]
    )
    store = build_store(settings)
    provider = build_provider(settings, transport, store)
    started = asyncio.Event()

    async def hanging_executor(name, args):
        started.set()
        await asyncio.Event().wait()

    task = asyncio.create_task(
        call(
            provider,
            tools=[{"name": "some_tool", "description": "d", "input_schema": {"type": "object"}}],
            tool_executor=hanging_executor,
        )
    )
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    failures = store.list_provider_failures()
    assert failures[0].exception_category == "cancelled"
    assert store.daily_cost() > 0


async def test_failure_records_never_contain_the_api_key(tmp_path):
    settings = make_settings(tmp_path)
    leaky = httpx.Response(
        400, text=f"invalid x-api-key {settings.anthropic_api_key} rejected"
    )
    transport = ScriptedTransport([leaky])
    store = build_store(settings)
    provider = build_provider(settings, transport, store)
    with pytest.raises(ProviderHTTPError):
        await call(provider)
    record = store.list_provider_failures()[0]
    assert settings.anthropic_api_key not in record.sanitized_message
    assert "[REDACTED]" in record.sanitized_message
