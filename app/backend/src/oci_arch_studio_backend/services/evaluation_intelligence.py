from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any


SUPPORTED_OCI_SERVICE_TERMS: tuple[str, ...] = (
    "api gateway",
    "architecture center",
    "audit",
    "autonomous database",
    "bastion",
    "base database",
    "block volume",
    "cdn",
    "cloud guard",
    "compute",
    "container registry",
    "cost analysis",
    "cost management",
    "data integration",
    "data safe",
    "database migration",
    "database services",
    "devops",
    "dns",
    "events",
    "fastconnect",
    "file storage",
    "full stack disaster recovery",
    "functions",
    "goldengate",
    "identity and access management",
    "identity",
    "iam",
    "kubernetes engine",
    "load balancer",
    "logging",
    "monitoring",
    "mysql heatwave",
    "network security groups",
    "notifications",
    "object storage",
    "oci kubernetes engine",
    "oke",
    "security zones",
    "service",
    "service connector hub",
    "services",
    "streaming",
    "vault",
    "virtual cloud network",
    "vcn",
    "web application firewall",
    "waf",
    "well-architected",
)

NONEXISTENT_OCI_PATTERNS: dict[str, str] = {
    r"\bOCI\s+AutoPilot\s+Architect\b": "non_existent_oci_service",
    r"\bOCI\s+Quantum\s+Database\b": "non_existent_oci_service",
    r"\bOCI\s+Magic\s+Migration\b": "non_existent_oci_service",
    r"\bOCI\s+Infinite\s+DR\b": "non_existent_oci_service",
}

UNSUPPORTED_FEATURE_PATTERNS: dict[str, str] = {
    r"\bguaranteed\s+(zero downtime|no downtime|recovery|availability)\b": "unsupported_availability_claim",
    r"\bno risk\b": "unsupported_risk_claim",
    r"\bself[- ]?healing\s+all\s+failures\b": "unsupported_self_healing_claim",
    r"\balways\s+(use|choose|deploy)\b": "overbroad_architecture_claim",
}

STALE_OR_RELEASE_PATTERNS: dict[str, str] = {
    r"\bi know the latest\b": "stale_release_claim",
    r"\bas of today\b": "stale_release_claim",
    r"\boracle\s+(just|recently)\s+(announced|released|changed)\b": "unverified_release_claim",
}

CONTRADICTION_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("active-active", "cheapest possible", "active-active design conflicts with cheapest-possible objective unless justified by RTO/RPO."),
    ("multi-region", "no replication", "multi-region resilience conflicts with no-replication guidance."),
    ("serverless", "persistent local state", "serverless guidance conflicts with persistent local-state requirements."),
    ("zero downtime", "no backup", "zero-downtime or strong DR claims conflict with no-backup guidance."),
)

GENERIC_FILLER_PATTERNS: tuple[str, ...] = (
    "leverage cloud-native best practices",
    "robust and scalable",
    "seamless integration",
    "future-proof",
    "enterprise-grade solution",
    "highly scalable and secure",
)

DIMENSIONS: tuple[str, ...] = (
    "oci_specificity",
    "architecture_completeness",
    "workload_alignment",
    "migration_realism",
    "ha_dr_quality",
    "cost_optimization_quality",
    "operational_realism",
    "security_realism",
    "observability_realism",
    "recommendation_explainability",
    "tradeoff_quality",
    "architecture_consistency",
)


@dataclass(frozen=True)
class DimensionScore:
    name: str
    score: float
    rationale: str


@dataclass(frozen=True)
class HallucinationFinding:
    category: str
    severity: str
    message: str
    impacted_section: str
    confidence_penalty: float
    pattern: str | None = None


@dataclass(frozen=True)
class BenchmarkResult:
    name: str
    passed: bool
    matched: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()
    score: float = 0.0


