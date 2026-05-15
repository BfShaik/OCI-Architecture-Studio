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


GENAI_REQUIRED_ENV = (
    "OCI_GENAI_COMPARTMENT_ID",
    "OCI_GENAI_CHAT_MODEL_ID",
)


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
    response = client.post("/architecture-review", json={"question": prompt})
    latency_ms = round((perf_counter() - started_at) * 1000, 2)
    response.raise_for_status()
    payload = response.json()
    payload["_latency_ms"] = latency_ms
    return payload


def summarize_response(response: dict[str, Any]) -> dict[str, Any]:
    confidence = response.get("confidence") or {}
    return {
        "intent": response.get("intent"),
        "synthesis_provider": response.get("synthesis_provider"),
        "synthesis_model": response.get("synthesis_model"),
        "synthesis_fallback_used": response.get("synthesis_fallback_used"),
        "latency_ms": response.get("_latency_ms"),
        "citation_count": len(response.get("citations", [])),
        "recommendation_count": len(response.get("recommendations", [])),
        "unsupported_claim_count": len(response.get("unsupported_claims", [])),
        "quality_warning_count": len(response.get("quality_warnings", [])),
        "not_enough_evidence": response.get("not_enough_evidence"),
        "low_confidence": response.get("low_confidence"),
        "overall_confidence": confidence.get("overall"),
        "confidence_level": confidence.get("level"),
    }


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
                summary = summarize_response(response)
                passed = (
                    summary["intent"] == case.get("expected_intent")
                    and summary["citation_count"] > 0
                    and not summary["synthesis_fallback_used"]
                    if provider == "oci_genai"
                    else summary["intent"] == case.get("expected_intent") and summary["citation_count"] > 0
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
        if candidate_summary.get("synthesis_fallback_used"):
            warnings.append("GenAI fallback was used")
        if candidate_summary.get("unsupported_claim_count", 0) > base_summary.get("unsupported_claim_count", 0):
            warnings.append("unsupported claim count increased")
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
                f"- Deterministic latency: `{item['deterministic'].get('latency_ms')} ms`",
                f"- OCI GenAI latency: `{item['oci_genai'].get('latency_ms')} ms`",
                "",
            ]
        )
    (output_dir / "genai-synthesis-parity-report.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare deterministic and OCI GenAI synthesis behavior.")
    parser.add_argument("--cases", type=Path, action="append", default=None)
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "evals" / "reports" / "genai-parity")
    parser.add_argument("--allow-skip", action="store_true")
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
            "deterministic": deterministic,
            "oci_genai": [],
            "comparisons": [],
        }
        write_reports(report, args.output_dir)
        print(json.dumps(report, indent=2))
        return 0 if args.allow_skip else 1

    genai = run_provider("oci_genai", cases, base_env)
    comparisons = compare_results(deterministic, genai)
    passed = sum(1 for item in comparisons if item["passed"])
    report = {
        "status": "passed" if passed == len(comparisons) else "failed",
        "summary": {"total": len(comparisons), "passed": passed, "failed": len(comparisons) - passed},
        "deterministic": deterministic,
        "oci_genai": genai,
        "comparisons": comparisons,
    }
    write_reports(report, args.output_dir)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
