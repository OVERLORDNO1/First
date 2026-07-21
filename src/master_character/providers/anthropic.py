from __future__ import annotations

import asyncio
import json
import random
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from master_character.config import Settings
from master_character.domain import ModelTier, ModelUsage, ProviderFailureRecord
from master_character.errors import (
    MaxTurnsExceededError,
    ProviderError,
    ProviderHTTPError,
    ProviderResponseError,
    ProviderTimeoutError,
    TaskBudgetExceededError,
    ZeroCostUsageError,
)
from master_character.pricing import MTOK, PricingRegistry
from master_character.providers.base import CognitionProvider, ToolExecutor
from master_character.store import Store

T = TypeVar("T", bound=BaseModel)

RETRYABLE_STATUS = {429, 500, 502, 503, 504, 529}
FINAL_TOOL_NAME = "emit_structured_result"


class AnthropicProvider(CognitionProvider):
    def __init__(
        self,
        settings: Settings,
        store: Store | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        rng: Callable[[], float] = random.random,
    ):
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when MASTER_PROVIDER=anthropic")
        self.settings = settings
        self.store = store
        self.pricing = PricingRegistry(settings.model_pricing_json)
        self._transport = transport
        self._sleep = sleep
        self._rng = rng

    def _model_for(self, tier: ModelTier) -> str:
        return {
            ModelTier.REASONER: self.settings.reasoning_model,
            ModelTier.WORKER: self.settings.worker_model,
            ModelTier.CRITIC: self.settings.critic_model,
        }[tier]

    def _sanitize(self, message: str, limit: int = 500) -> str:
        key = self.settings.anthropic_api_key or ""
        if key:
            message = message.replace(key, "[REDACTED]")
        return message[:limit]

    def _worst_case_call_cost(self, model: str, estimated_input_tokens: int) -> float:
        pricing = self.pricing.get("anthropic", model)
        input_rate = pricing.input_per_mtok
        if self.settings.prompt_cache:
            input_rate = max(input_rate, pricing.cache_write_per_mtok)
        return (
            estimated_input_tokens * input_rate
            + self.settings.provider_max_tokens * pricing.output_per_mtok
        ) / MTOK

    async def structured(
        self,
        *,
        system: str,
        prompt: str,
        response_model: type[T],
        tier: ModelTier,
        tools: list[dict[str, Any]] | None = None,
        tool_executor: ToolExecutor | None = None,
        max_turns: int = 6,
        cost_budget_usd: float = 0.25,
        correlation_id: str | None = None,
    ) -> tuple[T, ModelUsage]:
        model = self._model_for(tier)
        final_tool = {
            "name": FINAL_TOOL_NAME,
            "description": "Return the final validated structured result for this task.",
            "input_schema": response_model.model_json_schema(),
        }
        available_tools = [*(tools or []), final_tool]
        known_tool_names = {tool["name"] for tool in available_tools}
        messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]

        totals = ModelUsage(provider="anthropic", model=model, correlation_id=correlation_id)
        prior_task_cost = (
            self.store.task_cost(correlation_id) if self.store and correlation_id else 0.0
        )
        last_stop_reason: str | None = None
        turn = 0

        system_value: Any = system
        if self.settings.prompt_cache:
            system_value = [
                {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
            ]

        headers = {
            "x-api-key": self.settings.anthropic_api_key,
            "anthropic-version": self.settings.anthropic_version,
            "content-type": "application/json",
        }
        timeout = httpx.Timeout(90.0, connect=20.0)

        def fail(
            exc: ProviderError,
            *,
            http_status: int | None = None,
            retry_decision: str | None = None,
        ) -> ProviderError:
            self._persist_failure(
                totals,
                correlation_id=correlation_id,
                http_status=http_status,
                request_turn=turn,
                stop_reason=last_stop_reason,
                retry_decision=retry_decision,
                exception_category=exc.category,
                message=str(exc),
            )
            return exc

        client_kwargs: dict[str, Any] = {
            "base_url": self.settings.anthropic_base_url.rstrip("/"),
            "headers": headers,
            "timeout": timeout,
        }
        if self._transport is not None:
            client_kwargs["transport"] = self._transport

        try:
            async with httpx.AsyncClient(**client_kwargs) as client:
                while turn < max_turns:
                    turn += 1
                    body = {
                        "model": model,
                        "max_tokens": self.settings.provider_max_tokens,
                        "system": system_value,
                        "messages": messages,
                        "tools": available_tools,
                    }
                    accumulated = prior_task_cost + totals.estimated_cost_usd
                    self._enforce_budget(model, body, accumulated, cost_budget_usd, fail)
                    data = await self._post_with_retries(client, body, totals, fail)
                    usage = data.get("usage", {}) or {}
                    totals.input_tokens += int(usage.get("input_tokens", 0) or 0)
                    totals.output_tokens += int(usage.get("output_tokens", 0) or 0)
                    totals.cache_creation_input_tokens += int(
                        usage.get("cache_creation_input_tokens", 0) or 0
                    )
                    totals.cache_read_input_tokens += int(
                        usage.get("cache_read_input_tokens", 0) or 0
                    )
                    totals.calls += 1
                    totals.estimated_cost_usd = self.pricing.cost_usd(
                        "anthropic",
                        model,
                        input_tokens=totals.input_tokens,
                        output_tokens=totals.output_tokens,
                        cache_creation_input_tokens=totals.cache_creation_input_tokens,
                        cache_read_input_tokens=totals.cache_read_input_tokens,
                    )
                    last_stop_reason = data.get("stop_reason")
                    totals.stop_reason = last_stop_reason
                    content = data.get("content", [])
                    if not isinstance(content, list):
                        raise fail(
                            ProviderResponseError(
                                "Anthropic response content is not a list of blocks."
                            )
                        )
                    messages.append({"role": "assistant", "content": content})

                    if last_stop_reason == "pause_turn":
                        continue

                    tool_results: list[dict[str, Any]] = []
                    parsed_result: T | None = None
                    for block in content:
                        if block.get("type") != "tool_use":
                            continue
                        name = block.get("name")
                        tool_input = block.get("input", {})
                        block_id = block.get("id")
                        if block_id is None:
                            raise fail(
                                ProviderResponseError(
                                    "Anthropic tool_use block is missing its id; "
                                    "a valid tool_result relationship is impossible."
                                )
                            )
                        if not isinstance(tool_input, dict):
                            tool_results.append(
                                _error_result(block_id, f"Tool input for {name} must be an object.")
                            )
                            continue
                        if name == FINAL_TOOL_NAME:
                            try:
                                parsed_result = response_model.model_validate(tool_input)
                            except ValidationError as exc:
                                tool_results.append(
                                    _error_result(
                                        block_id,
                                        f"Invalid {response_model.__name__}: {exc}. "
                                        f"Correct the fields and call {FINAL_TOOL_NAME} again.",
                                    )
                                )
                            continue
                        if name not in known_tool_names:
                            tool_results.append(
                                _error_result(block_id, f"Unknown tool: {name}.")
                            )
                            continue
                        if tool_executor is None:
                            tool_results.append(
                                _error_result(block_id, f"No executor available for tool {name}.")
                            )
                            continue
                        try:
                            result = await tool_executor(name, tool_input)
                        except asyncio.CancelledError:
                            raise
                        except Exception as exc:  # tool crashes become model-visible errors
                            result = None
                            tool_results.append(
                                _error_result(
                                    block_id, f"Tool {name} failed: {self._sanitize(str(exc))}"
                                )
                            )
                        if result is not None:
                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block_id,
                                    "content": json.dumps(result, default=str),
                                }
                            )

                    if parsed_result is not None:
                        if totals.estimated_cost_usd <= 0:
                            raise fail(
                                ZeroCostUsageError(
                                    "Live Anthropic call succeeded but recorded zero cost; "
                                    "refusing to trust the ledger."
                                )
                            )
                        return parsed_result, totals

                    if tool_results:
                        messages.append({"role": "user", "content": tool_results})
                        continue

                    if last_stop_reason == "max_tokens":
                        messages.append(
                            {
                                "role": "user",
                                "content": (
                                    "Your previous response was truncated by the token limit. "
                                    f"Call {FINAL_TOOL_NAME} now with a concise result."
                                ),
                            }
                        )
                        continue

                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "You have not returned the required structured result. "
                                f"Call {FINAL_TOOL_NAME} now."
                            ),
                        }
                    )

            raise fail(
                MaxTurnsExceededError(
                    f"Anthropic did not return a valid {response_model.__name__} "
                    f"within {max_turns} turns."
                )
            )
        except asyncio.CancelledError:
            self._persist_failure(
                totals,
                correlation_id=correlation_id,
                http_status=None,
                request_turn=turn,
                stop_reason=last_stop_reason,
                retry_decision="cancelled",
                exception_category="cancelled",
                message="Task was cancelled during a provider exchange.",
            )
            raise

    def _enforce_budget(
        self,
        model: str,
        body: dict[str, Any],
        accumulated_cost: float,
        cost_budget_usd: float,
        fail: Callable[..., ProviderError],
    ) -> None:
        estimated_input_tokens = len(json.dumps(body, default=str)) // 4
        exposure = self._worst_case_call_cost(model, estimated_input_tokens)
        if accumulated_cost + exposure > cost_budget_usd:
            raise fail(
                TaskBudgetExceededError(
                    f"Refusing call: accumulated cost ${accumulated_cost:.4f} plus worst-case "
                    f"next-call exposure ${exposure:.4f} exceeds budget ${cost_budget_usd:.4f}."
                ),
                retry_decision="refused_before_call",
            )

    async def _post_with_retries(
        self,
        client: httpx.AsyncClient,
        body: dict[str, Any],
        totals: ModelUsage,
        fail: Callable[..., ProviderError],
    ) -> dict[str, Any]:
        attempt = 0
        while True:
            try:
                response = await client.post("/v1/messages", json=body)
            except httpx.TimeoutException as exc:
                if not self._retry_permitted(attempt, totals):
                    raise fail(
                        ProviderTimeoutError(
                            f"Anthropic request timed out after {attempt + 1} attempts: "
                            f"{self._sanitize(str(exc))}",
                            retryable=True,
                        ),
                        retry_decision="retries_exhausted",
                    ) from exc
                attempt = await self._backoff(attempt, totals)
                continue
            except httpx.TransportError as exc:
                if not self._retry_permitted(attempt, totals):
                    raise fail(
                        ProviderTimeoutError(
                            f"Anthropic connection failed after {attempt + 1} attempts: "
                            f"{self._sanitize(str(exc))}",
                            retryable=True,
                        ),
                        retry_decision="retries_exhausted",
                    ) from exc
                attempt = await self._backoff(attempt, totals)
                continue

            status = response.status_code
            if status in RETRYABLE_STATUS:
                if not self._retry_permitted(attempt, totals):
                    raise fail(
                        ProviderHTTPError(
                            f"Anthropic returned HTTP {status} after {attempt + 1} attempts.",
                            status_code=status,
                            retryable=True,
                            attempts=attempt + 1,
                        ),
                        http_status=status,
                        retry_decision="retries_exhausted",
                    )
                attempt = await self._backoff(attempt, totals)
                continue
            if status >= 400:
                raise fail(
                    ProviderHTTPError(
                        f"Anthropic returned non-retryable HTTP {status}: "
                        f"{self._sanitize(response.text)}",
                        status_code=status,
                        retryable=False,
                    ),
                    http_status=status,
                    retry_decision="not_retryable",
                )

            try:
                data = response.json()
            except (json.JSONDecodeError, ValueError) as exc:
                if not self._retry_permitted(attempt, totals):
                    raise fail(
                        ProviderResponseError(
                            "Anthropic returned an undecodable response body "
                            f"after {attempt + 1} attempts.",
                            retryable=True,
                        ),
                        http_status=status,
                        retry_decision="retries_exhausted",
                    ) from exc
                attempt = await self._backoff(attempt, totals)
                continue
            if not isinstance(data, dict):
                raise fail(
                    ProviderResponseError("Anthropic response JSON is not an object."),
                    http_status=status,
                    retry_decision="not_retryable",
                )
            return data

    def _retry_permitted(self, attempt: int, totals: ModelUsage) -> bool:
        return attempt < self.settings.provider_max_retries

    async def _backoff(self, attempt: int, totals: ModelUsage) -> int:
        delay = min(
            self.settings.provider_backoff_base_seconds * (2**attempt),
            self.settings.provider_backoff_max_seconds,
        )
        delay *= 0.5 + self._rng()  # jitter in [0.5, 1.5)
        totals.retries += 1
        await self._sleep(delay)
        return attempt + 1

    def _persist_failure(
        self,
        totals: ModelUsage,
        *,
        correlation_id: str | None,
        http_status: int | None,
        request_turn: int | None,
        stop_reason: str | None,
        retry_decision: str | None,
        exception_category: str,
        message: str,
    ) -> None:
        if self.store is None:
            return
        record = ProviderFailureRecord(
            correlation_id=correlation_id,
            provider="anthropic",
            model=totals.model,
            http_status=http_status,
            request_turn=request_turn,
            stop_reason=stop_reason,
            input_tokens=totals.input_tokens,
            output_tokens=totals.output_tokens,
            cache_creation_input_tokens=totals.cache_creation_input_tokens,
            cache_read_input_tokens=totals.cache_read_input_tokens,
            estimated_cost_usd=totals.estimated_cost_usd,
            retry_decision=retry_decision,
            exception_category=exception_category,
            sanitized_message=self._sanitize(message),
        )
        self.store.record_provider_failure(record)
        if totals.calls > 0:
            self.store.record_usage(totals)


def _error_result(tool_use_id: str, message: str) -> dict[str, Any]:
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": message,
        "is_error": True,
    }