@dataclass(frozen=True)
class ArchitectureQualityScore:
    dimensions: tuple[DimensionScore, ...]
    overall: float
    hallucination_findings: tuple[HallucinationFinding, ...] = ()
    benchmarks: tuple[BenchmarkResult, ...] = ()
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "dimensions": {item.name: {"score": item.score, "rationale": item.rationale} for item in self.dimensions},
            "overall": self.overall,
            "hallucination_findings": [finding.__dict__ for finding in self.hallucination_findings],
            "benchmarks": [benchmark.__dict__ for benchmark in self.benchmarks],
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class QualityGateThresholds:
    min_overall: float = 0.72
    min_oci_specificity: float = 0.65
    min_architecture_completeness: float = 0.65
    min_tradeoff_quality: float = 0.55
    max_high_hallucinations: int = 0
    max_medium_hallucinations: int = 2


@dataclass(frozen=True)
class QualityGateResult:
    passed: bool
    failures: tuple[str, ...] = ()


class HallucinationDetector:
    def detect(self, response: dict[str, Any], case: dict[str, Any] | None = None) -> tuple[HallucinationFinding, ...]:
        text = response_text(response)
        findings: list[HallucinationFinding] = []
        findings.extend(self._regex_findings(text, NONEXISTENT_OCI_PATTERNS, "high", 0.3))
        findings.extend(self._regex_findings(text, UNSUPPORTED_FEATURE_PATTERNS, "medium", 0.18))
        findings.extend(self._regex_findings(text, STALE_OR_RELEASE_PATTERNS, "medium", 0.15))
        findings.extend(self._unsupported_oci_phrase_findings(text))
        findings.extend(self._contradictions(text, case or {}))
        findings.extend(self._unsupported_migration_claims(response, case or {}))
        return tuple(findings)

    def _regex_findings(
        self,
        text: str,
        patterns: dict[str, str],
        severity: str,
        penalty: float,
    ) -> list[HallucinationFinding]:
        findings = []
        for pattern, category in patterns.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                findings.append(
                    HallucinationFinding(
                        category=category,
                        severity=severity,
                        message=f"Matched risky phrase pattern: {pattern}",
                        impacted_section=self._section_for_text(text, pattern),
                        confidence_penalty=penalty,
                        pattern=pattern,
                    )
                )
        return findings

    def _unsupported_oci_phrase_findings(self, text: str) -> list[HallucinationFinding]:
        phrases = sorted(set(re.findall(r"\bOCI[ \t]+[A-Z][A-Za-z0-9-]*(?:[ \t]+[A-Z][A-Za-z0-9-]*){0,3}", text)))
        findings = []
        for phrase in phrases:
            normalized = normalize(phrase)
            if any(term in normalized for term in SUPPORTED_OCI_SERVICE_TERMS):
                continue
            if normalized in {"oci architecture studio", "oci genai", "oci ha", "oci dr"}:
                continue
            findings.append(
                HallucinationFinding(
                    category="unsupported_oci_service_or_feature",
                    severity="medium",
                    message=f"Review possible unsupported OCI phrase: {phrase}",
                    impacted_section=self._section_for_text(text, re.escape(phrase)),
                    confidence_penalty=0.12,
                    pattern=phrase,
                )
            )
        return findings

    def _contradictions(self, text: str, case: dict[str, Any]) -> list[HallucinationFinding]:
        normalized = normalize(text)
        prompt = normalize(str(case.get("prompt", "")))
        expected_traits = " ".join(str(item) for item in case.get("required_traits", []))
        conflict_expected = any(
            term in f"{prompt} {normalize(expected_traits)}"
            for term in ("conflicting", "contradictory", "impossible", "zero downtime", "no backups", "no monitoring")
        )
        conflict_acknowledged = any(
            term in normalized
            for term in ("conflicting requirements", "contradictory requirements", "unrealistic", "not acceptable", "risks")
        )
        if conflict_expected and conflict_acknowledged:
            return []
        findings = []
        for left, right, message in CONTRADICTION_PATTERNS:
            if left in normalized and right in normalized:
                findings.append(
                    HallucinationFinding(
                        category="contradictory_recommendation",
                        severity="medium",
                        message=message,
                        impacted_section="Risks & Assumptions",
                        confidence_penalty=0.16,
                    )
                )
        return findings

    def _unsupported_migration_claims(
        self,
        response: dict[str, Any],
        case: dict[str, Any],
    ) -> list[HallucinationFinding]:
        prompt = str(case.get("prompt", ""))
        if not re.search(r"\b(migrate|migration|eks|rds|s3|aws|cloudwatch|lambda|glue|sagemaker)\b", prompt, flags=re.IGNORECASE):
            return []
        links = response.get("evidence_links", [])
        if any(link.get("support_level") in {"strong", "partial"} for link in links):
            return []
        return [
            HallucinationFinding(
                category="unsupported_migration_claim",
                severity="medium",
                message="Migration prompt has no supported recommendation evidence links.",
                impacted_section="Migration Strategy",
                confidence_penalty=0.18,
            )
        ]

    def _section_for_text(self, text: str, pattern: str) -> str:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            return "unknown"
        prefix = text[: match.start()]
        section_matches = re.findall(
            r"\b(Executive Summary|Recommended OCI Services|Reference Architecture|HA/DR Design|Security Considerations|Cost Optimization|Risks & Assumptions|Migration Strategy|Observability|Recommended Next Steps)\b",
            prefix,
        )
        return section_matches[-1] if section_matches else "unknown"


