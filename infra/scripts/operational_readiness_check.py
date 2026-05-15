from __future__ import annotations

import argparse
import json
import ssl
import sys
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


def ssl_context() -> ssl.SSLContext | None:
    try:
        import certifi
    except ImportError:
        return None
    return ssl.create_default_context(cafile=certifi.where())


def fetch_json(url: str, timeout: int = 15) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "oci-architecture-studio-operational-readiness/0.1"})
    with urlopen(request, timeout=timeout, context=ssl_context()) as response:
        return json.loads(response.read().decode("utf-8"))


def evaluate(base_url: str, *, require_oci_profile: bool = False) -> dict[str, Any]:
    base = base_url.rstrip("/")
    health = fetch_json(f"{base}/health")
    retrieval = fetch_json(f"{base}/retrieval/health")
    operations = fetch_json(f"{base}/operations/health")
    readiness = fetch_json(f"{base}/operations/readiness")
    infrastructure = fetch_json(f"{base}/operations/infrastructure")
    analytics = fetch_json(f"{base}/operations/analytics")

    failures: list[str] = []
    warnings: list[str] = []
    if health.get("status") != "ok":
        failures.append("backend health is not ok")
    store = retrieval.get("store", {}) if isinstance(retrieval.get("store"), dict) else {}
    if not store.get("exists"):
        failures.append("retrieval store is unavailable")
    if operations.get("status") == "critical":
        failures.append("operational health is critical")
    if operations.get("status") == "warning":
        warnings.append("operational health has warnings")
    if readiness.get("status") == "critical":
        failures.append("runtime readiness is critical")
    if readiness.get("status") == "warning":
        warnings.append("runtime readiness has warnings")
    deployment = operations.get("deployment", {}) if isinstance(operations.get("deployment"), dict) else {}
    infrastructure_environment = (
        infrastructure.get("environment", {}) if isinstance(infrastructure.get("environment"), dict) else {}
    )
    if require_oci_profile and infrastructure_environment.get("deployment_profile") == "local_dev":
        failures.append("OCI infrastructure visibility required but runtime reports local_dev")
    rebuildability = (
        infrastructure.get("rebuildability", {}) if isinstance(infrastructure.get("rebuildability"), dict) else {}
    )
    if rebuildability.get("status") == "warning":
        warnings.append("infrastructure rebuildability has warnings")
    if not infrastructure.get("topology"):
        failures.append("infrastructure topology visibility is unavailable")
    if require_oci_profile and deployment.get("profile") == "local_dev":
        failures.append("OCI deployment profile required but runtime reports local_dev")
    observability = analytics.get("observability", {}) if isinstance(analytics.get("observability"), dict) else {}
    metrics = observability.get("metrics", {}) if isinstance(observability.get("metrics"), dict) else {}

    return {
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "warnings": warnings,
        "profile": deployment.get("profile"),
        "retrieval_provider": retrieval.get("provider"),
        "retrieval_chunk_count": store.get("chunk_count", 0),
        "operational_status": operations.get("status"),
        "runtime_readiness_status": readiness.get("status"),
        "runtime_readiness_warnings": readiness.get("warning_checks", []),
        "infrastructure_rebuildability_status": rebuildability.get("status"),
        "infrastructure_gap_count": len(infrastructure.get("gaps", [])) if isinstance(infrastructure.get("gaps"), list) else 0,
        "request_count": metrics.get("request_count", 0),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate OCI Architecture Studio operational readiness endpoints.")
    parser.add_argument("--api-base-url", required=True)
    parser.add_argument("--require-oci-profile", action="store_true")
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = evaluate(args.api_base_url, require_oci_profile=args.require_oci_profile)
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        result = {"status": "failed", "failures": [str(exc)], "warnings": []}
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            file.write(text)
    print(text, end="")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
