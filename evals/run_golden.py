from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = REPO_ROOT / "app" / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

from fastapi.testclient import TestClient  # noqa: E402
from oci_arch_studio_backend.main import app  # noqa: E402
from oci_arch_studio_backend.services.evaluation_intelligence import (  # noqa: E402
    ArchitectureQualityScorer,
    QualityGateEvaluator,
    QualityGateThresholds,
    ResponseQualityAnalytics,
)


SUPPORTED_OCI_TERMS = {
    "autonomous database",
    "architecture center",
    "api gateway",
    "base database service",
    "budgets",
    "cdn",
    "cloud guard",
    "compute",
    "container registry",
    "cost analysis",
    "cost management overview",
    "data guard",
    "data safe",
    "database migration",
    "database services overview",
    "dns",
    "fastconnect",
    "functions",
    "full stack disaster recovery",
    "iam",
    "identity",
    "kubernetes engine",
    "load balancer",
    "logging",
    "monitoring",
    "mysql heatwave",
    "network security groups",
    "object storage",
    "oci container registry",
    "oci data safe",
    "oci functions",
    "oke",
    "oracle base database service",
    "oracle cloud infrastructure",
    "reference architecture",
    "security zones",
    "service",
    "services",
    "security services overview",
    "vault",
    "virtual cloud network",
    "vcn",
    "waf",
    "web application firewall",
    "well-architected",
}

SUSPICIOUS_PATTERNS = (
    r"\bguaranteed\s+(zero downtime|recovery|availability|success|no downtime)\b",
    r"\bzero downtime\s+(is|can be|will be)\s+guaranteed\b",
    r"\b(can|will)\s+guarantee\s+zero downtime\b",
    r"\bno risk\b",
    r"\balways\s+(choose|use|deploy|select|recommend)\b",
    r"\bnever\s+(fails|needs|requires|breaks)\b",
    r"\bdefinitely affects\b",
    r"\bi know the latest\b",
    r"\bas of today\b",
)

INVENTED_SERVICE_PATTERNS = (
    r"\bOCI AutoPilot Architect\b",
    r"\bOCI Quantum Database\b",
    r"\bOCI Magic Migration\b",
    r"\bOCI Infinite DR\b",
)

STALE_GUIDANCE_PATTERNS = (
    r"\bi know the latest\b",
    r"\bas of today\b",
    r"\bthe latest OCI update (definitely|always|will)\b",
    r"\boracle (just|recently) (announced|changed|released)\b",
)

TERM_ALIASES = {
    "cdn": ["cdn", "content delivery"],
    "data guard": ["data guard", "replication", "database replication"],
    "database": ["database", "data tier"],
    "dns": ["dns", "traffic failover"],
    "eks": ["eks", "kubernetes"],
    "load balancing": ["load balancer", "load balancing"],
    "object storage": ["object storage", "storage"],
    "api gateway": ["api gateway", "managed api front door"],
    "oci database": ["oci database", "database", "autonomous database", "base database", "mysql heatwave"],
    "oci kubernetes engine": ["oci kubernetes engine", "oke", "kubernetes engine"],
    "oke": ["oke", "kubernetes engine"],
    "rds": ["rds", "database migration"],
    "right-sized compute": ["right-sized compute", "compute", "right-sized"],
    "rto/rpo": ["rto", "rpo", "recovery"],
    "vault": ["vault", "key management", "secrets"],
    "web application firewall": ["web application firewall", "waf"],
}


