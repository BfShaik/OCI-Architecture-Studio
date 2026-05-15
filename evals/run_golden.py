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


SUPPORTED_OCI_TERMS = {
    "autonomous database",
    "architecture center",
    "base database service",
    "budgets",
    "cdn",
    "cloud guard",
    "compute",
    "cost analysis",
    "data guard",
    "database migration",
    "database services overview",
    "dns",
    "fastconnect",
    "full stack disaster recovery",
    "iam",
    "kubernetes engine",
    "load balancer",
    "logging",
    "monitoring",
    "mysql heatwave",
    "network security groups",
    "object storage",
    "oke",
    "oracle base database service",
    "oracle cloud infrastructure",
    "security zones",
    "security services overview",
    "vault",
    "virtual cloud network",
    "vcn",
    "waf",
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
    "oci database": ["oci database", "database", "autonomous database", "base database", "mysql heatwave"],
    "oci kubernetes engine": ["oci kubernetes engine", "oke", "kubernetes engine"],
    "oke": ["oke", "kubernetes engine"],
    "rds": ["rds", "database migration"],
    "right-sized compute": ["right-sized compute", "compute", "right-sized"],
    "rto/rpo": ["rto", "rpo", "recovery"],
    "vault": ["vault", "key management", "secrets"],
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
    response = client.post("/architecture-review", json={"question": prompt})
    response.raise_for_status()
    return response.json()


def validate_structure(response: dict[str, Any]) -> EvalCheck:
    required_fields = {
        "intent": str,
        "prompt_template": str,
        "synthesis_provider": str,
        "synthesis_warnings": list,
        "synthesis_fallback_used": bool,
        "answer": str,
        "recommendations": list,
        "assumptions": list,
        "risks": list,
        "citations": list,
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
    checks = [
        validate_structure(response),
        validate_intent(case, response),
        validate_required_terms("required_services", case.get("required_services", []), text, 15),
        validate_required_terms("required_traits", case.get("required_traits", []), text, 20),
        validate_citations(case, response),
        validate_grounding(case, response),
        validate_retrieval_support(case, response),
        validate_evidence_links(case, response),
        validate_confidence(case, response),
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
            "non_hallucination",
            "stale_unverified_guidance",
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
    if not recommendations:
        recommendations.append("No immediate eval failures. Add harder cases from real product failures.")

    return {
        "by_intent": dict(sorted(by_intent.items())),
        "score_summary": {
            "average": round(sum(scores) / len(scores), 1) if scores else 0,
            "minimum": min(scores) if scores else 0,
            "maximum": max(scores) if scores else 0,
        },
        "top_failure_reasons": failure_counter.most_common(10),
        "top_quality_warnings": warning_counter.most_common(10),
        "retrieval_gaps": retrieval_gaps,
        "failed_checks": dict(check_counter),
        "recommendations": recommendations,
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
        "top_failure_reasons": diagnostics["top_failure_reasons"],
        "top_quality_warnings": diagnostics["top_quality_warnings"],
        "retrieval_gaps": diagnostics["retrieval_gaps"],
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
