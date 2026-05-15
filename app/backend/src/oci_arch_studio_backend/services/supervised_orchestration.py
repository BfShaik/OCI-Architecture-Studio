from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from time import perf_counter

from oci_arch_studio_backend.models.architecture import (
    AgentContribution,
    AgentTrace,
    RetrievedSource,
)
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

SPECIALIST_FOCUS: dict[str, str] = {
    "architecture_advisor": "OCI service placement, tier boundaries, assumptions, risks, and grounded design guidance",
    "migration_advisor": "source-to-target mapping, migration waves, dependencies, validation, cutover, and rollback",
    "ha_dr_advisor": "RTO/RPO, cross-region resilience, failover, database protection, audit, and runbooks",
    "cost_advisor": "rightsizing, autoscaling, storage choices, budgets, tagging, and cost-performance tradeoffs",
    "release_awareness_advisor": "freshness boundaries, release evidence, stale-guidance risk, and current-vs-snapshot caution",
}

AGENT_SERVICE_HINTS: dict[str, tuple[str, ...]] = {
    "architecture_advisor": ("architecture", "networking", "compute", "database", "storage", "edge", "security"),
    "migration_advisor": ("containers", "database", "networking"),
    "ha_dr_advisor": ("resilience", "database", "networking", "security", "storage"),
    "cost_advisor": ("cost", "compute", "storage", "database"),
    "release_awareness_advisor": ("architecture", "networking", "compute", "database", "storage", "resilience"),
}