@dataclass
class EvalCheck:
    name: str
    passed: bool
    score: int
    max_score: int
    details: list[str] = field(default_factory=list)


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def response_text(response: dict[str, Any]) -> str:
    parts: list[str] = [
        str(response.get("intent", "")),
        str(response.get("prompt_template", "")),
        str(response.get("answer", "")),
    ]
    for key in ("recommendations", "assumptions", "risks", "next_steps"):
        parts.append(key)
        parts.extend(str(item) for item in response.get(key, []))
    for key in ("quality_warnings", "unsupported_claims", "synthesis_warnings"):
        parts.append(key)
        parts.extend(str(item) for item in response.get(key, []))
    for reason in response.get("decision_reasoning", []):
        parts.append(str(reason.get("service", "")))
        parts.append(str(reason.get("why_chosen", "")))
        parts.append(str(reason.get("workload_signal", "")))
        parts.extend(str(item) for item in reason.get("tradeoffs", []))
        parts.extend(str(item) for item in reason.get("alternatives_rejected", []))
    for finding in response.get("consistency_findings", []):
        parts.append(str(finding.get("check", "")))
        parts.append(str(finding.get("message", "")))
        parts.append(str(finding.get("recommendation", "")))
    reasoning_trace = response.get("reasoning_trace") or {}
    if isinstance(reasoning_trace, dict):
        parts.append(str(reasoning_trace.get("profile", "")))
        for key in ("heuristics_triggered", "pattern_hints", "retrieval_terms", "service_priorities", "risk_emphasis"):
            parts.extend(str(item) for item in reasoning_trace.get(key, []))
    for tradeoff in response.get("architecture_tradeoffs", []):
        parts.append(str(tradeoff.get("dimension", "")))
        parts.append(str(tradeoff.get("decision", "")))
        parts.append(str(tradeoff.get("benefit", "")))
        parts.append(str(tradeoff.get("cost_or_risk", "")))
        parts.append(str(tradeoff.get("guidance", "")))
    for item in response.get("recommendation_confidence", []):
        parts.append(str(item.get("recommendation", "")))
        parts.append(str(item.get("reasoning_basis", "")))
        parts.append(str(item.get("level", "")))
        parts.extend(str(value) for value in item.get("known_limitations", []))
        parts.extend(str(value) for value in item.get("assumptions", []))
    governance = response.get("enterprise_governance") or {}
    if isinstance(governance, dict):
        parts.append(str(governance.get("maturity_level", "")))
        executive = governance.get("executive_summary") or {}
        if isinstance(executive, dict):
            parts.extend(str(value) for value in executive.values())
        for key in (
            "governance_annotations",
            "security_posture_checks",
            "risk_classifications",
            "recommendation_priorities",
            "architecture_comparisons",
            "enterprise_review_findings",
        ):
            for item in governance.get(key, []):
                if isinstance(item, dict):
                    parts.extend(str(value) for value in item.values())
        audit = governance.get("auditability_trace") or {}
        if isinstance(audit, dict):
            parts.extend(str(value) for value in audit.values())
    topology = response.get("architecture_topology") or {}
    if isinstance(topology, dict):
        for key in ("topology_summary", "deployment_topology", "ha_dr_topology", "mermaid_flow"):
            parts.append(str(topology.get(key, "")))
        for item in topology.get("nodes", []):
            if isinstance(item, dict):
                parts.extend(str(value) for value in item.values())
        for item in topology.get("service_dependencies", []):
            if isinstance(item, dict):
                parts.extend(str(value) for value in item.values())
        parts.extend(str(note) for note in topology.get("operational_notes", []))
    executive = response.get("executive_experience") or {}
    if isinstance(executive, dict):
        parts.append(str(executive.get("executive_summary", "")))
        for key in ("decision_brief", "implementation_sequence", "comparison_summary", "explainability_highlights"):
            for item in executive.get(key, []):
                if isinstance(item, dict):
                    parts.extend(str(value) for value in item.values())
                else:
                    parts.append(str(item))
        visualization = executive.get("architecture_visualization") or {}
        if isinstance(visualization, dict):
            parts.extend(str(value) for value in visualization.values())
        for artifact in executive.get("review_artifacts", []):
            if isinstance(artifact, dict):
                parts.append(str(artifact.get("title", "")))
                parts.append(str(artifact.get("markdown_summary", "")))
                parts.extend(str(item) for item in artifact.get("review_checkpoints", []))
    optimization = response.get("optimization_plan") or {}
    if isinstance(optimization, dict):
        parts.append(str(optimization.get("maturity_level", "")))
        parts.extend(str(item) for item in optimization.get("implementation_readiness", []))
        parts.extend(str(item) for item in optimization.get("recommendation_additions", []))
        for key in (
            "migration_phases",
            "modernization_options",
            "finops_recommendations",
            "workload_optimization_signals",
            "optimization_comparisons",
        ):
            for item in optimization.get(key, []):
                if isinstance(item, dict):
                    parts.extend(str(value) for value in item.values())
    release_context = response.get("release_context") or {}
    if isinstance(release_context, dict):
        parts.extend(str(item) for item in release_context.get("architecture_affecting_services", []))
        parts.extend(str(item) for item in release_context.get("impact_categories", []))
        parts.extend(str(item) for item in release_context.get("maturity_notes", []))
    for key in ("active_agents", "critic_findings", "orchestration_warnings"):
        parts.append(key)
        parts.extend(str(item) for item in response.get(key, []))
    parts.append(str(response.get("aggregation_decision", "")))
    for contribution in response.get("agent_contributions", []):
        parts.append(str(contribution.get("agent", "")))
        parts.append(str(contribution.get("focus", "")))
        parts.append(str(contribution.get("summary", "")))
        parts.extend(str(item) for item in contribution.get("recommendations", []))
    parts.append(str(response.get("orchestration_mode", "")))
    parts.append(str(response.get("routing_decision", "")))
    confidence = response.get("confidence") or {}
    if isinstance(confidence, dict):
        parts.append("confidence")
        parts.append(str(confidence.get("level", "")))
        parts.extend(str(note) for note in confidence.get("notes", []))
    for link in response.get("evidence_links", []):
        parts.append(str(link.get("support_level", "")))
        parts.append(str(link.get("rationale", "")))
        parts.extend(str(title) for title in link.get("source_titles", []))
    for citation in response.get("citations", []):
        parts.append(str(citation.get("title", "")))
        parts.append(str(citation.get("summary", "")))
        parts.append(str(citation.get("url", "")))
    return "\n".join(parts)


