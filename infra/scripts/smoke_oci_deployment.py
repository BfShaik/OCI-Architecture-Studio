from __future__ import annotations

import argparse
import json
import ssl
import sys
from urllib.error import URLError
from urllib.request import Request, urlopen


def ssl_context() -> ssl.SSLContext | None:
    try:
        import certifi
    except ImportError:
        return None
    return ssl.create_default_context(cafile=certifi.where())


def fetch_json(url: str, timeout: int = 10) -> dict:
    request = Request(url, headers={"User-Agent": "oci-architecture-studio-smoke/0.1"})
    with urlopen(request, timeout=timeout, context=ssl_context()) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict, timeout: int = 20) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "oci-architecture-studio-smoke/0.1",
        },
    )
    with urlopen(request, timeout=timeout, context=ssl_context()) as response:
        return json.loads(response.read().decode("utf-8"))


def check_backend(api_base_url: str) -> None:
    health = fetch_json(f"{api_base_url.rstrip('/')}/health")
    assert health["status"] == "ok", health
    operations = fetch_json(f"{api_base_url.rstrip('/')}/operations/health")
    assert operations["status"] in {"ok", "warning"}, operations

    architecture_review = post_json(
        f"{api_base_url.rstrip('/')}/architecture-review",
        {"question": "Design a highly available ecommerce platform on OCI.", "save_to_history": False},
    )
    assert architecture_review["intent"] == "architecture", architecture_review
    assert architecture_review["citations"], architecture_review
    first = architecture_review["citations"][0]
    assert first.get("source_url") or first.get("url"), first

    release_review = post_json(
        f"{api_base_url.rstrip('/')}/architecture-review",
        {"question": "How does the latest OCI update affect this architecture?", "save_to_history": False},
    )
    assert release_review["intent"] == "release_awareness", release_review
    assert release_review["citations"], release_review

    print(
        "PASS backend: "
        f"{len(architecture_review['citations'])} architecture citations, "
        f"{len(release_review['citations'])} release-aware citations, "
        f"operations={operations['status']}"
    )


def check_frontend(frontend_url: str) -> None:
    request = Request(frontend_url, headers={"User-Agent": "oci-architecture-studio-smoke/0.1"})
    with urlopen(request, timeout=10, context=ssl_context()) as response:
        body = response.read().decode("utf-8", errors="ignore")
    assert response.status == 200, response.status
    assert "root" in body or "OCI Architecture Studio" in body, body[:200]
    print("PASS frontend")


def check_oci_cli() -> None:
    try:
        import oci
    except ImportError:
        print("SKIP OCI SDK: package not installed")
        return

    config = oci.config.from_file()
    identity = oci.identity.IdentityClient(config)
    tenancy = identity.get_tenancy(config["tenancy"]).data
    assert tenancy.id == config["tenancy"]
    print(f"PASS OCI SDK: tenancy {tenancy.name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test OCI Architecture Studio deployment.")
    parser.add_argument("--api-base-url", required=True, help="Backend API base URL, e.g. http://1.2.3.4:8000")
    parser.add_argument("--frontend-url", help="Frontend URL to verify.")
    parser.add_argument("--check-oci-sdk", action="store_true", help="Verify local OCI SDK config can read tenancy.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        check_backend(args.api_base_url)
        if args.frontend_url:
            check_frontend(args.frontend_url)
        if args.check_oci_sdk:
            check_oci_cli()
    except (AssertionError, URLError, TimeoutError) as exc:
        print(f"FAIL smoke test: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
