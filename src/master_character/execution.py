from __future__ import annotations

from master_character.config import Settings
from master_character.context import ContextBuilder
from master_character.domain import AgentExecutionResult, AgentSpec, ModelTier, Task
from master_character.providers.base import CognitionProvider
from master_character.store import Store
from master_character.tools import ToolRegistry


class TaskExecutor:
    def __init__(
        self,
        settings: Settings,
        provider: CognitionProvider,
        context: ContextBuilder,
        store: Store,
    ):
        self.settings = settings
        self.provider = provider
        self.context = context
        self.store = store

    async def execute(self, task: Task, agent: AgentSpec) -> AgentExecutionResult:
        if self.store.daily_cost() >= self.settings.max_daily_cost_usd:
            raise RuntimeError("Daily model cost limit reached.")

        allowed_tools = sorted(set(agent.tools) & set(task.tools or agent.tools))
        registry = ToolRegistry(self.settings.workspace, self.store, allowed_tools)
        system = (
            self.context.charter()
            + "\n\n# CHILD AGENT\n"
            + agent.model_dump_json(indent=2)
            + "\n\nReturn a truthful task result. Use tools only when needed."
        )
        prompt = (
            f"TASK:\n{task.model_dump_json(indent=2)}\n\n"
            f"{self.context.snapshot_text()}"
        )
        result, usage = await self.provider.structured(
            system=system,
            prompt=prompt,
            response_model=AgentExecutionResult,
            tier=agent.model_tier,
            tools=registry.definitions(),
            tool_executor=registry.execute,
            max_turns=min(agent.max_turns, self.settings.max_model_turns),
            cost_budget_usd=min(task.cost_budget_usd, agent.cost_budget_usd),
        )
        self.store.record_usage(usage)
        return result
