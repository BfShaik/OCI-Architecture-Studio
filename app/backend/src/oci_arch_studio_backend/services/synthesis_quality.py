from __future__ import annotations

import re
from dataclasses import dataclass

from oci_arch_studio_backend.models.architecture import RetrievedSource


@dataclass(frozen=True)
class SynthesisQualitySignals:
    grounding_quality: float
    oci_specificity: float
    workload_alignment: float
    migration_accuracy: float
    recommendation_diversity: float
    citation_coverage: float
    overall: float
    notes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "grounding_quality": self.grounding_quality,
            "oci_specificity": self.oci_specificity,
            "workload_alignment": self.workload_alignment,
            "migration_accuracy": self.migration_accuracy,
            "recommendation_diversity": self.recommendation_diversity,
            "citation_coverage": self.citation_coverage,
            "overall": self.overall,
            "notes": list(self.notes),
        }


class SynthesisQualityScorer:
    def score(
        self,
        *,
        answer: str,
        recommendations: list[str],
        sources: list[RetrievedSource],
        question: str,
    ) -> SynthesisQualitySignals:
        valid_sources = [source for source in sources if source.source_type != "missing_index"]
        answer_text = " ".join((answer, *recommendations))
        grounding = self._grounding_quality(answer_text, valid_sources)
        oci_specificity = self._oci_specificity(answer_text, valid_sources)
        workload_alignment = self._workload_alignment(answer_text, valid_sources, question)
        migration_accuracy = self._migration_accuracy(answer_text, valid_sources, question)
        diversity = self._recommendation_diversity(recommendations)
        citation_coverage = self._citation_coverage(valid_sources)
        overall = round(
            (
                grounding * 0.25
                + oci_specificity * 0.2
                + workload_alignment * 0.15
                + migration_accuracy * 0.15
                + diversity * 0.1
                + citation_coverage * 0.15
            ),
            3,
        )
        notes = []
        if grounding < 0.6:
            notes.append("Synthesis references limited retrieved evidence.")
        if oci_specificity < 0.6:
            notes.append("Synthesis has limited OCI-specific service language.")
        if workload_alignment < 0.6:
            notes.append("Synthesis has limited workload/domain alignment.")
        if migration_accuracy < 0.8 and self._is_migration_prompt(question):
            notes.append("Migration mapping coverage is partial.")
        return SynthesisQualitySignals(
            grounding_quality=grounding,
            oci_specificity=oci_specificity,
            workload_alignment=workload_alignment,
            migration_accuracy=migration_accuracy,
            recommendation_diversity=diversity,
            citation_coverage=citation_coverage,
            overall=overall,
            notes=tuple(notes),
        )

    def _grounding_quality(self, text: str, sources: list[RetrievedSource]) -> float:
        if not sources:
            return 0.0
        source_hits = sum(
            1
            for source in sources
            if (source.service and source.service.lower() in text.lower())
            or (source.title and source.title.lower() in text.lower())
        )
        return round(min(source_hits / min(len(sources), 6), 1.0), 3)

    def _oci_specificity(self, text: str, sources: list[RetrievedSource]) -> float:
        service_names = {source.service for source in sources if source.service}
        service_hits = sum(1 for service in service_names if service and service.lower() in text.lower())
        oci_terms = len(re.findall(r"\b(OCI|Object Storage|VCN|OKE|Vault|Load Balancer|Monitoring|Logging|Autonomous Database)\b", text))
        return round(min((service_hits + min(oci_terms, 6)) / 8, 1.0), 3)

    def _workload_alignment(self, text: str, sources: list[RetrievedSource], question: str) -> float:
        workload_terms = {
            "ecommerce",
            "checkout",
            "fintech",
            "tenant",
            "saas",
            "inference",
            "model",
            "observability",
            "analytics",
            "pipeline",
            "kubernetes",
        }
        source_terms = {
            item.lower()
            for source in sources
            for item in (*source.workload_types, *source.domain_tags)
            if item
        }
        prompt_terms = {term for term in workload_terms if term in question.lower()}
        expected = prompt_terms | source_terms
        if not expected:
            return 1.0
        hits = sum(1 for term in expected if term.lower() in text.lower())
        return round(min(hits / min(len(expected), 6), 1.0), 3)

    def _migration_accuracy(self, text: str, sources: list[RetrievedSource], question: str) -> float:
        if not self._is_migration_prompt(question):
            return 1.0
        mappings = {
            source_name.lower(): target.lower()
            for source in sources
            for source_name, target in source.migration_mappings.items()
        }
        expected_sources = [name for name in ("eks", "rds", "s3", "cloudwatch", "iam", "lambda", "ecr") if name in question.lower()]
        if not expected_sources and not mappings:
            return 0.7
        hits = 0
        for source_name in expected_sources:
            if source_name in text.lower():
                hits += 1
        for source_name, target in mappings.items():
            if source_name.lower() in text.lower() and any(part.strip() in text.lower() for part in target.split("/")):
                hits += 1
        denominator = max(len(expected_sources), 1)
        return round(min(hits / denominator, 1.0), 3)

    def _recommendation_diversity(self, recommendations: list[str]) -> float:
        domains = {
            "network": ("vcn", "subnet", "load balancer", "nsg", "dns"),
            "security": ("iam", "vault", "encryption", "waf", "least privilege"),
            "data": ("database", "backup", "replication", "object storage"),
            "operations": ("logging", "monitoring", "alarm", "runbook"),
            "cost": ("cost", "budget", "rightsize", "autoscaling"),
        }
        text = " ".join(recommendations).lower()
        hits = sum(1 for terms in domains.values() if any(term in text for term in terms))
        return round(min(hits / len(domains), 1.0), 3)

    def _citation_coverage(self, sources: list[RetrievedSource]) -> float:
        if not sources:
            return 0.0
        covered = [source for source in sources if source.chunk_id and (source.source_url or source.url)]
        return round(len(covered) / len(sources), 3)

    def _is_migration_prompt(self, question: str) -> bool:
        return any(token in question.lower() for token in ("migrate", "migration", "eks", "rds", "aws", "cloudwatch", "lambda", "ecr"))
