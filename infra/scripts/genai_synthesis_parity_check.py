from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_SRC = REPO_ROOT / "app" / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

from fastapi.testclient import TestClient  # noqa: E402
from oci_arch_studio_backend.core.config import get_settings  # noqa: E402
from oci_arch_studio_backend.main import app  # noqa: E402
from oci_arch_studio_backend.services.evaluation_intelligence import ArchitectureQualityScorer  # noqa: E402


GENAI_REQUIRED_ENV = (
    "OCI_GENAI_COMPARTMENT_ID",
    "OCI_GENAI_CHAT_MODEL_ID",
)

DEFAULT_MAX_LATENCY_RATIO = 8.0
DEFAULT_MAX_LATENCY_MS = 30000.0


@contextmanager
def patched_env(values: dict[str, str]) -> Iterator[None]:
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    get_settings.cache_clear()
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        get_settings.cache_clear()


def load_cases(paths: list[Path]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in paths:
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    cases.append(json.loads(line))
    return cases


def execute_case(client: TestClient, prompt: str) -> dict[str, Any]:
    started_at = perf_counter()
    response = client.post(
        "/architecture-review",
        json={"question": prompt, "synthesis_debug": True, "save_to_history": False},
    )
    latency_ms = round((perf_counter() - started_at) * 1000, 2)
    response.raise_for_status()
    payload = response.json()
    payload["_latency_ms"] = latency_ms
    return payload


def summarize_response(response: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    confidence = response.get("confidence") or {}
    synthesis_quality = response.get("synthesis_quality") or {}
    synthesis_debug = response.get("synthesis_debug") or {}
    architecture_quality = ArchitectureQualityScorer().score(response).as_dict()
    missing_services = missing_required_services(response, case)
    return {
        "intent": response.get("intent"),
        "synthesis_provider": response.get("synthesis_provider"),
        "synthesis_model": response.get("synthesis_model"),
        "synthesis_fallback_used": response.get("synthesis_fallback_used"),
        "latency_ms": response.get("_latency_ms"),
        "citation_count": len(response.get("citations", [])),
        "recommendation_count": len(response.get("recommendations", [])),
        "decision_reasoning_count": len(response.get("decision_reasoning", [])),
        "consistency_finding_count": len(response.get("consistency_findings", [])),
        "unsupported_claim_count": len(response.get("unsupported_claims", [])),
        "quality_warning_count": len(response.get("quality_warnings", [])),
        "not_enough_evidence": response.get("not_enough_evidence"),
        "low_confidence": response.get("low_confidence"),
        "overall_confidence": confidence.get("overall"),
        "confidence_level": confidence.get("level"),
        "grounding_quality": synthesis_quality.get("grounding_quality"),
        "oci_specificity": synthesis_quality.get("oci_specificity"),
        "workload_alignment": synthesis_quality.get("workload_alignment"),
        "migration_accuracy": synthesis_quality.get("migration_accuracy"),
        "recommendation_diversity": synthesis_quality.get("recommendation_diversity"),
        "citation_coverage": synthesis_quality.get("citation_coverage"),
        "synthesis_quality_overall": synthesis_quality.get("overall"),
        "architecture_quality_overall": architecture_quality.get("overall"),
        "hallucination_count": len(architecture_quality.get("hallucination_findings", [])),
        "high_hallucination_count": sum(
            1
            for finding in architecture_quality.get("hallucination_findings", [])
            if finding.get("severity") == "high"
        ),
        "tradeoff_quality": (
            architecture_quality.get("dimensions", {})
            .get("tradeoff_quality", {})
            .get("score")
        ),
        "operational_realism": (
            architecture_quality.get("dimensions", {})
            .get("operational_realism", {})
            .get("score")
        ),
        "prompt_sections": synthesis_debug.get("grounding_prompt_sections", []),
        "estimated_input_tokens": synthesis_debug.get("estimated_input_tokens"),
        "token_usage": synthesis_debug.get("token_usage", {}),
        "required_services": [str(item) for item in case.get("required_services", [])],
        "missing_required_services": missing_services,
        "required_service_coverage": 1.0
        if not case.get("required_services")
        else round(
            (len(case.get("required_services", [])) - len(missing_services))
            / max(len(case.get("required_services", [])), 1),
            3,
        ),
    }


def missing_required_services(response: dict[str, Any], case: dict[str, Any]) -> list[str]:
    required = [str(item) for item in case.get("required_services", [])]
    if not required:
        return []
    citations = response.get("citations", [])
    text_parts = [
        str(response.get("answer") or ""),
        " ".join(str(item) for item in response.get("recommendations", [])),
        " ".join(str(item) for item in response.get("assumptions", [])),
        " ".join(str(item) for item in response.get("risks", [])),
        " ".join(str(item) for item in response.get("next_steps", [])),
    ]
    for citation in citations:
        if isinstance(citation, dict):
            text_parts.extend(
                str(citation.get(key) or "")
                for key in ("title", "summary", "service", "service_domain", "source_url", "url")
            )
    haystack = " ".join(text_parts).lower()
    return [service for service in required if not _service_matches(service, haystack)]


def _service_matches(service: str, haystack: str) -> bool:
    normalized = service.lower()
    aliases = {
        "database": ("database", "autonomous database", "database services", "base database"),
        "rds": ("rds", "database migration", "autonomous database", "database services"),
        "oke": ("oke", "oci kubernetes engine", "kubernetes engine"),
        "load balancer": ("load balancer", "load balancing"),
        "object storage": ("object storage", "bucket"),
        "logging": ("logging", "logs"),
        "monitoring": ("monitoring", "metrics", "alarms"),
    }
    terms = aliases.get(normalized, (normalized,))
    return any(term in haystack for term in terms)


def run_provider(
    provider: str,
    cases: list[dict[str, Any]],
    base_env: dict[str, str],
) -> list[dict[str, Any]]:
    env = {**base_env, "ADVISORY_SYNTHESIS_PROVIDER": provider}
    results: list[dict[str, Any]] = []
    with patched_env(env):
        client = TestClient(app)
        for case in cases:
            try:
                response = execute_case(client, str(case["prompt"]))
                summary = summarize_response(response, case)
                passed = (
                    summary["intent"] == case.get("expected_intent")
                    and summary["citation_count"] > 0
                    and not summary["missing_required_services"]
                    and not summary["synthesis_fallback_used"]
                    if provider == "oci_genai"
                    else summary["intent"] == case.get("expected_intent")
                    and summary["citation_count"] > 0
                    and not summary["missing_required_services"]
                )
                results.append(
                    {
                        "id": case.get("id"),
                        "expected_intent": case.get("expected_intent"),
                        "passed": passed,
                        "summary": summary,
                    }
                )
            except Exception as exc:  # noqa: BLE001 - parity report should capture provider failures.
                results.append(
                    {
                        "id": case.get("id"),
                        "expected_intent": case.get("expected_intent"),
                        "passed": False,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
    return results


def compare_results(
    deterministic: list[dict[str, Any]],
    genai: list[dict[str, Any]],
    *,
    max_latency_ratio: float,
    max_latency_ms: float,
) -> list[dict[str, Any]]:
    comparisons: list[dict[str, Any]] = []
    genai_by_id = {item["id"]: item for item in genai}
    for base in deterministic:
        candidate = genai_by_id.get(base["id"], {})
        base_summary = base.get("summary", {})
        candidate_summary = candidate.get("summary", {})
        warnings: list[str] = []
        if candidate.get("error"):
            warnings.append(str(candidate["error"]))
        if base_summary.get("intent") != candidate_summary.get("intent"):
            warnings.append("intent mismatch")
        if int(candidate_summary.get("citation_count") or 0) < int(base_summary.get("citation_count") or 0):
            warnings.append("citation count regressed")
        if candidate_summary.get("missing_required_services"):
            warnings.append(
                "required service coverage missing: "
                + ", ".join(candidate_summary.get("missing_required_services", []))
            )
        if candidate_summary.get("synthesis_fallback_used"):
            warnings.append("GenAI fallback was used")
        if candidate_summary.get("unsupported_claim_count", 0) > base_summary.get("unsupported_claim_count", 0):
            warnings.append("unsupported claim count increased")
        if candidate_summary.get("hallucination_count", 0) > base_summary.get("hallucination_count", 0):
            warnings.append("hallucination finding count increased")
        if candidate_summary.get("high_hallucination_count", 0) > 0:
            warnings.append("high-severity hallucination finding present")
        for metric in (
            "grounding_quality",
            "oci_specificity",
            "migration_accuracy",
            "synthesis_quality_overall",
            "architecture_quality_overall",
            "tradeoff_quality",
            "operational_realism",
        ):
            base_value = _float_or_none(base_summary.get(metric))
            candidate_value = _float_or_none(candidate_summary.get(metric))
            if base_value is not None and candidate_value is not None and candidate_value + 0.15 < base_value:
                warnings.append(f"{metric} regressed by more than 0.15")
        if candidate_summary.get("synthesis_provider") == "oci_genai" and not candidate_summary.get("prompt_sections"):
            warnings.append("missing synthesis grounding prompt debug sections")
        base_latency = _float_or_none(base_summary.get("latency_ms"))
        candidate_latency = _float_or_none(candidate_summary.get("latency_ms"))
        if candidate_latency is not None and candidate_latency > max_latency_ms:
            warnings.append(f"OCI GenAI latency exceeded {max_latency_ms:.0f} ms")
        if (
            base_latency is not None
            and candidate_latency is not None
            and base_latency > 0
            and candidate_latency / base_latency > max_latency_ratio
        ):
            warnings.append(f"OCI GenAI latency exceeded {max_latency_ratio:.1f}x deterministic latency")
        comparisons.append(
            {
                "id": base["id"],
                "passed": not warnings and bool(candidate.get("passed")),
                "warnings": warnings,
                "deterministic": base_summary,
                "oci_genai": candidate_summary,
            }
        )
    return comparisons


def _float_or_none(value: object) -> float | None:
    return float(value) if isinstance(value, int | float) else None


def write_reports(report: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "genai-synthesis-parity-report.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# GenAI Synthesis Parity Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Cases: `{report['summary']['total']}`",
        f"- Passed: `{report['summary']['passed']}`",
        f"- Failed: `{report['summary']['failed']}`",
        f"- Recommendation: `{report['recommendation']}`",
        "",
        "## Cases",
        "",
    ]
    for item in report["comparisons"]:
        status = "PASS" if item["passed"] else "FAIL"
        lines.extend(
            [
                f"### {status} {item['id']}",
                "",
                f"- Warnings: {', '.join(item['warnings']) or 'none'}",
                f"- Deterministic provider: `{item['deterministic'].get('synthesis_provider')}`",
                f"- OCI GenAI provider: `{item['oci_genai'].get('synthesis_provider')}`",
                f"- Missing OCI GenAI services: `{', '.join(item['oci_genai'].get('missing_required_services', [])) or 'none'}`",
                f"- Deterministic latency: `{item['deterministic'].get('latency_ms')} ms`",
                f"- OCI GenAI latency: `{item['oci_genai'].get('latency_ms')} ms`",
                f"- Deterministic quality: `{item['deterministic'].get('synthesis_quality_overall')}`",
                f"- OCI GenAI quality: `{item['oci_genai'].get('synthesis_quality_overall')}`",
                f"- OCI GenAI prompt sections: `{', '.join(item['oci_genai'].get('prompt_sections', []))}`",
                "",
            ]
        )
    (output_dir / "genai-synthesis-parity-report.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare deterministic and OCI GenAI synthesis behavior.")
    parser.add_argument("--cases", type=Path, action="append", default=None)
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "evals" / "reports" / "genai-parity")
    parser.add_argument("--allow-skip", action="store_true")
    parser.add_argument("--max-latency-ratio", type=float, default=DEFAULT_MAX_LATENCY_RATIO)
    parser.add_argument("--max-latency-ms", type=float, default=DEFAULT_MAX_LATENCY_MS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    case_paths = args.cases or [REPO_ROOT / "evals" / "golden-prompts.jsonl"]
    cases = load_cases(case_paths)
    base_env = {
        "RETRIEVAL_PROVIDER": os.getenv("RETRIEVAL_PROVIDER", "local_json"),
        "EMBEDDING_PROVIDER": os.getenv("EMBEDDING_PROVIDER", "local"),
        "ADVISORY_ORCHESTRATION_MODE": os.getenv("ADVISORY_ORCHESTRATION_MODE", "multi_agent_pilot"),
    }
    deterministic = run_provider("deterministic", cases, base_env)
    missing = [name for name in GENAI_REQUIRED_ENV if not os.getenv(name)]
    if missing:
        report = {
            "status": "skipped",
            "reason": f"Missing required OCI GenAI environment variables: {', '.join(missing)}",
            "summary": {"total": len(cases), "passed": 0, "failed": 0},
            "recommendation": "do_not_promote_missing_live_genai_configuration",
            "deterministic": deterministic,
            "oci_genai": [],
            "comparisons": [],
        }
        write_reports(report, args.output_dir)
        print(json.dumps(report, indent=2))
        return 0 if args.allow_skip else 1

    genai = run_provider("oci_genai", cases, base_env)
    comparisons = compare_results(
        deterministic,
        genai,
        max_latency_ratio=args.max_latency_ratio,
        max_latency_ms=args.max_latency_ms,
    )
    passed = sum(1 for item in comparisons if item["passed"])
    status = "passed" if passed == len(comparisons) else "failed"
    report = {
        "status": status,
        "summary": {"total": len(comparisons), "passed": passed, "failed": len(comparisons) - passed},
        "recommendation": "eligible_for_controlled_synthesis_promotion_review"
        if status == "passed"
        else "do_not_promote_investigate_parity_failures",
        "deterministic": deterministic,
        "oci_genai": genai,
        "comparisons": comparisons,
    }
    write_reports(report, args.output_dir)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