def contains_term(text: str, term: str) -> bool:
    return normalize(term) in normalize(text)


def term_variants(term: str) -> list[str]:
    normalized = normalize(term)
    return TERM_ALIASES.get(normalized, [normalized])


def contains_supported_term(text: str, term: str) -> bool:
    normalized_text = normalize(text)
    return any(variant in normalized_text for variant in term_variants(term))


def citation_evidence_text(response: dict[str, Any]) -> str:
    parts: list[str] = []
    for citation in response.get("citations", []):
        parts.append(str(citation.get("title", "")))
        parts.append(str(citation.get("summary", "")))
        parts.append(str(citation.get("url", "")))
    return "\n".join(parts)


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                cases.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
    return cases


def execute_prompt(client: TestClient, prompt: str) -> dict[str, Any]:
    response = client.post("/architecture-review", json={"question": prompt, "save_to_history": False})
    response.raise_for_status()
    return response.json()


def validate_structure(response: dict[str, Any]) -> EvalCheck:
    required_fields = {
        "intent": str,
        "prompt_template": str,
        "orchestration_mode": str,
        "active_agents": list,
        "agent_trace": list,
        "agent_contributions": list,
        "critic_findings": list,
        "orchestration_warnings": list,
        "synthesis_provider": str,
        "synthesis_warnings": list,
        "synthesis_fallback_used": bool,
        "decision_reasoning": list,
        "consistency_findings": list,
        "answer": str,
        "recommendations": list,
        "assumptions": list,
        "risks": list,
        "citations": list,
        "section_citations": list,
        "next_steps": list,
        "evidence_links": list,
        "quality_warnings": list,
        "unsupported_claims": list,
        "not_enough_evidence": bool,
        "low_confidence": bool,
    }
    missing_or_invalid = [
        field
        for field, expected_type in required_fields.items()
        if field not in response or not isinstance(response[field], expected_type)
    ]
    list_failures = [
        field
        for field in ("recommendations", "assumptions", "risks", "next_steps")
        if isinstance(response.get(field), list) and not response[field]
    ]
    passed = not missing_or_invalid and not list_failures
    details = []
    if missing_or_invalid:
        details.append(f"missing/invalid fields: {', '.join(missing_or_invalid)}")
    if list_failures:
        details.append(f"empty sections: {', '.join(list_failures)}")
    return EvalCheck("structure", passed, 15 if passed else 0, 15, details)


def validate_orchestration(case: dict[str, Any], response: dict[str, Any]) -> EvalCheck:
    expected_mode = case.get("expected_orchestration_mode")
    required_agents = list(case.get("required_agents", []))
    minimum_contributions = int(case.get("minimum_agent_contributions", 0))
    if not expected_mode and not required_agents:
        return EvalCheck("orchestration", True, 5, 5, ["orchestration not asserted"])

    details: list[str] = []
    mode = response.get("orchestration_mode")
    if expected_mode and mode != expected_mode:
        details.append(f"expected mode {expected_mode}, got {mode}")
    active_agents = response.get("active_agents", [])
    missing_agents = [agent for agent in required_agents if agent not in active_agents]
    if missing_agents:
        details.append(f"missing agents: {', '.join(missing_agents)}")
    if expected_mode == "supervised" and not response.get("critic_findings"):
        details.append("missing critic findings")
    if expected_mode == "multi_agent_pilot" and not response.get("aggregation_decision"):
        details.append("missing aggregation decision")
    contributions = response.get("agent_contributions", [])
    if minimum_contributions and len(contributions) < minimum_contributions:
        details.append(f"expected at least {minimum_contributions} agent contributions, got {len(contributions)}")
    if expected_mode in {"supervised", "multi_agent_pilot"} and not response.get("critic_findings"):
        details.append("missing critic findings")
    trace = response.get("agent_trace", [])
    if expected_mode in {"supervised", "multi_agent_pilot"} and not trace:
        details.append("missing agent trace")

    passed = not details
    return EvalCheck("orchestration", passed, 5 if passed else 0, 5, details)


def validate_intent(case: dict[str, Any], response: dict[str, Any]) -> EvalCheck:
    expected = case["expected_intent"]
    actual = response.get("intent")
    passed = actual == expected
    return EvalCheck(
        "intent",
        passed,
        20 if passed else 0,
        20,
        [] if passed else [f"expected {expected}, got {actual}"],
    )


def validate_required_terms(
    name: str,
    terms: list[str],
    text: str,
    max_score: int,
) -> EvalCheck:
    if not terms:
        return EvalCheck(name, True, max_score, max_score, ["no required terms"])
    missing = [term for term in terms if not contains_term(text, term)]
    found_count = len(terms) - len(missing)
    score = round(max_score * (found_count / len(terms)))
    return EvalCheck(
        name,
        not missing,
        score,
        max_score,
        [] if not missing else [f"missing: {', '.join(missing)}"],
    )


