from __future__ import annotations

import asyncio
from datetime import timedelta

from master_character.agents import AgentFactory
from master_character.birth import seed_lineage
from master_character.config import Settings
from master_character.context import ContextBuilder
from master_character.domain import (
    ApprovalRequest,
    ApprovalStatus,
    CharacterIdentity,
    MasterDirective,
    Mission,
    MissionStatus,
    MutationStatus,
    SystemSnapshot,
    Task,
    TaskStatus,
    TaskKind,
)
from master_character.drive import DriveEngine
from master_character.evolution import EvolutionEngine
from master_character.execution import TaskExecutor
from master_character.planning import MissionArchitect
from master_character.providers.factory import create_provider
from master_character.store import Store
from master_character.util import new_id, utc_now


class MasterCharacter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.settings.ensure_directories()
        self.store = Store(settings.db_path)
        self.provider = create_provider(settings, self.store)
        self.context = ContextBuilder(settings, self.store)
        self.architect = MissionArchitect(self.provider, self.context, self.store)
        self.factory = AgentFactory(self.provider, self.context, self.store)
        self.executor = TaskExecutor(settings, self.provider, self.context, self.store)
        self.evolution = EvolutionEngine(settings, self.provider, self.context, self.store)
        self.drive = DriveEngine(self.store, settings.research_interval_minutes)

    async def birth(self) -> CharacterIdentity:
        self.store.initialize()
        identity = self.store.get_identity()
        if identity is None:
            identity = CharacterIdentity()
            self.store.save_identity(identity)
            self.store.append_event("master_character_born", identity.model_dump(mode="json"))

        created: list[str] = []
        for seed in seed_lineage():
            if self.store.get_active_agent(seed.key) is None:
                self.store.save_agent(seed)
                self.store.append_event(
                    "birth_child_created", seed.model_dump(mode="json"), "birth_sequence"
                )
                created.append(seed.key)

        identity.state = "awaiting_master_command"
        identity.last_boot_at = utc_now()
        identity.heartbeat_count += 1
        self.store.save_identity(identity)
        self.drive.ensure_internal_growth()
        self.store.append_event(
            "master_character_booted",
            {"created_children": created, "message": "Master, what do you want me to accomplish?"},
        )
        return identity

    async def command(
        self,
        statement: str,
        success_criteria: list[str] | None = None,
        constraints: list[str] | None = None,
        priority: int = 100,
    ) -> tuple[MasterDirective, Mission, list[Task]]:
        identity = await self.birth()
        directive = MasterDirective(
            statement=statement,
            success_criteria=success_criteria or [],
            constraints=constraints or [],
            priority=priority,
        )
        self.store.save_directive(directive)
        identity.active_directive_id = directive.id
        identity.state = "planning"
        self.store.save_identity(identity)
        self.store.add_memory(
            "master_directive",
            statement,
            {"success_criteria": success_criteria or [], "constraints": constraints or []},
        )
        self.store.append_event("master_command_received", directive.model_dump(mode="json"), directive.id)

        blueprint = await self.architect.plan(directive)
        agents = {agent.key: agent for agent in self.store.list_agents()}
        for requirement in blueprint.agents:
            agents[requirement.key] = await self.factory.ensure(
                requirement, created_by=f"directive:{directive.id}"
            )

        mission = Mission(
            directive_id=directive.id,
            title=blueprint.title,
            objective=blueprint.objective,
            rationale=blueprint.rationale,
            success_criteria=directive.success_criteria or blueprint.success_criteria,
            stop_conditions=blueprint.stop_conditions + directive.constraints,
            status=MissionStatus.RUNNING,
        )
        self.store.save_mission(mission)
        correlation_id = new_id("missionrun")

        task_by_key: dict[str, Task] = {}
        for item in blueprint.tasks:
            agent = agents.get(item.assigned_agent_key)
            if agent is None:
                requirement = next(
                    (req for req in blueprint.agents if req.key == item.assigned_agent_key),
                    None,
                )
                if requirement is None:
                    raise RuntimeError(f"Planner assigned unknown agent: {item.assigned_agent_key}")
                agent = await self.factory.ensure(requirement, created_by=f"directive:{directive.id}")
            task_by_key[item.key] = Task(
                correlation_id=correlation_id,
                mission_id=mission.id,
                key=item.key,
                title=item.title,
                objective=item.objective,
                kind=item.kind,
                assigned_agent_id=agent.id,
                expected_output=item.expected_output,
                tools=item.tools or agent.tools,
                requires_approval=item.requires_approval,
                risk_level=item.risk_level,
                cost_budget_usd=min(item.cost_budget_usd, self.settings.max_task_cost_usd),
                max_attempts=item.max_attempts,
            )

        for item in blueprint.tasks:
            task = task_by_key[item.key]
            task.dependency_ids = [task_by_key[key].id for key in item.depends_on_keys]
            self.store.save_task(task, priority=directive.priority)

        identity.state = "executing"
        self.store.save_identity(identity)
        self.store.append_event(
            "mission_created",
            {
                "mission": mission.model_dump(mode="json"),
                "task_ids": [task.id for task in task_by_key.values()],
                "agent_keys": sorted(agents),
            },
            correlation_id,
        )
        return directive, mission, list(task_by_key.values())

    async def step(self, max_tasks: int | None = None, worker_id: str | None = None) -> list[Task]:
        await self.birth()
        self.drive.ensure_internal_growth()
        worker = worker_id or new_id("worker")
        leased = self.store.lease_ready_tasks(
            worker, max_tasks or self.settings.max_tasks_per_step
        )
        processed: list[Task] = []

        for task in leased:
            if task.requires_approval:
                approval = ApprovalRequest(
                    action="execute_task",
                    reason=f"Task {task.title} requires approval before execution.",
                    risk_level=task.risk_level,
                    payload={"task_id": task.id, "mission_id": task.mission_id},
                )
                self.store.save_approval(approval)
                task.status = TaskStatus.WAITING_APPROVAL
                task.lease_owner = None
                task.lease_until = None
                self.store.save_task(task)
                self.store.append_event(
                    "task_waiting_approval", approval.model_dump(mode="json"), task.correlation_id
                )
                processed.append(task)
                continue

            agent = self.store.get_agent(task.assigned_agent_id)
            if agent is None:
                task.status = TaskStatus.FAILED
                task.error = "Assigned agent not found."
                self.store.save_task(task)
                processed.append(task)
                continue

            self.store.append_event(
                "task_started",
                {"task_id": task.id, "agent_key": agent.key, "attempt": task.attempts},
                task.correlation_id,
            )
            try:
                if task.kind is TaskKind.EVOLVE:
                    mutation = await self.evolution.propose()
                    report = self.evolution.evaluate(mutation)
                    staged = self.evolution.stage(mutation, report)
                    task.result = {
                        "mutation": mutation.model_dump(mode="json"),
                        "evaluation": report.model_dump(mode="json"),
                        "staged": staged.model_dump(mode="json") if staged else None,
                    }
                else:
                    result = await self.executor.execute(task, agent)
                    task.result = result.model_dump(mode="json")
                    for child_request in result.requested_child_agents:
                        await self.factory.ensure(
                            child_request.requirement, created_by=f"task:{task.id}"
                        )
                    self.store.add_memory(
                        "task_result",
                        result.summary,
                        {"task_id": task.id, "mission_id": task.mission_id, "artifacts": result.artifacts},
                    )
                task.status = TaskStatus.COMPLETED
                task.lease_owner = None
                task.lease_until = None
                self.store.save_task(task)
                self.store.append_event(
                    "task_completed", {"task_id": task.id, "result": task.result}, task.correlation_id
                )
            except Exception as exc:
                task.error = str(exc)
                task.lease_owner = None
                task.lease_until = None
                if task.attempts >= task.max_attempts:
                    task.status = TaskStatus.FAILED
                else:
                    task.status = TaskStatus.QUEUED
                self.store.save_task(task)
                self.store.append_event(
                    "task_failed",
                    {"task_id": task.id, "error": str(exc), "status": task.status.value},
                    task.correlation_id,
                )
            finally:
                self.store.update_mission_from_tasks(task.mission_id)
                processed.append(task)

        return processed

    async def run_until_idle(self, max_steps: int = 100) -> list[Task]:
        all_processed: list[Task] = []
        for _ in range(max_steps):
            processed = await self.step()
            all_processed.extend(processed)
            ready_or_running = [
                task
                for task in self.store.list_tasks(limit=1000)
                if task.status in {TaskStatus.QUEUED, TaskStatus.RUNNING}
            ]
            if not processed and not ready_or_running:
                break
            if not processed and ready_or_running:
                # Remaining queued tasks are dependency-blocked or waiting for another lease.
                break
        return all_processed

    async def run_forever(self) -> None:
        await self.birth()
        while True:
            await self.step()
            await asyncio.sleep(max(1, self.settings.tick_seconds))

    def resolve_approval(self, approval_id: str, approve: bool, note: str = "") -> ApprovalRequest:
        approval = self.store.get_approval(approval_id)
        if approval is None:
            raise KeyError(approval_id)
        approval.status = ApprovalStatus.APPROVED if approve else ApprovalStatus.REJECTED
        approval.resolved_at = utc_now()
        approval.resolution_note = note
        self.store.save_approval(approval)

        task_id = approval.payload.get("task_id")
        if task_id:
            task = self.store.get_task(task_id)
            if task:
                if approve:
                    task.requires_approval = False
                    task.status = TaskStatus.QUEUED
                else:
                    task.status = TaskStatus.CANCELLED
                    task.error = "Rejected by Master."
                self.store.save_task(task)

        mutation_id = approval.payload.get("mutation_id")
        if mutation_id:
            # Mutation payload remains in the candidate workspace. A later command can promote it.
            self.store.append_event(
                "mutation_approval_resolved",
                {"mutation_id": mutation_id, "approved": approve, "note": note},
                mutation_id,
            )

        self.store.append_event(
            "approval_resolved", approval.model_dump(mode="json"), approval.id
        )
        return approval

    def snapshot(self) -> SystemSnapshot:
        self.store.initialize()
        identity = self.store.get_identity() or CharacterIdentity()
        return SystemSnapshot(
            identity=identity,
            active_directive=self.store.get_active_directive(),
            missions=self.store.list_missions(limit=30),
            tasks=self.store.list_tasks(limit=100),
            agents=self.store.list_agents(),
            approvals=self.store.list_approvals(),
            daily_cost_usd=self.store.daily_cost(),
            recent_events=self.store.list_events(limit=50),
        )
