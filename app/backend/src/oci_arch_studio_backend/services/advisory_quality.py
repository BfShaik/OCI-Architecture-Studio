from __future__ import annotations

import re
from dataclasses import dataclass

from oci_arch_studio_backend.models.architecture import (
    ConfidenceScore,
    EvidenceLink,
    RetrievedSource,
)
from oci_arch_studio_backend.services.intents import Intent, IntentProfile
from oci_arch_studio_backend.services.releases import ReleaseSnapshotStore


STOPWORDS = {
    "about",
    "after",
    "against",
    "and",
    "architecture",
    "based",
    "before",
    "between",
    "choice",
    "choices",
    "context",
    "current",
    "design",
    "each",
    "from",
    "guidance",
    "into",
    "needs",
    "oci",
    "only",
    "operational",
    "requirements",
    "review",
    "service",
    "services",
    "should",
    "source",
    "target",
    "that",
    "the",
    "then",
    "this",
    "through",
    "until",
    "where",
    "with",
    "workload",
}

UNSUPPORTED_REQUEST_PATTERNS = {
    r"\bOCI\s+Quantum\s+Database\b": "Requested unsupported OCI database capability.",
    r"\bOCI\s+Infinite\s+DR\b": "Requested unsupported OCI disaster recovery capability.",
    r"\bOCI\s+AutoPilot\s+Architect\b": "Requested unsupported OCI architecture automation capability.",
    r"\bOCI\s+Magic\s+Migration\b": "Requested unsupported OCI migration capability.",
}


@dataclass(frozen=True)
class AdvisoryQualityAssessment:
    recommendations: list[str]
    evidence_links: list[EvidenceLink]
    confidence: ConfidenceScore
    quality_warnings: list[str]
    unsupported_claims: list[str]
    not_enough_evidence: bool
    low_confidence: bool
    citation_coverage: float
    evidence_support: float