def validate_grounding(case: dict[str, Any], response: dict[str, Any]) -> EvalCheck:
    citations = response.get("citations", [])
    requires_grounding = case.get("grounding_required", False)

    if not requires_grounding:
        return EvalCheck("grounding", True, 15, 15, ["grounding not required"])

    details: list[str] = []
    valid_citations = [
        citation
        for citation in citations
        if citation.get("source_type") != "missing_index"
        and citation.get("chunk_id")
        and citation.get("summary")
        and citation.get("url")
    ]
    scores = [
        citation.get("relevance_score")
        for citation in valid_citations
        if isinstance(citation.get("relevance_score"), int | float)
    ]
    if not scores:
        details.append("missing relevance scores")
    elif max(scores) < 0.05:
        details.append("weak top relevance score")

    passed = not details
    return EvalCheck("grounding", passed, 15 if passed else 0, 15, details)


def validate_retrieval_support(case: dict[str, Any], response: dict[str, Any]) -> EvalCheck:
    if not case.get("grounding_required", False):
        return EvalCheck("retrieval_support", True, 10, 10, ["retrieval support not required"])

    required_services = case.get("required_services", [])
    if not required_services:
        return EvalCheck("retrieval_support", True, 10, 10, ["no required services"])

    answer = response_text(response)
    evidence = citation_evidence_text(response)
    answer_terms = [term for term in required_services if contains_supported_term(answer, term)]
    if not answer_terms:
        return EvalCheck("retrieval_support", True, 10, 10, ["no service claims to verify"])

    unsupported = [term for term in answer_terms if not contains_supported_term(evidence, term)]
    supported_count = len(answer_terms) - len(unsupported)
    score = round(10 * (supported_count / len(answer_terms)))
    passed = score >= 6
    details = [] if passed else [f"weak or missing evidence for: {', '.join(unsupported)}"]
    if unsupported and passed:
        details.append(f"partial retrieval gaps: {', '.join(unsupported)}")

    return EvalCheck("retrieval_support", passed, score, 10, details)


def validate_citations(case: dict[str, Any], response: dict[str, Any]) -> EvalCheck:
    if not case.get("citation_required", False):
        return EvalCheck("citations", True, 10, 10, ["citations not required"])

    citations = response.get("citations", [])
    valid_citations = [
        citation
        for citation in citations
        if citation.get("source_type") != "missing_index"
        and citation.get("chunk_id")
        and citation.get("summary")
        and citation.get("url")
    ]
    details: list[str] = []
    if not valid_citations:
        details.append("missing valid citations with chunk id, summary, and url")
    elif len(valid_citations) < 2:
        details.append("fewer than two valid citations")

    passed = not details
    return EvalCheck("citations", passed, 10 if passed else 0, 10, details)


def validate_evidence_links(case: dict[str, Any], response: dict[str, Any]) -> EvalCheck:
    if not case.get("grounding_required", False):
        return EvalCheck("evidence_links", True, 10, 10, ["evidence links not required"])

    recommendations = response.get("recommendations", [])
    links = response.get("evidence_links", [])
    details: list[str] = []
    if len(links) < len(recommendations):
        details.append("fewer evidence links than recommendations")
    unsupported = [
        str(link.get("recommendation_index"))
        for link in links
        if link.get("support_level") == "unsupported"
    ]
    unsupported_allowed = bool(case.get("allow_unsupported_evidence", False))
    if unsupported and not unsupported_allowed:
        details.append(f"unsupported recommendation links: {', '.join(unsupported)}")
    linked = [
        link
        for link in links
        if link.get("support_level") in {"strong", "partial"}
        and link.get("source_chunk_ids")
        and link.get("source_titles")
    ]
    if not linked:
        details.append("no recommendations linked to citation chunk ids")

    passed = not details
    score = 10 if passed else max(0, 10 - (len(details) * 4))
    return EvalCheck("evidence_links", passed, score, 10, details)


def validate_section_citations(case: dict[str, Any], response: dict[str, Any]) -> EvalCheck:
    if not case.get("citation_required", False):
        return EvalCheck("section_citations", True, 10, 10, ["section citations not required"])

    sections = response.get("section_citations", [])
    details: list[str] = []
    if len(sections) < 6:
        details.append("fewer than six section citation groups")

    linked_sections = [
        section
        for section in sections
        if section.get("sources")
        and section.get("source_count", 0) >= len(section.get("sources", []))
        and section.get("traceability_note")
    ]
    if len(linked_sections) < 4:
        details.append("fewer than four sections have traceable sources")

    source_ids = {
        citation.get("chunk_id")
        for citation in response.get("citations", [])
        if citation.get("chunk_id")
    }
    orphaned = [
        source.get("chunk_id")
        for section in linked_sections
        for source in section.get("sources", [])
        if source.get("chunk_id") and source.get("chunk_id") not in source_ids
    ]
    if orphaned:
        details.append(f"section citation chunk ids missing from citations: {', '.join(orphaned[:3])}")

    passed = not details
    score = 10 if passed else max(0, 10 - (len(details) * 4))
    return EvalCheck("section_citations", passed, score, 10, details)


