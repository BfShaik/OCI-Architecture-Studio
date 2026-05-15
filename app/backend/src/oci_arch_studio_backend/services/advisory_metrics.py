from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AdvisoryQualityMetrics:
    request_count: int = 0
    low_confidence_count: int = 0
    not_enough_evidence_count: int = 0
    unsupported_claim_count: int = 0
    stale_evidence_count: int = 0
    total_citation_coverage: float = 0.0
    total_evidence_support: float = 0.0
    last_intent: str | None = None
    last_confidence_level: str | None = None
    last_overall_confidence: float | None = None
    last_synthesis_provider: str | None = None
    synthesis_fallback_count: int = 0
    last_orchestration_mode: str | None = None
    last_active_agents: list[str] = field(default_factory=list)
    last_routing_decision: str | None = None
    orchestration_failure_count: int = 0
    critic_warning_count: int = 0
    last_citation_coverage: float | None = None
    last_evidence_support: float | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def average_citation_coverage(self) -> float:
        if self.request_count == 0:
            return 0.0
        return round(self.total_citation_coverage / self.request_count, 3)

    @property
    def average_evidence_support(self) -> float:
        if self.request_count == 0:
            return 0.0
        return round(self.total_evidence_support / self.request_count, 3)

    def as_dict(self) -> dict[str, object]:
        return {
            "request_count": self.request_count,
            "low_confidence_count": self.low_confidence_count,
            "not_enough_evidence_count": self.not_enough_evidence_count,
            "unsupported_claim_count": self.unsupported_claim_count,
            "stale_evidence_count": self.stale_evidence_count,
            "average_citation_coverage": self.average_citation_coverage,
            "average_evidence_support": self.average_evidence_support,
            "last_intent": self.last_intent,
            "last_confidence_level": self.last_confidence_level,
            "last_overall_confidence": self.last_overall_confidence,
            "last_synthesis_provider": self.last_synthesis_provider,
            "synthesis_fallback_count": self.synthesis_fallback_count,
            "last_orchestration_mode": self.last_orchestration_mode,
            "last_active_agents": list(self.last_active_agents),
            "last_routing_decision": self.last_routing_decision,
            "orchestration_failure_count": self.orchestration_failure_count,
            "critic_warning_count": self.critic_warning_count,
            "last_citation_coverage": self.last_citation_coverage,
            "last_evidence_support": self.last_evidence_support,
            "warnings": list(self.warnings[-10:]),
        }


class AdvisoryQualityMetricsRecorder:
    def __init__(self) -> None:
        self.metrics = AdvisoryQualityMetrics()

    def record(
        self,
        *,
        intent: str,
        confidence_level: str,
        overall_confidence: float,
        citation_coverage: float,
        evidence_support: float,
        low_confidence: bool,
        not_enough_evidence: bool,
        unsupported_claims: list[str],
        stale_evidence_count: int,
        synthesis_provider: str,
        synthesis_fallback_used: bool,
        orchestration_mode: str = "single_pass",
        active_agents: list[str] | None = None,
        routing_decision: str | None = None,
        critic_warnings: list[str] | None = None,
        warnings: list[str] | None = None,
    ) -> None:
        self.metrics.request_count += 1
        self.metrics.total_citation_coverage += citation_coverage
        self.metrics.total_evidence_support += evidence_support
        self.metrics.last_intent = intent
        self.metrics.last_confidence_level = confidence_level
        self.metrics.last_overall_confidence = overall_confidence
        self.metrics.last_synthesis_provider = synthesis_provider
        self.metrics.last_orchestration_mode = orchestration_mode
        self.metrics.last_active_agents = list(active_agents or [])
        self.metrics.last_routing_decision = routing_decision
        self.metrics.last_citation_coverage = citation_coverage
        self.metrics.last_evidence_support = evidence_support
        if low_confidence:
            self.metrics.low_confidence_count += 1
        if not_enough_evidence:
            self.metrics.not_enough_evidence_count += 1
        if unsupported_claims:
            self.metrics.unsupported_claim_count += 1
        if stale_evidence_count:
            self.metrics.stale_evidence_count += 1
        if synthesis_fallback_used:
            self.metrics.synthesis_fallback_count += 1
        if critic_warnings:
            self.metrics.critic_warning_count += 1
        self.metrics.warnings.extend(warnings or [])

    def snapshot(self) -> dict[str, object]:
        return self.metrics.as_dict()


advisory_quality_metrics = AdvisoryQualityMetricsRecorder()
