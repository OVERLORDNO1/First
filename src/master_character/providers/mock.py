from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

from master_character.domain import (
    AgentExecutionResult,
    AgentRequirement,
    AgentSpec,
    ChildAgentRequest,
    MissionBlueprint,
    ModelTier,
    ModelUsage,
    MutationKind,
    MutationProposal,
    PermissionSet,
    RiskLevel,
    TaskBlueprint,
    TaskKind,
)
from master_character.providers.base import CognitionProvider, ToolExecutor

T = TypeVar("T", bound=BaseModel)


class MockProvider(CognitionProvider):
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
        if response_model is MissionBlueprint:
            value = MissionBlueprint(
                title="Execute the Master's command",
                objective="Produce a verified working result for the supplied directive.",
                rationale="Research first, build second, evaluate last.",
                agents=[
                    AgentRequirement(
                        key="mission_researcher",
                        name="Mission Researcher",
                        role="evidence researcher",
                        purpose="Find the knowledge required by this directive.",
                        model_tier=ModelTier.WORKER,
                        tools=["memory_search", "workspace_write", "system_state"],
                        permissions=PermissionSet(
                            allowed=["read_memory", "write_workspace"],
                            denied=["spend_money", "external_contact"],
                        ),
                        success_metrics=["useful findings", "clear unknowns"],
                        stop_conditions=["budget reached", "evidence sufficient"],
                    ),
                    AgentRequirement(
                        key="mission_builder",
                        name="Mission Builder",
                        role="implementation builder",
                        purpose="Create the requested working artifact.",
                        model_tier=ModelTier.REASONER,
                        tools=["memory_search", "workspace_list", "workspace_read", "workspace_write", "system_state"],
                        permissions=PermissionSet(
                            allowed=["read_memory", "read_workspace", "write_workspace"],
                            denied=["spend_money", "external_contact", "public_publish"],
                        ),
                        success_metrics=["working artifact", "reproducible output"],
                        stop_conditions=["budget reached", "blocked by approval"],
                    ),
                ],
                tasks=[
                    TaskBlueprint(
                        key="research",
                        title="Research the command",
                        objective="Identify requirements, existing memory, and the strongest implementation path.",
                        kind=TaskKind.RESEARCH,
                        assigned_agent_key="mission_researcher",
                        expected_output="Research report in workspace.",
                        tools=["memory_search", "workspace_write", "system_state"],
                        cost_budget_usd=0.10,
                    ),
                    TaskBlueprint(
                        key="build",
                        title="Build the requested result",
                        objective="Use the research to create the working result.",
                        kind=TaskKind.BUILD,
                        assigned_agent_key="mission_builder",
                        expected_output="Working artifact and execution notes.",
                        depends_on_keys=["research"],
                        tools=["memory_search", "workspace_list", "workspace_read", "workspace_write", "system_state"],
                        cost_budget_usd=0.20,
                    ),
                    TaskBlueprint(
                        key="evaluate",
                        title="Evaluate the result",
                        objective="Test the result against the Master's success criteria.",
                        kind=TaskKind.EVALUATE,
                        assigned_agent_key="evaluator",
                        expected_output="Pass, revise, or reject decision.",
                        depends_on_keys=["build"],
                        tools=["workspace_list", "workspace_read", "memory_search", "system_state"],
                        cost_budget_usd=0.10,
                    ),
                ],
                success_criteria=["A concrete artifact exists", "The result is evaluated"],
                stop_conditions=["Daily cost limit reached", "A required approval is rejected"],
            )
        elif response_model is AgentSpec:
            key = "generated_specialist"
            if "REQUIREMENT:" in prompt:
                try:
                    import json
                    data = json.loads(prompt.split("REQUIREMENT:", 1)[1].strip())
                    key = data.get("key", key)
                    name = data.get("name", key.replace("_", " ").title())
                    role = data.get("role", "specialist")
                    purpose = data.get("purpose", "Complete assigned work")
                    tier_value = data.get("model_tier", "worker")
                    tier_obj = ModelTier(tier_value)
                    tools_value = data.get("tools", [])
                    permissions_value = PermissionSet.model_validate(data.get("permissions", {}))
                    metrics = data.get("success_metrics", [])
                    stops = data.get("stop_conditions", [])
                except Exception:
                    name, role, purpose, tier_obj, tools_value, permissions_value, metrics, stops = (
                        "Generated Specialist", "specialist", "Complete assigned work", ModelTier.WORKER,
                        [], PermissionSet(), [], []
                    )
            else:
                name, role, purpose, tier_obj, tools_value, permissions_value, metrics, stops = (
                    "Generated Specialist", "specialist", "Complete assigned work", ModelTier.WORKER,
                    [], PermissionSet(), [], []
                )
            value = AgentSpec(
                key=key,
                name=name,
                role=role,
                purpose=purpose,
                model_tier=tier_obj,
                system_prompt=(
                    f"You are {name}, a child created by Master Character. Your role is {role}. "
                    f"Purpose: {purpose}. Work only within your tools, permissions, budget, and success tests."
                ),
                tools=tools_value,
                permissions=permissions_value,
                success_metrics=metrics,
                stop_conditions=stops,
                created_by="mock_agent_factory",
            )
        elif response_model is AgentExecutionResult:
            artifact = "artifacts/mock_result.md"
            if tool_executor and tools and any(tool.get("name") == "workspace_write" for tool in tools):
                await tool_executor(
                    "workspace_write",
                    {
                        "path": artifact,
                        "content": "# Mock mission result\n\nThe task completed through the bounded mock cognition provider.\n",
                    },
                )
            value = AgentExecutionResult(
                summary="Task completed in deterministic mock mode.",
                completed=True,
                verified_facts=["The execution path completed without a live model call."],
                inferences=[],
                unknowns=["Real-world quality requires a live provider and external evidence."],
                artifacts=[artifact],
                requested_child_agents=[],
                recommended_next_actions=["Run evaluation and inspect the stored events."],
            )
        elif response_model is MutationProposal:
            value = MutationProposal(
                kind=MutationKind.AGENT_PROMPT,
                target="researcher",
                title="Improve evidence discipline in the Researcher",
                capability_gap="continuous_research",
                baseline="Researcher prompt requests evidence but has no explicit contradiction check.",
                proposed_change=(
                    "Add a mandatory contradiction scan and a source-quality ranking section to the "
                    "Researcher's system prompt."
                ),
                rationale="It should reduce confident synthesis from weak or conflicting sources.",
                measurable_tests=[
                    "On a conflicting-source fixture, the candidate lists the disagreement.",
                    "On a weak-source fixture, the candidate lowers confidence below the baseline.",
                ],
                expected_benefit="Higher research reliability without new permissions.",
                expected_cost_usd=0.05,
                risk_level=RiskLevel.LOW,
                required_permissions=["create_agent_version"],
                rollback_plan="Reactivate the previous Researcher version.",
                candidate_files=["agent:researcher:system_prompt"],
            )
        else:
            raise TypeError(f"MockProvider has no response for {response_model.__name__}")

        usage = ModelUsage(provider="mock", model=f"mock-{tier.value}")
        return value, usage  # type: ignore[return-value]