class ArchitectureQualityScorer:
    def score(self, response: dict[str, Any], case: dict[str, Any] | None = None) -> ArchitectureQualityScore:
        case = case or {}
        text = response_text(response)
        detector = HallucinationDetector()
        hallucinations = detector.detect(response, case)
        dimensions = tuple(
            DimensionScore(name, *self._dimension_score(name, response, text, case))
            for name in DIMENSIONS
        )
        benchmarks = self._benchmarks(response, text, case)
        penalty = sum(finding.confidence_penalty for finding in hallucinations)
        overall = round(max((sum(item.score for item in dimensions) / len(dimensions)) - penalty, 0.0), 3)
        notes = []
        if penalty:
            notes.append(f"Applied hallucination/consistency penalty of {round(penalty, 3)}.")
        if any(benchmark.missing for benchmark in benchmarks):
            notes.append("One or more benchmark expectation groups are partially missing.")
        return ArchitectureQualityScore(
            dimensions=dimensions,
            overall=overall,
            hallucination_findings=hallucinations,
            benchmarks=benchmarks,
            notes=tuple(notes),
        )

    def _dimension_score(
        self,
        name: str,
        response: dict[str, Any],
        text: str,
        case: dict[str, Any],
    ) -> tuple[float, str]:
        normalized = normalize(text)
        citations = response.get("citations", [])
        evidence_links = response.get("evidence_links", [])
        reasoning = response.get("decision_reasoning", [])
        tradeoffs = response.get("architecture_tradeoffs", [])
        recommendations = response.get("recommendations", [])
        expected_services = case.get("expected_oci_services") or case.get("required_services") or []
        expected_tradeoffs = case.get("expected_tradeoffs") or []
        expected_risks = case.get("expected_risks") or []
        expected_migration = case.get("expected_migration_phases") or []
        expected_observability = case.get("expected_observability_guidance") or []
        expected_security = case.get("expected_security_guidance") or []

        if name == "oci_specificity":
            service_hits = count_matches(normalized, [*SUPPORTED_OCI_SERVICE_TERMS, *expected_services])
            return clamp(service_hits / 8), f"Matched {service_hits} OCI service or capability terms."
        if name == "architecture_completeness":
            sections = count_matches(normalized, [section.lower() for section in STANDARD_SECTIONS])
            return clamp(sections / len(STANDARD_SECTIONS)), f"Matched {sections} of {len(STANDARD_SECTIONS)} standard sections."
        if name == "workload_alignment":
            expected = workload_terms(case)
            hits = count_matches(normalized, expected)
            if not expected:
                return (0.75, "No workload-specific expectations supplied; using neutral score.")
            return clamp(hits / len(expected)), f"Matched {hits} of {len(expected)} workload expectation terms."
        if name == "migration_realism":
            expected = expected_migration or migration_terms_from_prompt(str(case.get("prompt", "")))
            if not expected:
                return (1.0, "No migration expectation for this case.")
            hits = count_matches(normalized, expected)
            mapping_score = confidence_value(response, "migration_mapping")
            return clamp((hits / len(expected) * 0.65) + (mapping_score * 0.35)), f"Matched {hits} migration terms; mapping confidence {mapping_score}."
        if name == "ha_dr_quality":
            expected = case.get("expected_dr_guidance") or ["rto", "rpo", "backup", "failover", "replication", "runbook"]
            hits = count_matches(normalized, expected)
            required = 3 if case.get("expected_intent") == "dr" or "dr" in normalize(str(case.get("prompt", ""))) else 5
            return clamp(hits / required), f"Matched {hits} HA/DR quality terms."
        if name == "cost_optimization_quality":
            expected = case.get("expected_cost_guidance") or ["cost", "budget", "rightsizing", "autoscaling", "lifecycle", "utilization"]
            hits = count_matches(normalized, expected)
            return clamp(hits / 4), f"Matched {hits} cost quality terms."
        if name == "operational_realism":
            expected = ["runbook", "validation", "testing", "monitoring", "alarm", "rollback", "owner", "incident"]
            hits = count_matches(normalized, expected)
            return clamp(hits / 5), f"Matched {hits} operational realism terms."
        if name == "security_realism":
            expected = expected_security or ["iam", "vault", "encryption", "least privilege", "audit", "private", "nsg", "cloud guard"]
            hits = count_matches(normalized, expected)
            return clamp(hits / 4), f"Matched {hits} security realism terms."
        if name == "observability_realism":
            expected = expected_observability or ["logging", "monitoring", "metrics", "alarm", "dashboard", "audit", "slo"]
            hits = count_matches(normalized, expected)
            return clamp(hits / 4), f"Matched {hits} observability realism terms."
        if name == "recommendation_explainability":
            supported = sum(1 for link in evidence_links if link.get("support_level") in {"strong", "partial"})
            reasoned = len(reasoning)
            return clamp(((supported + reasoned) / max(len(recommendations) * 2, 1))), f"{supported} supported links and {reasoned} reasoning records."
        if name == "tradeoff_quality":
            expected_hits = count_matches(normalized, expected_tradeoffs)
            tradeoff_score = min(len(tradeoffs) / 3, 1.0)
            if expected_tradeoffs:
                tradeoff_score = (tradeoff_score * 0.5) + (expected_hits / len(expected_tradeoffs) * 0.5)
            return clamp(tradeoff_score), f"{len(tradeoffs)} tradeoff records; matched {expected_hits} expected tradeoff terms."
        if name == "architecture_consistency":
            warning_count = sum(1 for finding in response.get("consistency_findings", []) if finding.get("severity") in {"warning", "error"})
            hallucination_count = len(HallucinationDetector().detect(response, case))
            return clamp(1.0 - (warning_count * 0.12) - (hallucination_count * 0.18)), f"{warning_count} consistency warnings/errors and {hallucination_count} hallucination findings."
        return (0.0, "Unknown dimension.")

    def _benchmarks(
        self,
        response: dict[str, Any],
        text: str,
        case: dict[str, Any],
    ) -> tuple[BenchmarkResult, ...]:
        normalized = normalize(text)
        benchmarks = []
        benchmark_fields = {
            "expected_oci_services": "oci_service_expectations",
            "expected_tradeoffs": "tradeoff_expectations",
            "expected_risks": "risk_expectations",
            "expected_migration_phases": "migration_phase_expectations",
            "expected_observability_guidance": "observability_expectations",
            "expected_security_guidance": "security_expectations",
        }
        for field_name, benchmark_name in benchmark_fields.items():
            expected = tuple(str(item) for item in case.get(field_name, []))
            if not expected:
                continue
            matched = tuple(item for item in expected if contains_any(normalized, term_variants(item)))
            missing = tuple(item for item in expected if item not in matched)
            score = round(len(matched) / len(expected), 3)
            benchmarks.append(BenchmarkResult(benchmark_name, not missing, matched, missing, score))
        return tuple(benchmarks)


