from __future__ import annotations

from dataclasses import dataclass

import yaml

from master_character.config import Settings
from master_character.context import ContextBuilder
from master_character.domain import (
    AgentSpec,
    ApprovalRequest,
    EvaluationReport,
    ModelTier,
    MutationKind,
    MutationProposal,
    MutationStatus,
    RiskLevel,
)
from master_character.providers.base import CognitionProvider
from master_character.store import Store


SENSITIVE_PERMISSIONS = {
    "production_code_promotion",
    "grant_permissions",
    "spend_money",
    "external_contact",
    "public_publish",
    "modify_charter",
    "modify_rules",
}


@dataclass(frozen=True)
class CapabilityGap:
    key: str
    maturity: float
    importance: float
    evidence: str


class EvolutionEngine:
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

    def select_gap(self) -> CapabilityGap:
        raw = yaml.safe_load(self.settings.capability_path.read_text(encoding="utf-8"))
        gaps = [
            CapabilityGap(
                key=item["key"],
                maturity=float(item["maturity"]),
                importance=float(item["importance"]),
                evidence=item["evidence"],
            )
            for item in raw["capabilities"]
        ]
        return max(gaps, key=lambda gap: gap.importance * (1.0 - gap.maturity))

    async def propose(self) -> MutationProposal:
        trainer = self.store.get_active_agent("trainer")
        if trainer is None:
            raise RuntimeError("Trainer does not exist.")
        gap = self.select_gap()
        system = (
            self.context.charter()
            + "\n\n# TRAINER\n"
            + trainer.model_dump_json(indent=2)
            + "\n\nPropose one narrow mutation. It must have a baseline, tests, cost, risk, permissions, "
            "and rollback. Do not request authority expansion."
        )
        prompt = (
            f"CAPABILITY GAP: {gap.key}\nMATURITY: {gap.maturity}\nIMPORTANCE: {gap.importance}\n"
            f"EVIDENCE: {gap.evidence}\n\n{self.context.snapshot_text()}"
        )
        mutation, usage = await self.provider.structured(
            system=system,
            prompt=prompt,
            response_model=MutationProposal,
            tier=ModelTier.REASONER,
            max_turns=6,
            cost_budget_usd=0.35,
        )
        self.store.record_usage(usage)
        self.store.save_mutation(mutation)
        self.store.append_event("mutation_proposed", mutation.model_dump(mode="json"), mutation.id)
        return mutation

    def evaluate(self, mutation: MutationProposal) -> EvaluationReport:
        passed: list[str] = []
        failed: list[str] = []
        score = 0.0

        if len(mutation.measurable_tests) >= 2:
            passed.append("measurable_tests")
            score += 25
        else:
            failed.append("measurable_tests")
        if mutation.baseline.strip():
            passed.append("baseline")
            score += 15
        else:
            failed.append("baseline")
        if mutation.rollback_plan.strip():
            passed.append("rollback")
            score += 15
        else:
            failed.append("rollback")
        if mutation.expected_cost_usd <= self.settings.max_task_cost_usd:
            passed.append("cost_boundary")
            score += 15
        else:
            failed.append("cost_boundary")
        forbidden = sorted(set(mutation.required_permissions) & {"modify_charter", "modify_rules", "grant_permissions"})
        if not forbidden:
            passed.append("authority_boundary")
            score += 20
        else:
            failed.append("authority_boundary")
        if mutation.risk_level is RiskLevel.LOW:
            passed.append("low_risk")
            score += 10

        approval = bool(set(mutation.required_permissions) & SENSITIVE_PERMISSIONS)
        approval = approval or mutation.kind in {MutationKind.CODE, MutationKind.TOOL}
        approval = approval or mutation.risk_level in {RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL}
        recommendation = "reject" if failed else ("approve_after_review" if approval else "stage")
        report = EvaluationReport(
            mutation_id=mutation.id,
            score=score,
            passed=passed,
            failed=failed,
            recommendation=recommendation,
            requires_approval=approval,
            explanation=(
                "Mutation passed structural gates." if not failed else "Mutation failed one or more structural gates."
            ),
        )
        self.store.append_event("mutation_evaluated", report.model_dump(mode="json"), mutation.id)
        return report

    def stage(self, mutation: MutationProposal, report: EvaluationReport) -> ApprovalRequest | AgentSpec | None:
        if report.failed:
            mutation.status = MutationStatus.REJECTED
            self.store.save_mutation(mutation)
            return None

        candidate_dir = self.settings.candidate_workspace / mutation.id
        candidate_dir.mkdir(parents=True, exist_ok=True)
        (candidate_dir / "proposal.json").write_text(mutation.model_dump_json(indent=2), encoding="utf-8")
        (candidate_dir / "evaluation.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
        mutation.status = MutationStatus.STAGED
        self.store.save_mutation(mutation)

        if report.requires_approval or not self.settings.auto_promote_prompt_mutations:
            approval = ApprovalRequest(
                action="promote_mutation",
                reason=f"Mutation {mutation.title} is staged and requires the Master's decision.",
                risk_level=mutation.risk_level,
                payload={"mutation_id": mutation.id, "evaluation": report.model_dump(mode="json")},
            )
            self.store.save_approval(approval)
            self.store.append_event("mutation_waiting_approval", approval.model_dump(mode="json"), mutation.id)
            return approval

        if mutation.kind is MutationKind.AGENT_PROMPT:
            return self.promote_prompt_mutation(mutation)
        return None

    def promote_prompt_mutation(self, mutation: MutationProposal) -> AgentSpec | None:
        current = self.store.get_active_agent(mutation.target)
        if current is None:
            return None
        candidate = current.model_copy(deep=True)
        candidate.id = __import__("master_character.util", fromlist=["new_id"]).new_id("agent")
        candidate.version = current.version + 1
        candidate.system_prompt = current.system_prompt + "\n\n# PROMOTED MUTATION\n" + mutation.proposed_change
        candidate.created_by = f"mutation:{mutation.id}"
        candidate.created_at = __import__("master_character.util", fromlist=["utc_now"]).utc_now()
        self.store.save_agent(candidate)
        mutation.status = MutationStatus.PROMOTED
        self.store.save_mutation(mutation)
        self.store.append_event(
            "agent_version_promoted", candidate.model_dump(mode="json"), mutation.id
        )
        return candidate
