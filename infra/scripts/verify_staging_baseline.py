from __future__ import annotations

import argparse
import json
import sys
from urllib.request import Request, urlopen


def fetch_json(url: str, timeout: int = 10) -> dict:
    request = Request(url, headers={"User-Agent": "oci-architecture-studio-baseline/0.1"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str, timeout: int = 10) -> str:
    request = Request(url, headers={"User-Agent": "oci-architecture-studio-baseline/0.1"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def post_json(url: str, payload: dict, timeout: int = 20) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "oci-architecture-studio-baseline/0.1",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def check_baseline(
    api_base_url: str,
    frontend_url: str,
    expected_chunks: int,
    expected_retrieval_provider: str,
) -> dict[str, object]:
    api_base_url = api_base_url.rstrip("/")
    checks: list[dict[str, object]] = []

    health = fetch_json(f"{api_base_url}/health")
    checks.append(
        {
            "name": "backend_health",
            "passed": health.get("status") == "ok",
            "detail": health,
        }
    )

    retrieval = fetch_json(f"{api_base_url}/retrieval/health")
    store = retrieval.get("store", {})
    checks.append(
        {
            "name": "retrieval_health",
            "passed": (
                retrieval.get("provider") == expected_retrieval_provider
                and store.get("exists") is True
                and int(store.get("chunk_count", 0)) >= expected_chunks
            ),
            "detail": {
                "provider": retrieval.get("provider"),
                "expected_provider": expected_retrieval_provider,
                "chunk_count": store.get("chunk_count"),
                "warnings": retrieval.get("metrics", {}).get("warnings", []),
            },
        }
    )

    review = post_json(
        f"{api_base_url}/architecture-review",
        {"question": "Design a highly available ecommerce platform on OCI."},
    )
    checks.append(
        {
            "name": "architecture_review",
            "passed": review.get("intent") == "architecture" and len(review.get("citations", [])) >= 1,
            "detail": {
                "intent": review.get("intent"),
                "citations": len(review.get("citations", [])),
            },
        }
    )

    frontend = fetch_text(frontend_url)
    checks.append(
        {
            "name": "frontend_reachability",
            "passed": "<div id=\"root\"></div>" in frontend and "./assets/" in frontend,
            "detail": {
                "has_root": "<div id=\"root\"></div>" in frontend,
                "uses_relative_assets": "./assets/" in frontend,
            },
        }
    )

    passed = all(check["passed"] for check in checks)
    return {"passed": passed, "checks": checks}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify OCI Architecture Studio staging baseline.")
    parser.add_argument("--api-base-url", required=True)
    parser.add_argument("--frontend-url", required=True)
    parser.add_argument("--expected-chunks", type=int, default=13)
    parser.add_argument("--expected-retrieval-provider", default="local_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = check_baseline(
            args.api_base_url,
            args.frontend_url,
            args.expected_chunks,
            args.expected_retrieval_provider,
        )
    except Exception as exc:  # noqa: BLE001 - guardrail script reports actionable failure.
        print(json.dumps({"passed": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
