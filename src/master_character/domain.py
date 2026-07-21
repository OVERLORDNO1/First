from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from master_character.util import new_id, utc_now


class ModelTier(StrEnum):
    REASONER = "reasoner"
    WORKER = "worker"
    CRITIC = "critic"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DirectiveStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"


class MissionStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskKind(StrEnum):
    RESEARCH = "research"
    ANALYSE = "analyse"
    BUILD = "build"
    OPERATE = "operate"
    EVALUATE = "evaluate"
    EVOLVE = "evolve"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MutationKind(StrEnum):
    AGENT_PROMPT = "agent_prompt"
    WORKFLOW = "workflow"
    MEMORY = "memory"
    ROUTING = "routing"
    TOOL = "tool"
    CODE = "code"


class MutationStatus(StrEnum):
    PROPOSED = "proposed"
    STAGED = "staged"
    APPROVED = "approved"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


class CharacterIdentity(BaseModel):
    id: str = "master_character"
    name: str = "Master Character"
    version: str = "2.0.0"
    state: str = "new"
    master_name: str = "Ryan"
    active_directive_id: str | None = None
    born_at: datetime = Field(default_factory=utc_now)
    last_boot_at: datetime | None = None
    heartbeat_count: int = 0


class MasterDirective(BaseModel):
    id: str = Field(default_factory=lambda: new_id("directive"))
    statement: str
    success_criteria: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    priority: int = Field(default=100, ge=0, le=100)
    status: DirectiveStatus = DirectiveStatus.ACTIVE
    created_at: datetime = Field(default_factory=utc_now)


class PermissionSet(BaseModel):
    allowed: list[str] = Field(default_factory=list)
    denied: list[str] = Field(default_factory=list)
    approval_required: list[str] = Field(default_factory=list)


class AgentRequirement(BaseModel):
    key: str
    name: str
    role: str
    purpose: str
    model_tier: ModelTier = ModelTier.WORKER
    tools: list[str] = Field(default_factory=list)
    permissions: PermissionSet = Field(default_factory=PermissionSet)
    success_metrics: list[str] = Field(default_factory=list)
    stop_conditions: list[str] = Field(default_factory=list)


class AgentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("agent"))
    key: str
    version: int = 1
    name: str
    role: str
    purpose: str
    model_tier: ModelTier
    system_prompt: str
    tools: list[str] = Field(default_factory=list)
    permissions: PermissionSet = Field(default_factory=PermissionSet)
    max_turns: int = Field(default=6, ge=1, le=30)
    cost_budget_usd: float = Field(default=0.25, ge=0)
    success_metrics: list[str] = Field(default_factory=list)
    stop_conditions: list[str] = Field(default_factory=list)
    created_by: str
    active: bool = True
    created_at: datetime = Field(default_factory=utc_now)


class TaskBlueprint(BaseModel):
    key: str
    title: str
    objective: str
    kind: TaskKind
    assigned_agent_key: str
    expected_output: str
    depends_on_keys: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    requires_approval: bool = False
    risk_level: RiskLevel = RiskLevel.LOW
    cost_budget_usd: float = Field(default=0.25, ge=0)
    max_attempts: int = Field(default=2, ge=1, le=10)


class MissionBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    objective: str
    rationale: str
    agents: list[AgentRequirement]
    tasks: list[TaskBlueprint]
    success_criteria: list[str]
    stop_conditions: list[str]

    @field_validator("tasks")
    @classmethod
    def unique_task_keys(cls, value: list[TaskBlueprint]) -> list[TaskBlueprint]:
        keys = [task.key for task in value]
        if len(keys) != len(set(keys)):
            raise ValueError("Task keys must be unique.")
        known = set(keys)
        for task in value:
            missing = set(task.depends_on_keys) - known
            if missing:
                raise ValueError(f"Task {task.key} depends on unknown keys: {sorted(missing)}")
        return value