class ResponseQualityAnalytics:
    def summarize(self, evaluated_results: list[dict[str, Any]]) -> dict[str, Any]:
        recommendation_counter: Counter[str] = Counter()
        filler_counter: Counter[str] = Counter()
        service_counter: Counter[str] = Counter()
        pattern_counter: Counter[str] = Counter()
        workload_scores: dict[str, list[float]] = {}
        retrieval_influence_scores: list[float] = []
        citation_coverages: list[float] = []
        hallucination_counter: Counter[str] = Counter()

        for result in evaluated_results:
            response = result.get("response", {})
            quality = result.get("architecture_quality", {})
            text = normalize(response_text(response))
            for recommendation in response.get("recommendations", []):
                recommendation_counter[normalize(str(recommendation))[:160]] += 1
            for phrase in GENERIC_FILLER_PATTERNS:
                if phrase in text:
                    filler_counter[phrase] += 1
            for service in SUPPORTED_OCI_SERVICE_TERMS:
                if service in text:
                    service_counter[service] += 1
            trace = response.get("reasoning_trace") or {}
            for pattern in trace.get("pattern_hints", []):
                pattern_counter[str(pattern)] += 1
            dimensions = (quality.get("dimensions") or {}) if isinstance(quality, dict) else {}
            workload_score = dimensions.get("workload_alignment", {}).get("score") if isinstance(dimensions.get("workload_alignment"), dict) else None
            if isinstance(workload_score, int | float):
                workload = str(result.get("expected_intent") or "unknown")
                workload_scores.setdefault(workload, []).append(float(workload_score))
            confidence = response.get("confidence") or {}
            if isinstance(confidence.get("citation_coverage"), int | float):
                citation_coverages.append(float(confidence["citation_coverage"]))
            if isinstance(confidence.get("evidence"), int | float):
                retrieval_influence_scores.append(float(confidence["evidence"]))
            for finding in quality.get("hallucination_findings", []) if isinstance(quality, dict) else []:
                hallucination_counter[str(finding.get("category"))] += 1

        return {
            "recommendation_repetition": recommendation_counter.most_common(10),
            "generic_filler_frequency": filler_counter.most_common(),
            "oci_service_recommendation_frequency": service_counter.most_common(20),
            "architecture_pattern_coverage": pattern_counter.most_common(20),
            "average_citation_coverage": average(citation_coverages),
            "average_retrieval_influence": average(retrieval_influence_scores),
            "workload_specific_quality": {
                workload: average(scores) for workload, scores in sorted(workload_scores.items())
            },
            "hallucination_trends": hallucination_counter.most_common(),
        }


