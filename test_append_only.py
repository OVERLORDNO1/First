from __future__ import annotations

import json
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from master_character.config import Settings
from master_character.domain import ModelTier, ModelUsage
from master_character.providers.base import CognitionProvider, ToolExecutor

T = TypeVar("T", bound=BaseModel)


class AnthropicProvider(CognitionProvider):
    def __init__(self, settings: Settings):
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when MASTER_PROVIDER=anthropic")
        self.settings = settings

    def _model_for(self, tier: ModelTier) -> str:
        return {
            ModelTier.REASONER: self.settings.reasoning_model,
            ModelTier.WORKER: self.settings.worker_model,
            ModelTier.CRITIC: self.settings.critic_model,
        }[tier]

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
    ) -> tuple[T, ModelUsage]:
        model = self._model_for(tier)
        final_tool_name = "emit_structured_result"
        final_tool = {
            "name": final_tool_name,
            "description": "Return the final validated structured result for this task.",
            "input_schema": response_model.model_json_schema(),
        }
        available_tools = [*(tools or []), final_tool]
        messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
        total_input = 0
        total_output = 0

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

        async with httpx.AsyncClient(
            base_url=self.settings.anthropic_base_url.rstrip("/"),
            headers=headers,
            timeout=timeout,
        ) as client:
            for turn in range(max_turns):
                body = {
                    "model": model,
                    "max_tokens": 4096,
                    "system": system_value,
                    "messages": messages,
                    "tools": available_tools,
                }
                response = await client.post("/v1/messages", json=body)
                response.raise_for_status()
                data = response.json()
                usage = data.get("usage", {})
                total_input += int(usage.get("input_tokens", 0))
                total_output += int(usage.get("output_tokens", 0))
                content = data.get("content", [])
                messages.append({"role": "assistant", "content": content})

                tool_results: list[dict[str, Any]] = []
                for block in content:
                    if block.get("type") != "tool_use":
                        continue
                    name = block.get("name")
                    tool_input = block.get("input", {})
                    if name == final_tool_name:
                        try:
                            parsed = response_model.model_validate(tool_input)
                        except ValidationError as exc:
                            raise ValueError(
                                f"Anthropic returned invalid {response_model.__name__}: {exc}"
                            ) from exc
                        return parsed, ModelUsage(
                            provider="anthropic",
                            model=model,
                            input_tokens=total_input,
                            output_tokens=total_output,
                            estimated_cost_usd=0.0,
                        )
                    if tool_executor is None:
                        result = {"ok": False, "error": f"No executor available for tool {name}"}
                    else:
                        result = await tool_executor(name, tool_input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block["id"],
                            "content": json.dumps(result, default=str),
                        }
                    )

                if tool_results:
                    messages.append({"role": "user", "content": tool_results})
                    continue

                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "You have not returned the required structured result. "
                            f"Call {final_tool_name} now."
                        ),
                    }
                )

        raise RuntimeError(
            f"Anthropic did not return {response_model.__name__} within {max_turns} turns."
        )