def validate_confidence(case: dict[str, Any], response: dict[str, Any]) -> EvalCheck:
    confidence = response.get("confidence")
    if not isinstance(confidence, dict):
        return EvalCheck("confidence", False, 0, 10, ["missing confidence object"])

    required_keys = {
        "retrieval",
        "evidence",
        "freshness",
        "release_awareness",
        "recommendation",
        "service_relevance",
        "workload_alignment",
        "migration_mapping",
        "citation_coverage",
        "overall",
        "level",
        "notes",
    }
    missing = sorted(required_keys - set(confidence))
    details: list[str] = []
    if missing:
        details.append(f"missing confidence keys: {', '.join(missing)}")
    numeric_keys = required_keys - {"level", "notes"}
    out_of_range = [
        key
        for key in numeric_keys
        if not isinstance(confidence.get(key), int | float)
        or float(confidence.get(key)) < 0
        or float(confidence.get(key)) > 1
    ]
    if out_of_range:
        details.append(f"confidence scores out of range: {', '.join(sorted(out_of_range))}")
    minimum = float(case.get("minimum_confidence", 0.0))
    overall = float(confidence.get("overall", 0.0)) if isinstance(confidence.get("overall"), int | float) else 0.0
    if minimum and overall < minimum:
        details.append(f"overall confidence {overall} below required {minimum}")
    if case.get("expect_low_confidence") is True and not response.get("low_confidence", False):
        details.append("expected low_confidence=true")
    if case.get("expect_not_enough_evidence") is True and not response.get("not_enough_evidence", False):
        details.append("expected not_enough_evidence=true")

    passed = not details
    return EvalCheck("confidence", passed, 10 if passed else 0, 10, details)


def validate_reasoning_metadata(case: dict[str, Any], response: dict[str, Any]) -> EvalCheck:
    if not case.get("reasoning_required", False):
        return EvalCheck("reasoning_metadata", True, 5, 5, ["reasoning metadata not required"])
    reasons = response.get("decision_reasoning", [])
    details: list[str] = []
    if not reasons:
        details.append("missing decision reasoning")
    else:
        first = reasons[0]
        for field_name in ("recommendation", "why_chosen", "tradeoffs", "source_chunk_ids", "confidence"):
            if not first.get(field_name):
                details.append(f"missing {field_name}")
    passed = not details
    return EvalCheck("reasoning_metadata", passed, 5 if passed else 0, 5, details)


def validate_consistency_metadata(case: dict[str, Any], response: dict[str, Any]) -> EvalCheck:
    expected_checks = list(case.get("expected_consistency_checks", []))
    if not expected_checks:
        return EvalCheck("consistency_metadata", True, 5, 5, ["consistency checks not asserted"])
    checks = {str(finding.get("check")) for finding in response.get("consistency_findings", [])}
    missing = [check for check in expected_checks if check not in checks]
    passed = not missing
    return EvalCheck(
        "consistency_metadata",
        passed,
        5 if passed else 0,
        5,
        [] if passed else [f"missing checks: {', '.join(missing)}"],
    )


def validate_architecture_quality(case: dict[str, Any], response: dict[str, Any]) -> EvalCheck:
    quality = ArchitectureQualityScorer().score(response, case)
    thresholds = QualityGateThresholds(
        min_overall=float(case.get("minimum_architecture_quality", 0.55)),
        min_oci_specificity=float(case.get("minimum_oci_specificity", 0.45)),
        min_architecture_completeness=float(case.get("minimum_architecture_completeness", 0.45)),
        min_tradeoff_quality=float(case.get("minimum_tradeoff_quality", 0.35)),
        max_high_hallucinations=int(case.get("max_high_hallucinations", 0)),
        max_medium_hallucinations=int(case.get("max_medium_hallucinations", 3)),
    )
    gate = QualityGateEvaluator().evaluate(quality, thresholds)
    score = round(20 * quality.overall)
    details = list(gate.failures)
    if quality.hallucination_findings:
        details.extend(
            f"{finding.severity}:{finding.category}:{finding.impacted_section}"
            for finding in quality.hallucination_findings
        )
    if not details:
        details.append(f"overall architecture quality {quality.overall}")
    return EvalCheck("architecture_quality", gate.passed, score if gate.passed else max(score - 5, 0), 20, details)


