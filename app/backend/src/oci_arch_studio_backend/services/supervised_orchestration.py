from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

from oci_arch_studio_backend.models.architecture import AgentTrace, RetrievedSource
from oci_arch_studio_backend.services.advisory_quality import AdvisoryQualityAssessment
from oci_arch_studio_backend.services.intents import Intent, IntentProfile
from oci_arch_studio_backend.services.synthesis import SynthesisResult


AGENT_BY_INTENT: dict[Intent, str] = {
    Intent.PRODUCT_OVERVIEW: "architecture_advisor",
    Intent.ARCHITECTURE: "architecture_advisor",
    Intent.MIGRATION: "migration_advisor",
    Intent.DR: "ha_dr_advisor",
    Intent.COST: "cost_advisor",
    Intent.SECURITY: "architecture_advisor",
    Intent.RELEASE_AWARENESS: "release_awareness_advisor",
    Intent.GENERAL: "architecture_advisor",
}


@dataclass(frozen=True)
class OrchestrationPlan:
    mode: str
    active_agents: list[str]
    routing_decision: str
    context_note: str
    traces: list[AgentTrace] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CritiqueResult:
    findings: list[str]
    traces: list[AgentTrace] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class SupervisedAgentOrchestrator:
    """Small in-process supervisor for deterministic specialist advisory routing."""

    def __init__(self, mode: str = "supervised") -> None:
        normalized = mode.strip().lower() if mode else "supervised"
        self.mode = normalized if normalized in {"supervised", "single_pass"} else "supervised"

    def plan(
        self,
        *,
        question: str,
        profile: IntentProfile,
        sources: list[RetrievedSource],
        context_note: str,
    ) -> OrchestrationPlan:
        if self.mode == "single_pass":
            return OrchestrationPlan(
                mode="single_pass",
                active_agents=[],
                routing_decision="Single-pass orchestration selected by configuration.",
                context_note=context_note,
            )

        started_at = perf_counter()
        specialist = AGENT_BY_INTENT.get(profile.intent, "architecture_advisor")
        active_agents = ["supervisor", specialist, "validation_critic"]
        valid_sources = [source for source in sources if source.source_type != "missing_index"]
        notes = [
            f"Routed intent '{profile.intent.value}' to {specialist}.",
            f"Shared {len(valid_sources)} retrieved evidence chunk(s) with the specialist.",
        ]
        if profile.intent == Intent.RELEASE_AWARENESS:
            notes.append("Release-awareness advisor must separate snapshot-backed guidance from current-release uncertainty.")

        route_context = (
            f"{context_note} Supervised routing selected {specialist} for intent "
            f"{profile.intent.value}; validation_critic will review evidence support, citations, "
            "freshness, and unsupported-claim risk before the response is returned."
        )
        latency_ms = round((perf_counter() - started_at) * 1000, 2)
        return OrchestrationPlan(
            mode="supervised",
            active_agents=active_agents,
            routing_decision=(
                f"Supervisor routed intent '{profile.intent.value}' to {specialist} "
                "with shared retrieval evidence and a mandatory critic review."
            ),
            context_note=route_context,
            traces=[
                AgentTrace(
                    agent="supervisor",
                    role="routing",
                    status="completed",
                    latency_ms=latency_ms,
                    evidence_count=len(valid_sources),
                    notes=notes,
                ),
                AgentTrace(
                    agent=specialist,
                    role="specialist_advisor",
                    status="completed",
                    latency_ms=0.0,
                    evidence_count=len(valid_sources),
                    notes=[self._specialist_note(profile.intent)],
                ),
            ],
        )

    def critique(
        self,
        *,
        synthesis: SynthesisResult,
        quality: AdvisoryQualityAssessment,
        sources: list[RetrievedSource],
    ) -> CritiqueResult:
        if self.mode == "single_pass":
            return CritiqueResult(findings=[])

        started_at = perf_counter()
        findings: list[str] = []
        warnings: list[str] = []
        valid_sources = [source for source in sources if source.source_type != "missing_index"]

        if quality.not_enough_evidence:
            findings.append("Critic marked the advisory as provisional because retrieved evidence is insufficient.")
        else:
            findings.append("Critic confirmed enough retrieved evidence for a bounded advisory response.")

        if quality.unsupported_claims:
            findings.append("Critic flagged unsupported requested capabilities and kept them out of valid OCI recommendations.")
            warnings.append("Unsupported requested capabilities were present in the prompt.")

        if quality.citation_coverage >= 0.8:
            findings.append("Critic confirmed citation coverage is acceptable for the current evidence set.")
        else:
            findings.append("Critic found thin citation coverage; validate service choices before implementation.")
            warnings.append("Citation coverage is below the preferred threshold.")

        if quality.evidence_support < 0.7:
            findings.append("Critic found partial retrieval-to-recommendation alignment.")
            warnings.append("Evidence support is partial.")
        else:
            findings.append("Critic confirmed recommendations are linked to retrieved evidence.")

        if any(source.is_stale for source in valid_sources):
            findings.append("Critic detected stale or low-freshness evidence in the retrieved context.")
            warnings.append("Some retrieved evidence may be stale.")

        if synthesis.used_fallback:
            findings.append("Critic noted synthesis fallback was used and response remained deterministic.")
            warnings.append("Synthesis fallback was used.")

        latency_ms = round((perf_counter() - started_at) * 1000, 2)
        return CritiqueResult(
            findings=findings,
            traces=[
                AgentTrace(
                    agent="validation_critic",
                    role="critic",
                    status="completed",
                    latency_ms=latency_ms,
                    evidence_count=len(valid_sources),
                    notes=findings[:4],
                    warnings=warnings,
                )
            ],
            warnings=warnings,
        )

    def _specialist_note(self, intent: Intent) -> str:
        if intent == Intent.MIGRATION:
            return "Migration advisor focused on source-to-target service mapping, phases, dependencies, and cutover risk."
        if intent == Intent.DR:
            return "HA/DR advisor focused on RTO/RPO, cross-region resilience, failover, security, and runbooks."
        if intent == Intent.COST:
            return "Cost advisor focused on rightsizing, autoscaling, storage choices, budgets, and tradeoffs."
        if intent == Intent.RELEASE_AWARENESS:
            return "Release-awareness advisor focused on freshness boundaries, release evidence, and stale-guidance risk."
        return "Architecture advisor focused on OCI service placement, assumptions, risks, and grounded design guidance."
