from __future__ import annotations

from master_character.context import ContextBuilder
from master_character.domain import MasterDirective, MissionBlueprint, ModelTier
from master_character.providers.base import CognitionProvider
from master_character.store import Store


class MissionArchitect:
    def __init__(self, provider: CognitionProvider, context: ContextBuilder, store: Store):
        self.provider = provider
        self.context = context
        self.store = store

    async def plan(self, directive: MasterDirective) -> MissionBlueprint:
        system = (
            self.context.charter()
            + "\n\nYou are the Mission Architect. Return an executable typed mission blueprint. "
            "Do not create decorative agents or vague tasks."
        )
        prompt = (
            f"MASTER DIRECTIVE:\n{directive.model_dump_json(indent=2)}\n\n"
            f"{self.context.snapshot_text()}"
        )
        plan, usage = await self.provider.structured(
            system=system,
            prompt=prompt,
            response_model=MissionBlueprint,
            tier=ModelTier.REASONER,
            max_turns=6,
            cost_budget_usd=0.40,
        )
        self.store.record_usage(usage)
        return plan