def validate_forbidden_patterns(case: dict[str, Any], text: str) -> EvalCheck:
    patterns = list(case.get("forbidden_patterns", []))
    patterns.extend(SUSPICIOUS_PATTERNS)
    patterns.extend(INVENTED_SERVICE_PATTERNS)
    matches = [
        pattern
        for pattern in patterns
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]
    passed = not matches
    return EvalCheck(
        "non_hallucination",
        passed,
        10 if passed else 0,
        10,
        [] if passed else [f"forbidden/suspicious patterns: {', '.join(matches)}"],
    )


def validate_unsupported_oci_claims(text: str) -> EvalCheck:
    oci_phrases = set(re.findall(r"\bOCI\s+[A-Z][A-Za-z0-9-]*(?:\s+[A-Z][A-Za-z0-9-]*){0,3}", text))
    unsupported = [
        phrase
        for phrase in sorted(oci_phrases)
        if not any(term in normalize(phrase) for term in SUPPORTED_OCI_TERMS)
    ]
    # Product names in source URLs/titles can be noisy; keep this check advisory.
    passed = len(unsupported) <= 3
    return EvalCheck(
        "unsupported_oci_claims",
        passed,
        5 if passed else 0,
        5,
        [] if passed else [f"review possible unsupported OCI phrases: {', '.join(unsupported)}"],
    )


def validate_stale_or_unverified_guidance(case: dict[str, Any], text: str) -> EvalCheck:
    normalized_text = normalize(text)
    matches = [
        pattern
        for pattern in STALE_GUIDANCE_PATTERNS
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]
    release_case = case.get("expected_intent") == "release_awareness" or "latest" in normalize(case["prompt"])
    release_caution = any(
        phrase in normalized_text
        for phrase in (
            "release note",
            "local rag index",
            "refresh",
            "current release context",
            "latest oci release sources",
        )
    )
    if release_case and not release_caution:
        matches.append("missing release-context caution")

    passed = not matches
    return EvalCheck(
        "stale_unverified_guidance",
        passed,
        5 if passed else 0,
        5,
        [] if passed else [f"stale/unverified guidance: {', '.join(matches)}"],
    )


