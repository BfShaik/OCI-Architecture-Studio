from __future__ import annotations

import argparse
import json
import ssl
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


def ssl_context() -> ssl.SSLContext | None:
    try:
        import certifi
    except ImportError:
        return None
    return ssl.create_default_context(cafile=certifi.where())


def fetch_json(url: str, timeout: int = 20) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "oci-architecture-studio-internal-beta/0.1"})
    with urlopen(request, timeout=timeout, context=ssl_context()) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict[str, Any], timeout: int = 40) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "oci-architecture-studio-internal-beta/0.1",
        },
    )
    with urlopen(request, timeout=timeout, context=ssl_context()) as response:
        return json.loads(response.read().decode("utf-8"))


def evaluate(base_url: str, *, require_oci_profile: bool = False) -> dict[str, Any]:
    base = base_url.rstrip("/")
    failures: list[str] = []
    warnings: list[str] = []
    endpoints = {
        "health": fetch_json(f"{base}/health"),
        "retrieval": fetch_json(f"{base}/retrieval/health"),
        "operations_health": fetch_json(f"{base}/operations/health"),
        "readiness": fetch_json(f"{base}/operations/readiness"),
        "infrastructure": fetch_json(f"{base}/operations/infrastructure"),
        "analytics": fetch_json(f"{base}/operations/analytics"),
        "refresh": fetch_json(f"{base}/knowledge/refresh/status"),
    }

    if endpoints["health"].get("status") != "ok":
        failures.append("health endpoint is not ok")
    retrieval_store = _dict(endpoints["retrieval"].get("store"))
    if not retrieval_store.get("exists"):
        failures.append("retrieval store is unavailable")
    if int(retrieval_store.get("chunk_count") or 0) < 40:
        warnings.append("retrieval chunk count is below the current internal-beta baseline of 40 chunks")

    readiness = endpoints["readiness"]
    if readiness.get("status") == "critical":
        failures.append("runtime readiness is critical")
    elif readiness.get("status") == "warning":
        warning_checks = set(readiness.get("warning_checks") or [])
        expected = {"api_gateway", "oci_devops", "release_refresh"}
        unexpected = sorted(warning_checks - expected)
        if unexpected:
            failures.append(f"runtime readiness has unexpected warning checks: {', '.join(unexpected)}")
        else:
            warnings.append(f"runtime readiness warnings accepted: {', '.join(sorted(warning_checks))}")

    infrastructure = endpoints["infrastructure"]
    environment = _dict(infrastructure.get("environment"))
    if require_oci_profile and environment.get("deployment_profile") == "local_dev":
        failures.append("OCI profile is required but deployment_profile is local_dev")
    if not infrastructure.get("topology"):
        failures.append("infrastructure topology visibility is missing")
    gap_summary = summarize_gaps(infrastructure.get("gaps") or [])
    if gap_summary["high"] or gap_summary["critical"]:
        failures.append("infrastructure has high or critical gaps")

    advisory_results = run_advisory_checks(base)
    for result in advisory_results:
        failures.extend(f"{result['id']}: {failure}" for failure in result["failures"])
        warnings.extend(f"{result['id']}: {warning}" for warning in result["warnings"])

    return {
        "status": "passed" if not failures else "failed",
        "base_url": base,
        "failures": failures,
        "warnings": warnings,
        "summary": {
            "deployment_profile": environment.get("deployment_profile"),
            "retrieval_provider": endpoints["retrieval"].get("provider"),
            "retrieval_chunk_count": retrieval_store.get("chunk_count", 0),
            "operations_status": endpoints["operations_health"].get("status"),
            "readiness_status": readiness.get("status"),
            "refresh_status": endpoints["refresh"].get("status"),
            "infrastructure_gap_summary": gap_summary,
        },
        "advisory_checks": advisory_results,
    }


