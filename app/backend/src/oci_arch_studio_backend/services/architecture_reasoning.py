from __future__ import annotations

import re

from oci_arch_studio_backend.models.architecture import ArchitectureDecisionReason, EvidenceLink, RetrievedSource
from oci_arch_studio_backend.services.architecture_heuristics import ArchitectureHeuristicClassifier
from oci_arch_studio_backend.services.architecture_patterns import ArchitecturePatternSelector
from oci_arch_studio_backend.services.intents import IntentProfile


class ArchitectureDecisionReasoner:
    """Builds concise, user-safe reasoning metadata for major recommendations."""

    def build(
        self,
        *,
        question: str,
        workload_context: str | None,
        profile: IntentProfile,
        recommendations: list[str],
        evidence_links: list[EvidenceLink],
        sources: list[RetrievedSource],
        limit: int = 6,
    ) -> list[ArchitectureDecisionReason]:
        heuristics = ArchitectureHeuristicClassifier().detect(
            " ".join(part for part in (question, workload_context) if part)
        )
        pattern = ArchitecturePatternSelector().select(
            question=question,
            workload_context=workload_context,
            profile=profile,
            sources=sources,
        )
        source_by_chunk = {source.chunk_id: source for source in sources if source.chunk_id}
        reasons: list[ArchitectureDecisionReason] = []
        for recommendation, link in zip(recommendations, evidence_links, strict=False):
            linked_sources = [
                source_by_chunk[chunk_id]
                for chunk_id in link.source_chunk_ids
                if chunk_id in source_by_chunk
            ]
            service = self._service_for_recommendation(recommendation, linked_sources, sources)
            reasons.append(
                ArchitectureDecisionReason(
                    recommendation=recommendation,
                    service=service,
                    why_chosen=self._why_chosen(service, profile, pattern.name, linked_sources),
                    workload_signal=self._workload_signal(workload_context, heuristics.domains, linked_sources),
                    tradeoffs=self._tradeoffs(recommendation, service),
                    alternatives_rejected=self._alternatives_rejected(recommendation, service),
                    source_chunk_ids=link.source_chunk_ids,
                    confidence=self._confidence(link.support_level, linked_sources),
                )
            )
            if len(reasons) >= limit:
                break
        return reasons

    def _service_for_recommendation(
        self,
        recommendation: str,
        linked_sources: list[RetrievedSource],
        sources: list[RetrievedSource],
    ) -> str | None:
        for source in linked_sources:
            if source.service and source.service.lower() in recommendation.lower():
                return source.service
        if linked_sources and linked_sources[0].service:
            return linked_sources[0].service
        for source in sources:
            if source.service and source.service.lower() in recommendation.lower():
                return source.service
        return None

    def _why_chosen(
        self,
        service: str | None,
        profile: IntentProfile,
        pattern_name: str,
        linked_sources: list[RetrievedSource],
    ) -> str:
        evidence_text = ", ".join(source.title for source in linked_sources[:2]) or "retrieved OCI evidence"
        service_text = service or "this recommendation"
        return (
            f"{service_text} aligns with the {profile.intent.value} intent and "
            f"{pattern_name} pattern, with support from {evidence_text}."
        )

    def _workload_signal(
        self,
        workload_context: str | None,
        domains: tuple[str, ...],
        linked_sources: list[RetrievedSource],
    ) -> str | None:
        signals = [
            *domains,
            *(tag for source in linked_sources for tag in source.domain_tags),
            *(workload for source in linked_sources for workload in source.workload_types),
        ]
        unique_signals = list(dict.fromkeys(signal for signal in signals if signal))
        if unique_signals:
            return ", ".join(unique_signals[:4])
        if workload_context:
            return workload_context[:160]
        return None

    def _tradeoffs(self, recommendation: str, service: str | None) -> list[str]:
        text = f"{recommendation} {service or ''}".lower()
        tradeoffs: list[str] = []
        if any(token in text for token in ("multi-region", "disaster", "failover", "dr")):
            tradeoffs.append("Improves resilience but adds replication, testing, and operational cost.")
        if any(token in text for token in ("gpu", "inference", "autoscaling", "compute", "oke", "kubernetes")):
            tradeoffs.append("Improves scaling control but requires sizing, deployment, and saturation testing.")
        if any(token in text for token in ("vault", "iam", "security", "private", "network")):
            tradeoffs.append("Reduces blast radius but requires policy, network, and operational ownership.")
        if any(token in text for token in ("object storage", "cdn", "cost", "budget", "lifecycle")):
            tradeoffs.append("Can reduce cost or origin load when access patterns and lifecycle rules are validated.")
        return tradeoffs or ["Recommendation remains provisional until workload SLOs and evidence coverage are validated."]

    def _alternatives_rejected(self, recommendation: str, service: str | None) -> list[str]:
        text = f"{recommendation} {service or ''}".lower()
        alternatives: list[str] = []
        if re.search(r"\b(oke|kubernetes|container)\b", text):
            alternatives.append("Unvalidated lift-and-shift of the existing cluster.")
        if any(token in text for token in ("database", "rds", "autonomous")):
            alternatives.append("One-for-one database replacement without engine/version compatibility checks.")
        if any(token in text for token in ("dr", "failover", "backup", "replication")):
            alternatives.append("Backup-only recovery without tested failover and return-to-primary runbooks.")
        if any(token in text for token in ("cost", "right-sized", "gpu")):
            alternatives.append("Largest-shape or always-on capacity without measured demand.")
        return alternatives

    def _confidence(self, support_level: str, linked_sources: list[RetrievedSource]) -> float:
        base = {"strong": 0.9, "partial": 0.65, "unsupported": 0.25}.get(support_level, 0.4)
        if linked_sources and all(source.source_url or source.url for source in linked_sources):
            base += 0.05
        if any(source.is_stale for source in linked_sources):
            base -= 0.15
        return round(min(max(base, 0.0), 1.0), 3)
