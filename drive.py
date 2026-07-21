from __future__ import annotations

from master_character.context import ContextBuilder
from master_character.domain import AgentRequirement, AgentSpec, ModelTier
from master_character.providers.base import CognitionProvider
from master_character.store import Store


class AgentFactory:
    def __init__(self, provider: CognitionProvider, context: ContextBuilder, store: Store):
        self.provider = provider
        self.context = context
        self.store = store

    async def ensure(self, requirement: AgentRequirement, created_by: str) -> AgentSpec:
        current = self.store.get_active_agent(requirement.key)
        if current:
            return current

        system = (
            self.context.charter()
            + "\n\nYou are the Agent Factory. Compile one narrow, testable, permission-bounded child "
            "agent. The requirement is authoritative. Do not expand its powers."
        )
        prompt = "REQUIREMENT:\n" + requirement.model_dump_json()
        agent, usage = await self.provider.structured(
            system=system,
            prompt=prompt,
            response_model=AgentSpec,
            tier=ModelTier.REASONER,
            max_turns=5,
            cost_budget_usd=0.25,
        )
        self.store.record_usage(usage)
        agent.key = requirement.key
        agent.name = requirement.name
        agent.role = requirement.role
        agent.purpose = requirement.purpose
        agent.model_tier = requirement.model_tier
        agent.tools = requirement.tools
        agent.permissions = requirement.permissions
        agent.success_metrics = requirement.success_metrics
        agent.stop_conditions = requirement.stop_conditions
        agent.created_by = created_by
        agent.cost_budget_usd = min(agent.cost_budget_usd, 0.50)
        self.store.save_agent(agent)
        self.store.append_event(
            "child_agent_created", agent.model_dump(mode="json"), correlation_id=created_by
        )
        return agent