@dataclass(frozen=True)
class OrchestrationPlan:
    mode: str
    active_agents: list[str]
    routing_decision: str
    context_note: str
    traces: list[AgentTrace] = field(default_factory=list)
    contributions: list[AgentContribution] = field(default_factory=list)
    aggregation_decision: str | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CritiqueResult:
    findings: list[str]
    traces: list[AgentTrace] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class SupervisedAgentOrchestrator:
    """Small in-process supervisor for deterministic specialist advisory routing."""

    def __init__(self, mode: str = "multi_agent_pilot") -> None:
        normalized = mode.strip().lower() if mode else "multi_agent_pilot"
        allowed_modes = {"multi_agent_pilot", "supervised", "single_pass"}
        self.mode = normalized if normalized in allowed_modes else "multi_agent_pilot"

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

        if self.mode == "supervised":
            return self._single_specialist_plan(
                question=question,
                profile=profile,
                sources=sources,
                context_note=context_note,
            )

        return self._multi_agent_plan(
            question=question,
            profile=profile,
            sources=sources,
            context_note=context_note,
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

        if self.mode == "multi_agent_pilot":
            findings.append("Critic verified the controlled multi-agent pilot kept one shared evidence set and one final synthesis step.")

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

    def _single_specialist_plan(
        self,
        *,
        question: str,
        profile: IntentProfile,
        sources: list[RetrievedSource],
        context_note: str,
    ) -> OrchestrationPlan:
        started_at = perf_counter()
        specialist = AGENT_BY_INTENT.get(profile.intent, "architecture_advisor")
        valid_sources = self._valid_sources(sources)
        contribution = self._build_contribution(specialist, question, valid_sources)
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
            active_agents=["supervisor", specialist, "validation_critic"],
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
            contributions=[contribution],
            aggregation_decision="Single specialist contribution forwarded to the configured synthesis provider.",
        )

    def _multi_agent_plan(
        self,
        *,
        question: str,
        profile: IntentProfile,
        sources: list[RetrievedSource],
        context_note: str,
    ) -> OrchestrationPlan:
        started_at = perf_counter()
        valid_sources = self._valid_sources(sources)
        specialists = self._select_specialists(question, profile, valid_sources)
        contributions = self._run_specialists(specialists, question, valid_sources)
        active_agents = ["supervisor", *specialists, "validation_critic", "final_synthesizer"]
        routing_note = (
            f"Supervisor selected {', '.join(specialists)} for intent '{profile.intent.value}' "
            "using deterministic routing, one shared evidence set, and one final synthesis step."
        )
        aggregation_decision = (
            f"Aggregated {len(contributions)} specialist contribution(s); final answer remains single-writer through "
            "the configured synthesis provider and centralized citation/confidence checks."
        )
        contribution_summary = " ".join(
            f"{item.agent}: {item.summary}" for item in contributions
        )
        route_context = (
            f"{context_note} Controlled multi-agent pilot active. {routing_note} "
            f"{aggregation_decision} Specialist signals: {contribution_summary}"
        )
        latency_ms = round((perf_counter() - started_at) * 1000, 2)
        traces = [
            AgentTrace(
                agent="supervisor",
                role="routing",
                status="completed",
                latency_ms=latency_ms,
                evidence_count=len(valid_sources),
                notes=[
                    routing_note,
                    "All specialists received the same retrieved evidence and cannot mutate citations, confidence, or final response fields.",
                ],
            )
        ]
        traces.extend(
            AgentTrace(
                agent=contribution.agent,
                role="specialist_advisor",
                status="completed",
                latency_ms=0.0,
                evidence_count=contribution.evidence_count,
                notes=[contribution.summary, *contribution.recommendations[:2]],
                warnings=contribution.warnings,
            )
            for contribution in contributions
        )
        traces.append(
            AgentTrace(
                agent="final_synthesizer",
                role="aggregation",
                status="completed",
                latency_ms=0.0,
                evidence_count=len(valid_sources),
                notes=[aggregation_decision],
            )
        )
        return OrchestrationPlan(
            mode="multi_agent_pilot",
            active_agents=active_agents,
            routing_decision=routing_note,
            context_note=route_context,
            traces=traces,
            contributions=contributions,
            aggregation_decision=aggregation_decision,
        )

    def _select_specialists(
        self,
        question: str,
        profile: IntentProfile,
        sources: list[RetrievedSource],
    ) -> list[str]:
        selected: list[str] = [AGENT_BY_INTENT.get(profile.intent, "architecture_advisor")]
        normalized = question.lower()
        source_domains = {source.service_domain for source in sources if source.service_domain}

        if any(token in normalized for token in ("migrate", "migration", "eks", "rds", "aws")):
            selected.append("migration_advisor")
        if any(token in normalized for token in ("dr", "disaster recovery", "failover", "rto", "rpo", "resilience", "fintech")) or "resilience" in source_domains:
            selected.append("ha_dr_advisor")
        if any(token in normalized for token in ("cost", "budget", "right-size", "cheap", "optimize")) or "cost" in source_domains:
            selected.append("cost_advisor")
        if any(token in normalized for token in ("latest", "release", "update", "current", "changed")):
            selected.append("release_awareness_advisor")
        if profile.intent in {Intent.COST, Intent.DR, Intent.MIGRATION, Intent.RELEASE_AWARENESS}:
            selected.append("architecture_advisor")

        deduped: list[str] = []
        for agent in selected:
            if agent not in deduped:
                deduped.append(agent)
        return deduped[:3]

    def _run_specialists(
        self,
        specialists: list[str],
        question: str,
        sources: list[RetrievedSource],
    ) -> list[AgentContribution]:
        if len(specialists) == 1:
            return [self._build_contribution(specialists[0], question, sources)]
        with ThreadPoolExecutor(max_workers=min(len(specialists), 3)) as executor:
            return list(executor.map(lambda agent: self._build_contribution(agent, question, sources), specialists))

    def _build_contribution(
        self,
        agent: str,
        question: str,
        sources: list[RetrievedSource],
    ) -> AgentContribution:
        matched_sources = self._sources_for_agent(agent, sources)
        warnings: list[str] = []
        if not matched_sources:
            warnings.append("No agent-specific evidence matched; contribution remains advisory and should defer to shared retrieval evidence.")
            matched_sources = sources[:2]
        source_titles = [source.title for source in matched_sources[:3]]
        summary = (
            f"Reviewed {len(matched_sources)} evidence chunk(s) for {SPECIALIST_FOCUS[agent]}. "
            f"Key evidence: {', '.join(source_titles) if source_titles else 'none'}."
        )
        return AgentContribution(
            agent=agent,
            focus=SPECIALIST_FOCUS[agent],
            evidence_count=len(matched_sources),
            summary=summary,
            recommendations=self._agent_recommendations(agent),
            warnings=warnings,
        )

    def _sources_for_agent(self, agent: str, sources: list[RetrievedSource]) -> list[RetrievedSource]:
        hints = set(AGENT_SERVICE_HINTS.get(agent, ()))
        matched = [source for source in sources if source.service_domain in hints]
        return matched or sources[:2]

    def _valid_sources(self, sources: list[RetrievedSource]) -> list[RetrievedSource]:
        return [source for source in sources if source.source_type != "missing_index"]

    def _agent_recommendations(self, agent: str) -> list[str]:
        if agent == "migration_advisor":
            return ["Validate source-to-target service mappings and cutover dependencies before migration waves."]
        if agent == "ha_dr_advisor":
            return ["Tie resilience recommendations to RTO/RPO, failover evidence, and operational runbooks."]
        if agent == "cost_advisor":
            return ["Preserve cost controls without weakening required resilience, security, or monitoring controls."]
        if agent == "release_awareness_advisor":
            return ["Do not claim latest release impact without matching release evidence or a refreshed snapshot."]
        return ["Keep service placement and architecture recommendations grounded in retrieved OCI evidence."]

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