class AdvisoryQualityAnalyzer:
    def assess(
        self,
        *,
        question: str,
        profile: IntentProfile,
        base_recommendations: list[str],
        sources: list[RetrievedSource],
        release_store: ReleaseSnapshotStore | None,
    ) -> AdvisoryQualityAssessment:
        valid_sources = self._valid_sources(sources)
        unsupported_claims = self._unsupported_requested_claims(question)
        assessed_recommendations = self._suppress_unsupported_terms(
            base_recommendations,
            unsupported_claims,
        )
        evidence_links = [
            self._link_recommendation(index, recommendation, valid_sources)
            for index, recommendation in enumerate(assessed_recommendations)
        ]
        low_context_prompt = self._is_low_context_prompt(question)
        evidence_support = self._evidence_support(evidence_links)
        citation_coverage = self._citation_coverage(valid_sources)
        freshness_confidence = self._freshness_confidence(valid_sources)
        release_confidence = self._release_confidence(question, profile, release_store)
        retrieval_confidence = self._retrieval_confidence(valid_sources)
        service_relevance = self._service_relevance(base_recommendations, valid_sources)
        workload_alignment = self._workload_alignment(question, valid_sources)
        migration_mapping = self._migration_mapping_confidence(question, valid_sources)
        recommendation_confidence = round((evidence_support * 0.7) + (citation_coverage * 0.3), 3)
        if low_context_prompt:
            recommendation_confidence = min(recommendation_confidence, 0.45)
        overall = round(
            (
                retrieval_confidence * 0.25
                + evidence_support * 0.3
                + freshness_confidence * 0.2
                + release_confidence * 0.1
                + recommendation_confidence * 0.1
                + service_relevance * 0.025
                + workload_alignment * 0.015
                + migration_mapping * 0.01
            ),
            3,
        )
        if low_context_prompt:
            overall = min(overall, 0.58)
        quality_warnings = self._quality_warnings(
            profile=profile,
            question=question,
            valid_sources=valid_sources,
            evidence_links=evidence_links,
            evidence_support=evidence_support,
            release_confidence=release_confidence,
            unsupported_claims=unsupported_claims,
        )
        not_enough_evidence = not valid_sources or evidence_support < 0.45 or low_context_prompt
        low_confidence = overall < 0.6 or not_enough_evidence
        confidence = ConfidenceScore(
            retrieval=retrieval_confidence,
            evidence=evidence_support,
            freshness=freshness_confidence,
            release_awareness=release_confidence,
            recommendation=recommendation_confidence,
            service_relevance=service_relevance,
            workload_alignment=workload_alignment,
            migration_mapping=migration_mapping,
            citation_coverage=citation_coverage,
            overall=overall,
            level=self._confidence_level(overall),
            notes=quality_warnings[:4],
        )
        return AdvisoryQualityAssessment(
            recommendations=self._ground_recommendations(assessed_recommendations, evidence_links),
            evidence_links=evidence_links,
            confidence=confidence,
            quality_warnings=quality_warnings,
            unsupported_claims=unsupported_claims,
            not_enough_evidence=not_enough_evidence,
            low_confidence=low_confidence,
            citation_coverage=citation_coverage,
            evidence_support=evidence_support,
        )

    def _valid_sources(self, sources: list[RetrievedSource]) -> list[RetrievedSource]:
        return [
            source
            for source in sources
            if source.source_type != "missing_index"
            and bool(source.chunk_id)
            and bool(source.summary)
            and bool(source.source_url or source.url)
        ]

    def _link_recommendation(
        self,
        index: int,
        recommendation: str,
        sources: list[RetrievedSource],
    ) -> EvidenceLink:
        recommendation_terms = self._terms(recommendation)
        scored: list[tuple[float, RetrievedSource]] = []
        for source in sources:
            source_text = " ".join(
                (
                    source.title,
                    source.summary,
                    source.service or "",
                    source.service_domain or "",
                    source.service_category or "",
                    source.category or "",
                    source.topic or "",
                    source.workload or "",
                    " ".join(source.workload_types),
                    source.domain or "",
                    " ".join(source.domain_tags),
                    " ".join(source.intent_tags),
                    " ".join(source.architecture_patterns),
                    " ".join(source.ha_dr_tags),
                    " ".join(source.cost_optimization_tags),
                )
            )
            source_terms = self._terms(source_text)
            overlap = len(recommendation_terms & source_terms)
            service_bonus = 2 if source.service and source.service.lower() in recommendation.lower() else 0
            domain_bonus = 1 if source.service_domain and source.service_domain.lower() in recommendation.lower() else 0
            relevance_bonus = float(source.relevance_score or 0.0) * 2
            score = overlap + service_bonus + domain_bonus + relevance_bonus
            if score > 0:
                scored.append((score, source))

        scored.sort(key=lambda item: item[0], reverse=True)
        linked_sources = [source for _, source in scored[:2]]
        if not linked_sources:
            return EvidenceLink(
                recommendation_index=index,
                support_level="unsupported",
                rationale="No retrieved citation has enough term overlap to support this recommendation.",
            )
        support_level = "strong" if len(linked_sources) >= 2 or scored[0][0] >= 4 else "partial"
        return EvidenceLink(
            recommendation_index=index,
            support_level=support_level,
            source_chunk_ids=[source.chunk_id or "" for source in linked_sources if source.chunk_id],
            source_titles=[source.title for source in linked_sources],
            rationale=(
                "Recommendation is linked to retrieved OCI evidence: "
                + "; ".join(source.title for source in linked_sources)
            ),
        )

    def _ground_recommendations(
        self,
        recommendations: list[str],
        evidence_links: list[EvidenceLink],
    ) -> list[str]:
        grounded: list[str] = []
        for recommendation, link in zip(recommendations, evidence_links, strict=True):
            if link.support_level == "unsupported":
                grounded.append(
                    f"{recommendation} Evidence gap: validate this point with an official OCI source before implementation."
                )
                continue
            title_text = "; ".join(link.source_titles[:2])
            grounded.append(f"{recommendation} Evidence: {title_text}.")
        return grounded

    def _unsupported_requested_claims(self, question: str) -> list[str]:
        claims: list[str] = []
        for pattern, message in UNSUPPORTED_REQUEST_PATTERNS.items():
            if re.search(pattern, question, flags=re.IGNORECASE):
                claims.append(message)
        return claims

    def _suppress_unsupported_terms(
        self,
        recommendations: list[str],
        unsupported_claims: list[str],
    ) -> list[str]:
        if not unsupported_claims:
            return recommendations
        sanitized: list[str] = []
        for recommendation in recommendations:
            revised = recommendation
            revised = re.sub(
                r"\bOCI\s+(Quantum\s+Database|Infinite\s+DR|AutoPilot\s+Architect|Magic\s+Migration)\b",
                "the requested unsupported OCI capability",
                revised,
                flags=re.IGNORECASE,
            )
            sanitized.append(revised)
        sanitized.append(
            "Do not use the requested unsupported service names as valid OCI design components; validate alternatives against official OCI services."
        )
        return sanitized

    def _quality_warnings(
        self,
        *,
        profile: IntentProfile,
        question: str,
        valid_sources: list[RetrievedSource],
        evidence_links: list[EvidenceLink],
        evidence_support: float,
        release_confidence: float,
        unsupported_claims: list[str],
    ) -> list[str]:
        warnings: list[str] = []
        if not valid_sources:
            warnings.append("No valid retrieved evidence is available; response should stay at requirements and next-step level.")
        if len(valid_sources) < 2:
            warnings.append("Citation coverage is thin; validate service choices before implementation.")
        if any(source.is_stale for source in valid_sources):
            warnings.append("Some retrieved evidence is stale or missing freshness metadata.")
        if any(link.support_level == "unsupported" for link in evidence_links):
            warnings.append("One or more recommendations are not directly supported by retrieved evidence.")
        if evidence_support < 0.7:
            warnings.append("Evidence support is partial; treat recommendations as provisional.")
        if self._is_low_context_prompt(question):
            warnings.append("Not enough context is available for a final architecture recommendation.")
        if unsupported_claims:
            warnings.append("The prompt includes unsupported or invented service names; do not treat them as OCI services.")
        if profile.intent == Intent.RELEASE_AWARENESS and release_confidence < 0.8:
            warnings.append("Release-aware confidence is limited until a matching release note is provided or refreshed.")
        return warnings

    def _retrieval_confidence(self, valid_sources: list[RetrievedSource]) -> float:
        if not valid_sources:
            return 0.0
        count_score = min(len(valid_sources) / 4, 1.0)
        url_score = sum(1 for source in valid_sources if source.source_url or source.url) / len(valid_sources)
        relevance_scores = [
            float(source.relevance_score)
            for source in valid_sources
            if isinstance(source.relevance_score, int | float)
        ]
        relevance_score = min((sum(relevance_scores) / len(relevance_scores)) * 3, 1.0) if relevance_scores else 0.5
        return round((count_score * 0.4) + (url_score * 0.3) + (relevance_score * 0.3), 3)

    def _evidence_support(self, evidence_links: list[EvidenceLink]) -> float:
        if not evidence_links:
            return 0.0
        support_values = {"strong": 1.0, "partial": 0.65, "unsupported": 0.0}
        return round(sum(support_values.get(link.support_level, 0.0) for link in evidence_links) / len(evidence_links), 3)

    def _citation_coverage(self, valid_sources: list[RetrievedSource]) -> float:
        if not valid_sources:
            return 0.0
        complete = [
            source
            for source in valid_sources
            if source.chunk_id and source.summary and (source.source_url or source.url)
        ]
        return round(len(complete) / len(valid_sources), 3)

    def _freshness_confidence(self, valid_sources: list[RetrievedSource]) -> float:
        if not valid_sources:
            return 0.0
        freshness_values = [
            float(source.freshness_score)
            for source in valid_sources
            if isinstance(source.freshness_score, int | float)
        ]
        if not freshness_values:
            return 0.4
        stale_penalty = sum(1 for source in valid_sources if source.is_stale) / len(valid_sources)
        return round(max((sum(freshness_values) / len(freshness_values)) - stale_penalty, 0.0), 3)

    def _release_confidence(
        self,
        question: str,
        profile: IntentProfile,
        release_store: ReleaseSnapshotStore | None,
    ) -> float:
        if profile.intent != Intent.RELEASE_AWARENESS and "latest" not in question.lower():
            return 1.0
        if release_store is None or not release_store.exists:
            return 0.2
        matches = release_store.find_matches(question)
        return 0.85 if matches else 0.55

    def _service_relevance(self, recommendations: list[str], valid_sources: list[RetrievedSource]) -> float:
        if not valid_sources:
            return 0.0
        source_services = [source.service.lower() for source in valid_sources if source.service]
        if not source_services:
            return 0.4
        recommendation_text = " ".join(recommendations).lower()
        matched = sum(1 for service in source_services if service in recommendation_text)
        return round(min(matched / max(len(source_services), 1), 1.0), 3)

    def _workload_alignment(self, question: str, valid_sources: list[RetrievedSource]) -> float:
        if not valid_sources:
            return 0.0
        question_terms = self._terms(question)
        source_tags = {
            tag.lower()
            for source in valid_sources
            for tag in [source.workload or "", source.domain or "", *source.workload_types, *source.domain_tags]
            if tag
        }
        if not source_tags:
            return 0.45
        matched = sum(1 for tag in source_tags if any(part in question_terms for part in self._terms(tag)))
        return round(min(matched / len(source_tags), 1.0), 3)

    def _migration_mapping_confidence(self, question: str, valid_sources: list[RetrievedSource]) -> float:
        requested_migration = bool(
            re.search(r"\b(eks|rds|s3|cloudfront|route\s?53|fargate|lambda|cloudwatch|glue|sagemaker|aws)\b", question, flags=re.IGNORECASE)
        )
        if not requested_migration:
            return 1.0
        mappings = {
            source_name.lower(): target.lower()
            for source in valid_sources
            for source_name, target in source.migration_mappings.items()
        }
        if mappings:
            return 0.85
        source_text = " ".join(
            " ".join((source.summary, source.service or "", source.title)).lower()
            for source in valid_sources
        )
        return 0.65 if any(token in source_text for token in ("migration", "oke", "database migration")) else 0.35

    def _confidence_level(self, score: float) -> str:
        if score >= 0.8:
            return "high"
        if score >= 0.6:
            return "medium"
        return "low"

    def _is_low_context_prompt(self, question: str) -> bool:
        terms = self._terms(question)
        has_specific_oci_service = bool(
            re.search(
                r"\b(load balancer|object storage|oke|kubernetes|rds|database|vault|logging|monitoring|dr|disaster recovery|cdn|vcn)\b",
                question,
                flags=re.IGNORECASE,
            )
        )
        return len(terms) <= 3 and not has_specific_oci_service

    def _terms(self, text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9][a-z0-9-]{2,}", text.lower())
            if token not in STOPWORDS
        }