class QualityGateEvaluator:
    def evaluate(
        self,
        quality: ArchitectureQualityScore,
        thresholds: QualityGateThresholds | None = None,
    ) -> QualityGateResult:
        thresholds = thresholds or QualityGateThresholds()
        dimensions = {dimension.name: dimension.score for dimension in quality.dimensions}
        failures = []
        if quality.overall < thresholds.min_overall:
            failures.append(f"overall {quality.overall} below {thresholds.min_overall}")
        for name, threshold in (
            ("oci_specificity", thresholds.min_oci_specificity),
            ("architecture_completeness", thresholds.min_architecture_completeness),
            ("tradeoff_quality", thresholds.min_tradeoff_quality),
        ):
            if dimensions.get(name, 0.0) < threshold:
                failures.append(f"{name} {dimensions.get(name, 0.0)} below {threshold}")
        high = sum(1 for finding in quality.hallucination_findings if finding.severity == "high")
        medium = sum(1 for finding in quality.hallucination_findings if finding.severity == "medium")
        if high > thresholds.max_high_hallucinations:
            failures.append(f"high hallucinations {high} above {thresholds.max_high_hallucinations}")
        if medium > thresholds.max_medium_hallucinations:
            failures.append(f"medium hallucinations {medium} above {thresholds.max_medium_hallucinations}")
        return QualityGateResult(passed=not failures, failures=tuple(failures))


STANDARD_SECTIONS = (
    "Executive Summary",
    "Recommended OCI Services",
    "Reference Architecture",
    "HA/DR Design",
    "Security Considerations",
    "Cost Optimization",
    "Risks & Assumptions",
    "Migration Strategy",
    "Observability",
    "Recommended Next Steps",
)