def run_advisory_checks(base: str) -> list[dict[str, Any]]:
    cases = [
        {
            "id": "governance-executive-topology",
            "payload": {
                "question": "Create an enterprise OCI landing zone review with governance, IAM, Vault, Logging, Monitoring, risk prioritization, and executive summary.",
                "workload_context": "Regulated internal beta platform with architecture review board oversight.",
            },
            "required_intents": ("security", "architecture"),
            "checks": (
                "enterprise_governance",
                "executive_experience",
                "architecture_topology",
                "recommendation_priorities",
            ),
        },
        {
            "id": "migration-finops-optimization",
            "payload": {
                "question": "Plan a VMware migration to OCI with phased sequencing, coexistence, rollback, rightsizing, OCI Budgets/Cost Analysis cadence, and DR cost tiering.",
                "workload_context": "Enterprise production workload with staging validation and rollback gates.",
            },
            "required_intents": ("migration",),
            "checks": (
                "optimization_plan",
                "migration_phases",
                "finops_recommendations",
                "implementation_readiness",
            ),
        },
        {
            "id": "release-aware-freshness",
            "payload": {
                "question": "How should the latest OCI Object Storage release context affect a data platform architecture?",
                "workload_context": "Analytics platform with lifecycle policy, governance, and operational readiness requirements.",
            },
            "required_intents": ("release_awareness",),
            "checks": ("release_context", "knowledge_temporal_context", "citations"),
        },
    ]
    results = []
    for case in cases:
        case["payload"]["save_to_history"] = False
        response = post_json(f"{base}/architecture-review", case["payload"])
        failures: list[str] = []
        warnings: list[str] = []
        if response.get("intent") not in case["required_intents"]:
            failures.append(
                f"intent {response.get('intent')} did not match one of {', '.join(case['required_intents'])}"
            )
        if not response.get("citations"):
            failures.append("citations are missing")
        if response.get("not_enough_evidence"):
            warnings.append("response marked not_enough_evidence")
        for check in case["checks"]:
            validate_advisory_field(response, check, failures)
        results.append(
            {
                "id": case["id"],
                "intent": response.get("intent"),
                "confidence": _dict(response.get("confidence")).get("level"),
                "citation_count": len(response.get("citations") or []),
                "failures": failures,
                "warnings": warnings,
            }
        )
    return results


def validate_advisory_field(response: dict[str, Any], check: str, failures: list[str]) -> None:
    if check == "enterprise_governance":
        if not response.get("enterprise_governance"):
            failures.append("enterprise_governance metadata is missing")
    elif check == "executive_experience":
        if not response.get("executive_experience"):
            failures.append("executive_experience metadata is missing")
    elif check == "architecture_topology":
        if not response.get("architecture_topology"):
            failures.append("architecture_topology metadata is missing")
    elif check == "recommendation_priorities":
        governance = _dict(response.get("enterprise_governance"))
        if not governance.get("recommendation_priorities"):
            failures.append("recommendation priorities are missing")
    elif check == "optimization_plan":
        if not response.get("optimization_plan"):
            failures.append("optimization_plan metadata is missing")
    elif check == "migration_phases":
        if not _dict(response.get("optimization_plan")).get("migration_phases"):
            failures.append("migration phases are missing")
    elif check == "finops_recommendations":
        if not _dict(response.get("optimization_plan")).get("finops_recommendations"):
            failures.append("FinOps recommendations are missing")
    elif check == "implementation_readiness":
        readiness = _dict(response.get("optimization_plan")).get("implementation_readiness") or []
        if not any("Implementation readiness" in str(item) for item in readiness):
            failures.append("implementation readiness checks are missing")
    elif check == "release_context":
        if not response.get("release_context"):
            failures.append("release_context metadata is missing")
    elif check == "knowledge_temporal_context":
        if not response.get("knowledge_temporal_context"):
            failures.append("knowledge_temporal_context metadata is missing")
    elif check == "citations":
        if not response.get("citations"):
            failures.append("citations are missing")


def summarize_gaps(gaps: list[Any]) -> dict[str, int]:
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for gap in gaps:
        if isinstance(gap, dict):
            severity = str(gap.get("severity") or "").lower()
            if severity in summary:
                summary[severity] += 1
    return summary


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def write_reports(result: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "internal-beta-readiness.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Internal Beta Readiness Check",
        "",
        f"- Status: `{result['status']}`",
        f"- Base URL: `{result['base_url']}`",
        f"- Deployment profile: `{result['summary'].get('deployment_profile')}`",
        f"- Retrieval provider: `{result['summary'].get('retrieval_provider')}`",
        f"- Retrieval chunks: `{result['summary'].get('retrieval_chunk_count')}`",
        f"- Runtime readiness: `{result['summary'].get('readiness_status')}`",
        "",
    ]
    if result["failures"]:
        lines.extend(["## Failures", ""])
        lines.extend(f"- {failure}" for failure in result["failures"])
    if result["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result["warnings"])
    lines.extend(["", "## Advisory Checks", ""])
    for item in result["advisory_checks"]:
        lines.extend(
            [
                f"### {item['id']}",
                f"- Intent: `{item['intent']}`",
                f"- Confidence: `{item['confidence']}`",
                f"- Citations: `{item['citation_count']}`",
                f"- Failures: `{len(item['failures'])}`",
                f"- Warnings: `{len(item['warnings'])}`",
                "",
            ]
        )
    (output_dir / "internal-beta-readiness.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate internal beta readiness for OCI Architecture Studio.")
    parser.add_argument("--api-base-url", required=True)
    parser.add_argument("--require-oci-profile", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=Path("evals/reports/internal-beta-readiness"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = evaluate(args.api_base_url, require_oci_profile=args.require_oci_profile)
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        result = {
            "status": "failed",
            "base_url": args.api_base_url,
            "failures": [str(exc)],
            "warnings": [],
            "summary": {},
            "advisory_checks": [],
        }
    write_reports(result, args.output_dir)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