def evaluate_case(client: TestClient, case: dict[str, Any]) -> dict[str, Any]:
    response = execute_prompt(client, case["prompt"])
    text = response_text(response)
    architecture_quality = ArchitectureQualityScorer().score(response, case)
    checks = [
        validate_structure(response),
        validate_intent(case, response),
        validate_orchestration(case, response),
        validate_required_terms("required_services", case.get("required_services", []), text, 15),
        validate_required_terms("required_traits", case.get("required_traits", []), text, 20),
        validate_citations(case, response),
        validate_grounding(case, response),
        validate_retrieval_support(case, response),
        validate_evidence_links(case, response),
        validate_section_citations(case, response),
        validate_confidence(case, response),
        validate_reasoning_metadata(case, response),
        validate_consistency_metadata(case, response),
        validate_architecture_quality(case, response),
        validate_forbidden_patterns(case, text),
        validate_unsupported_oci_claims(text),
        validate_stale_or_unverified_guidance(case, text),
    ]
    score = sum(check.score for check in checks)
    max_score = sum(check.max_score for check in checks)
    normalized_score = round((score / max_score) * 100)
    minimum_score = int(case.get("minimum_score", 80))
    passed = normalized_score >= minimum_score and all(
        check.passed
        for check in checks
        if check.name
        in {
            "structure",
            "intent",
            "citations",
            "grounding",
            "retrieval_support",
            "evidence_links",
            "confidence",
            "orchestration",
            "non_hallucination",
            "stale_unverified_guidance",
            "architecture_quality",
        }
    )
    failure_reasons = [
        f"{check.name}: {'; '.join(check.details) if check.details else 'failed'}"
        for check in checks
        if not check.passed
    ]

    return {
        "id": case["id"],
        "prompt": case["prompt"],
        "expected_intent": case["expected_intent"],
        "actual_intent": response.get("intent"),
        "score": normalized_score,
        "minimum_score": minimum_score,
        "passed": passed,
        "failure_reasons": failure_reasons,
        "checks": [
            {
                "name": check.name,
                "passed": check.passed,
                "score": check.score,
                "max_score": check.max_score,
                "details": check.details,
            }
            for check in checks
        ],
        "architecture_quality": architecture_quality.as_dict(),
        "response": response,
        "top_citations": [
            {
                "title": citation.get("title"),
                "url": citation.get("url"),
                "score": citation.get("relevance_score"),
                "chunk_id": citation.get("chunk_id"),
            }
            for citation in response.get("citations", [])[:6]
        ],
    }


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_intent: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0})
    failure_counter: Counter[str] = Counter()
    warning_counter: Counter[str] = Counter()
    check_counter: Counter[str] = Counter()
    retrieval_gaps: list[dict[str, str]] = []
    scores = [int(result["score"]) for result in results]
    architecture_scores = [
        float(result.get("architecture_quality", {}).get("overall", 0.0))
        for result in results
        if isinstance(result.get("architecture_quality"), dict)
    ]

    for result in results:
        intent = result.get("actual_intent") or "unknown"
        by_intent[intent]["total"] += 1
        if result["passed"]:
            by_intent[intent]["passed"] += 1
        else:
            by_intent[intent]["failed"] += 1
        for check in result["checks"]:
            if check["passed"]:
                continue
            check_counter[check["name"]] += 1
            for detail in check["details"] or ["failed"]:
                reason = f"{check['name']}: {detail}"
                if check["name"] == "retrieval_support":
                    retrieval_gaps.append({"id": result["id"], "detail": detail})
                if result["passed"]:
                    warning_counter[reason] += 1
                else:
                    failure_counter[reason] += 1

    recommendations: list[str] = []
    if check_counter["intent"]:
        recommendations.append("Review intent classifier rules and add focused classifier tests.")
    if check_counter["required_services"] or check_counter["required_traits"]:
        recommendations.append("Update intent profiles or prompt templates to include missing service mappings and response traits.")
    if check_counter["citations"] or check_counter["grounding"]:
        recommendations.append("Improve retrieval corpus, chunk metadata, and citation selection for weakly grounded cases.")
    if check_counter["retrieval_support"]:
        recommendations.append("Add or retune source chunks for recommendations that are not supported by retrieved evidence.")
    if check_counter["evidence_links"] or check_counter["confidence"]:
        recommendations.append("Review advisory confidence scoring and recommendation-to-citation linking.")
    if check_counter["non_hallucination"] or check_counter["unsupported_oci_claims"]:
        recommendations.append("Tighten hallucination guardrails and review unsupported OCI service claims.")
    if check_counter["stale_unverified_guidance"]:
        recommendations.append("Strengthen release-awareness prompts so current guidance requires explicit release context.")
    if check_counter["architecture_quality"]:
        recommendations.append("Review architecture-quality dimensions, hallucination findings, and benchmark gaps before promotion.")
    if not recommendations:
        recommendations.append("No immediate eval failures. Add harder cases from real product failures.")

    return {
        "by_intent": dict(sorted(by_intent.items())),
        "score_summary": {
            "average": round(sum(scores) / len(scores), 1) if scores else 0,
            "minimum": min(scores) if scores else 0,
            "maximum": max(scores) if scores else 0,
        },
        "architecture_quality_summary": {
            "average": round(sum(architecture_scores) / len(architecture_scores), 3) if architecture_scores else 0.0,
            "minimum": round(min(architecture_scores), 3) if architecture_scores else 0.0,
            "maximum": round(max(architecture_scores), 3) if architecture_scores else 0.0,
        },
        "top_failure_reasons": failure_counter.most_common(10),
        "top_quality_warnings": warning_counter.most_common(10),
        "retrieval_gaps": retrieval_gaps,
        "failed_checks": dict(check_counter),
        "recommendations": recommendations,
        "quality_analytics": ResponseQualityAnalytics().summarize(results),
    }


def failure_diagnostics(result: dict[str, Any]) -> list[str]:
    if result["passed"]:
        return []

    checks = {check["name"]: check for check in result["checks"]}

    def details_for(name: str) -> str:
        details = checks.get(name, {}).get("details", [])
        return "; ".join(details) if details else "none"

    recommended_fix = "Review the failed checks and update the classifier, prompt template, retrieval corpus, or eval expectation."
    if not checks.get("intent", {}).get("passed", True):
        recommended_fix = "Adjust intent classifier keywords or add a focused classifier test."
    elif not checks.get("retrieval_support", {}).get("passed", True):
        recommended_fix = "Add source chunks or intent retrieval terms for the unsupported recommendation."
    elif not checks.get("non_hallucination", {}).get("passed", True):
        recommended_fix = "Tighten the response template to avoid unsafe certainty or invented OCI services."

    return [
        f"  expected_intent={result['expected_intent']}",
        f"  actual_intent={result['actual_intent']}",
        f"  missing_services={details_for('required_services')}",
        f"  unsupported_claims={details_for('unsupported_oci_claims')}; {details_for('non_hallucination')}",
        f"  weak_or_missing_evidence={details_for('grounding')}; {details_for('retrieval_support')}",
        f"  recommended_fix={recommended_fix}",
    ]