def response_text(response: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in (
        "intent",
        "answer",
        "synthesis_provider",
    ):
        parts.append(str(response.get(key, "")))
    for key in ("recommendations", "assumptions", "risks", "next_steps", "quality_warnings", "unsupported_claims"):
        parts.extend(str(item) for item in response.get(key, []))
    for reason in response.get("decision_reasoning", []):
        parts.extend(str(reason.get(key, "")) for key in ("recommendation", "service", "why_chosen", "workload_signal"))
        parts.extend(str(item) for item in reason.get("tradeoffs", []))
        parts.extend(str(item) for item in reason.get("alternatives_rejected", []))
    trace = response.get("reasoning_trace") or {}
    if isinstance(trace, dict):
        parts.append(str(trace.get("profile", "")))
        for key in ("heuristics_triggered", "pattern_hints", "retrieval_terms", "service_priorities", "risk_emphasis"):
            parts.extend(str(item) for item in trace.get(key, []))
    for tradeoff in response.get("architecture_tradeoffs", []):
        parts.extend(str(tradeoff.get(key, "")) for key in ("dimension", "decision", "benefit", "cost_or_risk", "guidance"))
    for item in response.get("recommendation_confidence", []):
        parts.extend(str(item.get(key, "")) for key in ("recommendation", "level", "reasoning_basis"))
        parts.extend(str(value) for value in item.get("known_limitations", []))
        parts.extend(str(value) for value in item.get("assumptions", []))
    for citation in response.get("citations", []):
        parts.extend(str(citation.get(key, "")) for key in ("title", "service", "service_domain", "summary", "url"))
    for link in response.get("evidence_links", []):
        parts.extend(str(link.get(key, "")) for key in ("support_level", "rationale"))
        parts.extend(str(title) for title in link.get("source_titles", []))
    return "\n".join(parts)


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def clamp(value: float) -> float:
    return round(min(max(value, 0.0), 1.0), 3)


def average(values: list[float]) -> float:
    return round(sum(values) / len(values), 3) if values else 0.0


def contains_any(text: str, variants: list[str]) -> bool:
    return any(normalize(variant) in text for variant in variants)


def count_matches(text: str, terms: list[str] | tuple[str, ...]) -> int:
    return sum(1 for term in terms if contains_any(text, term_variants(str(term))))


def term_variants(term: str) -> list[str]:
    aliases = {
        "database": ["database", "autonomous database", "base database", "mysql heatwave"],
        "oci database": ["oci database", "database", "autonomous database", "base database"],
        "load balancing": ["load balancer", "load balancing"],
        "object storage": ["object storage", "storage"],
        "rto/rpo": ["rto", "rpo"],
        "key management": ["key management", "vault", "key"],
        "tenant isolation": ["tenant isolation", "tenant", "isolation"],
        "cost allocation": ["cost allocation", "cost tags", "tagging", "attribution"],
        "rollback": ["rollback", "backout", "return-to-primary"],
    }
    return aliases.get(normalize(term), [normalize(term)])


def workload_terms(case: dict[str, Any]) -> list[str]:
    terms = []
    for field_name in ("expected_workload_terms", "expected_traits", "required_traits"):
        terms.extend(str(item) for item in case.get(field_name, []))
    prompt = normalize(str(case.get("prompt", "")))
    for term in ("fintech", "ecommerce", "saas", "tenant", "inference", "analytics", "observability", "kubernetes", "landing zone"):
        if term in prompt:
            terms.append(term)
    return list(dict.fromkeys(terms))


def migration_terms_from_prompt(prompt: str) -> list[str]:
    terms = []
    normalized = normalize(prompt)
    if any(item in normalized for item in ("eks", "kubernetes")):
        terms.extend(["oke", "kubernetes", "migration waves", "rollback"])
    if "rds" in normalized:
        terms.extend(["database", "database migration", "validation"])
    if "s3" in normalized:
        terms.extend(["object storage", "compatibility"])
    if "cloudwatch" in normalized:
        terms.extend(["logging", "monitoring"])
    return list(dict.fromkeys(terms))


def confidence_value(response: dict[str, Any], key: str) -> float:
    confidence = response.get("confidence") or {}
    value = confidence.get(key)
    return float(value) if isinstance(value, int | float) else 0.0
