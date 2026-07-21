from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, TypeVar

from pydantic import BaseModel

from master_character.domain import ModelTier, ModelUsage

T = TypeVar("T", bound=BaseModel)
ToolExecutor = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


class CognitionProvider(ABC):
    @abstractmethod
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
        raise NotImplementedError