class Mission(BaseModel):
    id: str = Field(default_factory=lambda: new_id("mission"))
    directive_id: str
    title: str
    objective: str
    rationale: str
    success_criteria: list[str]
    stop_conditions: list[str]
    status: MissionStatus = MissionStatus.PLANNED
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None


class Task(BaseModel):
    id: str = Field(default_factory=lambda: new_id("task"))
    correlation_id: str
    mission_id: str
    key: str
    title: str
    objective: str
    kind: TaskKind
    assigned_agent_id: str
    expected_output: str
    dependency_ids: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    requires_approval: bool = False
    risk_level: RiskLevel = RiskLevel.LOW
    cost_budget_usd: float = Field(default=0.25, ge=0)
    max_attempts: int = Field(default=2, ge=1, le=10)
    attempts: int = 0
    status: TaskStatus = TaskStatus.QUEUED
    lease_owner: str | None = None
    lease_until: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ChildAgentRequest(BaseModel):
    requirement: AgentRequirement
    reason: str


class AgentExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    completed: bool
    verified_facts: list[str] = Field(default_factory=list)
    inferences: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    requested_child_agents: list[ChildAgentRequest] = Field(default_factory=list)
    recommended_next_actions: list[str] = Field(default_factory=list)


class ResearchSource(BaseModel):
    url: str
    title: str
    retrieved_at: datetime = Field(default_factory=utc_now)
    published_at: datetime | None = None
    evidence_excerpt: str
    source_class: str = "unknown"
    confidence: float = Field(default=0.5, ge=0, le=1)


class ResearchJob(BaseModel):
    id: str = Field(default_factory=lambda: new_id("research"))
    query: str
    purpose: str
    freshness_days: int | None = None
    max_calls: int = Field(default=3, ge=1, le=100)
    cost_budget_usd: float = Field(default=0.25, ge=0)
    status: str = "queued"
    sources: list[ResearchSource] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class MutationProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("mutation"))
    kind: MutationKind
    target: str
    title: str
    capability_gap: str
    baseline: str
    proposed_change: str
    rationale: str
    measurable_tests: list[str]
    expected_benefit: str
    expected_cost_usd: float = Field(ge=0)
    risk_level: RiskLevel
    required_permissions: list[str]
    rollback_plan: str
    candidate_files: list[str] = Field(default_factory=list)
    status: MutationStatus = MutationStatus.PROPOSED
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("measurable_tests")
    @classmethod
    def minimum_tests(cls, value: list[str]) -> list[str]:
        if len(value) < 2:
            raise ValueError("At least two measurable tests are required.")
        return value


class EvaluationReport(BaseModel):
    mutation_id: str
    score: float = Field(ge=0, le=100)
    passed: list[str]
    failed: list[str]
    recommendation: str
    requires_approval: bool
    explanation: str
    created_at: datetime = Field(default_factory=utc_now)


class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: new_id("approval"))
    action: str
    reason: str
    risk_level: RiskLevel
    payload: dict[str, Any]
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = None
    resolution_note: str | None = None


class ModelUsage(BaseModel):
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    calls: int = 0
    retries: int = 0
    stop_reason: str | None = None
    estimated_cost_usd: float = 0.0
    correlation_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class ProviderFailureRecord(BaseModel):
    id: str = Field(default_factory=lambda: new_id("pfail"))
    correlation_id: str | None = None
    provider: str
    model: str
    http_status: int | None = None
    request_turn: int | None = None
    stop_reason: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    estimated_cost_usd: float = 0.0
    retry_decision: str | None = None
    exception_category: str
    sanitized_message: str
    created_at: datetime = Field(default_factory=utc_now)


class ProviderResult(BaseModel):
    value: Any
    usage: ModelUsage


class SystemSnapshot(BaseModel):
    identity: CharacterIdentity
    active_directive: MasterDirective | None
    missions: list[Mission]
    tasks: list[Task]
    agents: list[AgentSpec]
    approvals: list[ApprovalRequest]
    daily_cost_usd: float
    recent_events: list[dict[str, Any]]
