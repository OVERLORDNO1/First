from __future__ import annotations

from datetime import timedelta

from master_character.domain import (
    Mission,
    MissionStatus,
    RiskLevel,
    Task,
    TaskKind,
    TaskStatus,
)
from master_character.store import Store
from master_character.util import new_id, utc_now


class DriveEngine:
    def __init__(self, store: Store, research_interval_minutes: int):
        self.store = store
        self.research_interval_minutes = research_interval_minutes

    def ensure_internal_growth(self) -> list[Task]:
        # Do not keep generating self-improvement proposals while the Master already has
        # a pending decision. Growth must not become approval spam.
        if self.store.list_approvals():
            return []

        existing = [
            task
            for task in self.store.list_tasks(limit=500)
            if task.key.startswith("internal_")
            and task.status in {TaskStatus.QUEUED, TaskStatus.RUNNING, TaskStatus.WAITING_APPROVAL}
        ]
        if existing:
            return []

        recent = self.store.list_events(limit=500)
        last = next(
            (
                event
                for event in recent
                if event["event_type"] == "internal_growth_scheduled"
            ),
            None,
        )
        if last:
            from datetime import datetime
            last_at = datetime.fromisoformat(last["created_at"])
            if last_at > utc_now() - timedelta(minutes=self.research_interval_minutes):
                return []

        directive = self.store.get_active_directive()
        directive_id = directive.id if directive else "internal_drive"
        mission = Mission(
            directive_id=directive_id,
            title="Continuous research and evolution",
            objective="Research the strongest current capability gap and propose one measured improvement.",
            rationale="Master Character should continue becoming more useful when external work is idle.",
            success_criteria=["One research artifact", "One evaluated mutation"],
            stop_conditions=["Daily cost limit reached", "No valid capability gap"],
            status=MissionStatus.RUNNING,
        )
        self.store.save_mission(mission)
        correlation_id = new_id("growth")
        researcher = self.store.get_active_agent("researcher")
        trainer = self.store.get_active_agent("trainer")
        evaluator = self.store.get_active_agent("evaluator")
        if not researcher or not trainer or not evaluator:
            return []

        research = Task(
            correlation_id=correlation_id,
            mission_id=mission.id,
            key=f"internal_research_{mission.id}",
            title="Research the strongest capability gap",
            objective="Inspect current state and produce evidence for one useful improvement.",
            kind=TaskKind.RESEARCH,
            assigned_agent_id=researcher.id,
            expected_output="Capability-gap research artifact.",
            tools=researcher.tools,
            cost_budget_usd=0.15,
        )
        evolve = Task(
            correlation_id=correlation_id,
            mission_id=mission.id,
            key=f"internal_evolve_{mission.id}",
            title="Propose and evaluate a mutation",
            objective="Use Trainer to propose a narrow improvement and stage it for policy review.",
            kind=TaskKind.EVOLVE,
            assigned_agent_id=trainer.id,
            expected_output="Mutation proposal, evaluation, and promotion or approval state.",
            dependency_ids=[research.id],
            tools=trainer.tools,
            cost_budget_usd=0.35,
            risk_level=RiskLevel.LOW,
        )
        self.store.save_task(research, priority=10)
        self.store.save_task(evolve, priority=10)
        self.store.append_event(
            "internal_growth_scheduled",
            {"mission_id": mission.id, "task_ids": [research.id, evolve.id]},
            correlation_id,
        )
        return [research, evolve]