def write_reports(results: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC).isoformat()
    diagnostics = summarize_results(results)
    summary = {
        "generated_at": generated_at,
        "case_count": len(results),
        "passed": sum(1 for result in results if result["passed"]),
        "failed": sum(1 for result in results if not result["passed"]),
        "by_intent": diagnostics["by_intent"],
        "score_summary": diagnostics["score_summary"],
        "architecture_quality_summary": diagnostics["architecture_quality_summary"],
        "top_failure_reasons": diagnostics["top_failure_reasons"],
        "top_quality_warnings": diagnostics["top_quality_warnings"],
        "retrieval_gaps": diagnostics["retrieval_gaps"],
        "quality_analytics": diagnostics["quality_analytics"],
        "recommendations": diagnostics["recommendations"],
        "results": results,
    }
    report_name = output_dir.name.replace("_", "-").replace(" ", "-")
    (output_dir / f"{report_name}-report.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        f"# {report_name.title()} Eval Report",
        "",
        f"Generated: {generated_at}",
        "",
        f"Passed: {summary['passed']} / {summary['case_count']}",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|---|---:|",
        f"| Passed | {summary['passed']} |",
        f"| Failed | {summary['failed']} |",
        f"| Total | {summary['case_count']} |",
        "",
        "## Score Summary",
        "",
        "| Metric | Score |",
        "|---|---:|",
        f"| Average | {summary['score_summary']['average']} |",
        f"| Minimum | {summary['score_summary']['minimum']} |",
        f"| Maximum | {summary['score_summary']['maximum']} |",
        f"| Architecture Quality Avg | {summary['architecture_quality_summary']['average']} |",
        f"| Architecture Quality Min | {summary['architecture_quality_summary']['minimum']} |",
        "",
        "## Per-Intent Breakdown",
        "",
        "| Intent | Passed | Failed | Total |",
        "|---|---:|---:|---:|",
    ]
    for intent, stats in summary["by_intent"].items():
        lines.append(f"| {intent} | {stats['passed']} | {stats['failed']} | {stats['total']} |")
    lines.extend(
        [
            "",
            "## Top Failure Reasons",
            "",
        ]
    )
    if summary["top_failure_reasons"]:
        for reason, count in summary["top_failure_reasons"]:
            lines.append(f"- {count}x {reason}")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Top Quality Warnings",
            "",
        ]
    )
    if summary["top_quality_warnings"]:
        for reason, count in summary["top_quality_warnings"]:
            lines.append(f"- {count}x {reason}")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Retrieval Gaps",
            "",
        ]
    )
    if summary["retrieval_gaps"]:
        for gap in summary["retrieval_gaps"]:
            lines.append(f"- `{gap['id']}`: {gap['detail']}")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Quality Analytics",
            "",
            f"- Average citation coverage: `{summary['quality_analytics']['average_citation_coverage']}`",
            f"- Average retrieval influence: `{summary['quality_analytics']['average_retrieval_influence']}`",
            "- Top OCI service recommendations:",
        ]
    )
    for service, count in summary["quality_analytics"]["oci_service_recommendation_frequency"][:10]:
        lines.append(f"  - {count}x {service}")
    lines.append("- Hallucination trends:")
    if summary["quality_analytics"]["hallucination_trends"]:
        for category, count in summary["quality_analytics"]["hallucination_trends"]:
            lines.append(f"  - {count}x {category}")
    else:
        lines.append("  - None")
    lines.extend(
        [
            "",
            "## Recommendations",
            "",
        ]
    )
    lines.extend(f"- {recommendation}" for recommendation in summary["recommendations"])
    lines.extend(
        [
            "",
            "## Case Results",
            "",
            "| ID | Intent | Score | Result |",
            "|---|---|---:|---|",
        ]
    )
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        lines.append(
            f"| {result['id']} | {result['actual_intent']} | "
            f"{result['score']} / {result['minimum_score']} | {status} |"
        )
    lines.append("")
    for result in results:
        lines.extend(
            [
                f"## {result['id']}",
                "",
                f"Prompt: {result['prompt']}",
                "",
                f"Expected intent: `{result['expected_intent']}`",
                f"Actual intent: `{result['actual_intent']}`",
                f"Score: {result['score']} / {result['minimum_score']}",
                "",
                "Checks:",
            ]
        )
        for check in result["checks"]:
            status = "PASS" if check["passed"] else "FAIL"
            details = "; ".join(check["details"]) if check["details"] else ""
            lines.append(
                f"- {status} `{check['name']}`: {check['score']}/{check['max_score']} {details}"
            )
        lines.append("")
    (output_dir / f"{report_name}-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OCI Architecture Studio golden evals.")
    parser.add_argument(
        "--cases",
        type=Path,
        default=REPO_ROOT / "evals" / "golden-prompts.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "evals" / "reports",
    )
    parser.add_argument(
        "--no-write-reports",
        action="store_true",
        help="Run evals without writing JSON/Markdown reports.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases = load_cases(args.cases)
    client = TestClient(app)
    results = [evaluate_case(client, case) for case in cases]

    passed = sum(1 for result in results if result["passed"])
    failed = len(results) - passed
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        print(
            f"{status} {result['id']} "
            f"intent={result['actual_intent']} score={result['score']} min={result['minimum_score']}"
        )
        for line in failure_diagnostics(result):
            print(line)

    print(f"\nEval suite: {passed} passed, {failed} failed, {len(results)} total")
    if not args.no_write_reports:
        write_reports(results, args.output_dir)
        print(f"Reports written to {args.output_dir}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
