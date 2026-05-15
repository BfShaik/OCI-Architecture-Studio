from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from time import perf_counter


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_SRC = REPO_ROOT / "app" / "backend" / "src"
sys.path.append(str(BACKEND_SRC))

from oci_arch_studio_backend.core.config import Settings  # noqa: E402
from oci_arch_studio_backend.services.intents import IntentClassifier, get_intent_profile  # noqa: E402
from oci_arch_studio_backend.services.retrieval import build_retriever  # noqa: E402


def load_cases(paths: list[Path]) -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []
    for path in paths:
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    cases.append(json.loads(line))
    return cases


def normalize(value: str) -> str:
    return value.lower().replace("oci ", "").replace("/", " ").replace("-", " ").strip()


def required_service_matches(required: str, services: set[str], titles: set[str], summaries: str) -> bool:
    required_norm = normalize(required)
    aliases = {
        "load balancing": ("load balancer", "traffic to backend resources"),
        "oci database": ("database services", "autonomous database", "base database service"),
        "right sized compute": ("right-sized compute", "compute"),
        "autoscaling": ("autoscaling", "auto scaling"),
        "rto rpo": ("rto and rpo", "rto", "rpo"),
    }
    haystack = " ".join((*services, *titles, *summaries.split()[:180])).lower()
    normalized_haystack = normalize(haystack)
    if required_norm in normalized_haystack or required.lower() in haystack:
        return True
    return any(alias in haystack for alias in aliases.get(required_norm, ()))


async def run_case(case: dict[str, object], retriever, classifier: IntentClassifier) -> dict[str, object]:
    prompt = str(case["prompt"])
    expected_intent = str(case.get("expected_intent", "general"))
    intent = classifier.classify(prompt)
    profile = get_intent_profile(intent)
    started_at = perf_counter()
    citations = await retriever.retrieve(prompt, intent_profile=profile)
    latency_ms = round((perf_counter() - started_at) * 1000, 2)

    services = {source.service or "" for source in citations if source.service}
    titles = {source.title for source in citations}
    summaries = " ".join(source.summary for source in citations)
    missing_services = [
        service
        for service in case.get("required_services", [])
        if not required_service_matches(str(service), services, titles, summaries)
    ]
    missing_citations = [
        source.chunk_id or source.title
        for source in citations
        if not source.source_url and not source.url
    ]
    stale_citations = [source.chunk_id or source.title for source in citations if source.is_stale]
    passed = (
        intent.value == expected_intent
        and not missing_services
        and not missing_citations
        and bool(citations)
        and all(source.source_type != "missing_index" for source in citations)
    )

    return {
        "id": case.get("id"),
        "prompt": prompt,
        "expected_intent": expected_intent,
        "actual_intent": intent.value,
        "passed": passed,
        "latency_ms": latency_ms,
        "citation_count": len(citations),
        "top_chunks": [source.chunk_id for source in citations[:5]],
        "services": sorted(services),
        "missing_services": missing_services,
        "missing_citations": missing_citations,
        "stale_citations": stale_citations,
    }


def write_reports(results: list[dict[str, object]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    passed = sum(1 for result in results if result["passed"])
    failed = len(results) - passed
    report = {
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
        },
        "results": results,
    }
    (output_dir / "retrieval-regression-report.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Retrieval Regression Report",
        "",
        f"- Total: {len(results)}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        "",
        "## Cases",
        "",
    ]
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        lines.extend(
            [
                f"### {status} {result['id']}",
                "",
                f"- Expected intent: `{result['expected_intent']}`",
                f"- Actual intent: `{result['actual_intent']}`",
                f"- Latency: `{result['latency_ms']} ms`",
                f"- Citations: `{result['citation_count']}`",
                f"- Services: {', '.join(result['services']) or 'none'}",
                f"- Top chunks: {', '.join(str(chunk) for chunk in result['top_chunks']) or 'none'}",
            ]
        )
        if result["missing_services"]:
            lines.append(f"- Missing services: {', '.join(result['missing_services'])}")
        if result["missing_citations"]:
            lines.append(f"- Missing citation URLs: {', '.join(result['missing_citations'])}")
        if result["stale_citations"]:
            lines.append(f"- Stale citations: {', '.join(result['stale_citations'])}")
        lines.append("")

    (output_dir / "retrieval-regression-report.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run retrieval quality regression checks.")
    parser.add_argument(
        "--cases",
        type=Path,
        action="append",
        default=None,
        help="JSONL eval case file. Can be provided multiple times.",
    )
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "evals" / "reports" / "retrieval")
    parser.add_argument("--provider", choices=("local_json", "oci_object_storage", "oracle_ai_vector_search"), default="local_json")
    parser.add_argument("--index-path", type=Path, default=REPO_ROOT / "knowledge" / "snapshots" / "oci-rag-index.json")
    parser.add_argument("--embedding-provider", choices=("local", "oci_genai"), default="local")
    parser.add_argument("--retrieval-fallback-enabled", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--oci-region")
    parser.add_argument("--oci-profile", default="DEFAULT")
    parser.add_argument("--oci-auth-mode", choices=("config_file", "instance_principal", "resource_principal"), default="config_file")
    parser.add_argument("--embedding-fallback-enabled", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--oci-namespace")
    parser.add_argument("--oci-vector-bucket")
    parser.add_argument("--oci-vector-object-name", default="knowledge/oci-rag-index.json")
    parser.add_argument("--oci-genai-compartment-id")
    parser.add_argument("--oci-genai-embedding-model-id")
    parser.add_argument("--oci-genai-embedding-dimensions", type=int)
    parser.add_argument("--oci-genai-endpoint")
    parser.add_argument("--oci-vector-db-dsn")
    parser.add_argument("--oci-vector-db-user")
    parser.add_argument("--oci-vector-db-password")
    parser.add_argument("--oci-vector-wallet-location")
    parser.add_argument("--oci-vector-wallet-password")
    parser.add_argument("--oci-vector-table-name", default="OCI_ARCHITECTURE_CHUNKS")
    parser.add_argument("--oci-vector-index-name", default="OCI_ARCH_CHUNKS_VEC_IDX")
    parser.add_argument("--oci-vector-dimensions", type=int, default=256)
    parser.add_argument("--oci-vector-distance-metric", default="COSINE")
    return parser.parse_args()


async def async_main() -> int:
    args = parse_args()
    settings = Settings(
        KNOWLEDGE_INDEX_PATH=args.index_path,
        RETRIEVAL_PROVIDER=args.provider,
        RETRIEVAL_FALLBACK_ENABLED=args.retrieval_fallback_enabled,
        EMBEDDING_PROVIDER=args.embedding_provider,
        EMBEDDING_FALLBACK_ENABLED=args.embedding_fallback_enabled,
        OCI_REGION=args.oci_region,
        OCI_PROFILE=args.oci_profile,
        OCI_AUTH_MODE=args.oci_auth_mode,
        OCI_OBJECT_STORAGE_NAMESPACE=args.oci_namespace,
        OCI_VECTOR_BUCKET=args.oci_vector_bucket,
        OCI_VECTOR_OBJECT_NAME=args.oci_vector_object_name,
        OCI_GENAI_COMPARTMENT_ID=args.oci_genai_compartment_id,
        OCI_GENAI_EMBEDDING_MODEL_ID=args.oci_genai_embedding_model_id,
        OCI_GENAI_EMBEDDING_DIMENSIONS=args.oci_genai_embedding_dimensions,
        OCI_GENAI_ENDPOINT=args.oci_genai_endpoint,
        OCI_VECTOR_DB_DSN=args.oci_vector_db_dsn,
        OCI_VECTOR_DB_USER=args.oci_vector_db_user,
        OCI_VECTOR_DB_PASSWORD=args.oci_vector_db_password,
        OCI_VECTOR_WALLET_LOCATION=args.oci_vector_wallet_location,
        OCI_VECTOR_WALLET_PASSWORD=args.oci_vector_wallet_password,
        OCI_VECTOR_TABLE_NAME=args.oci_vector_table_name,
        OCI_VECTOR_INDEX_NAME=args.oci_vector_index_name,
        OCI_VECTOR_DIMENSIONS=args.oci_vector_dimensions,
        OCI_VECTOR_DISTANCE_METRIC=args.oci_vector_distance_metric,
    )
    retriever = build_retriever(settings)
    health = retriever.diagnostics()
    print(json.dumps(health, indent=2))
    if not isinstance(health.get("store"), dict) or not health["store"].get("exists"):
        print("FAIL retrieval store is missing or unreachable", file=sys.stderr)
        return 1

    classifier = IntentClassifier()
    case_paths = args.cases or [REPO_ROOT / "evals" / "golden-prompts.jsonl"]
    results = [await run_case(case, retriever, classifier) for case in load_cases(case_paths)]
    write_reports(results, args.output_dir)
    failed = [result for result in results if not result["passed"]]
    if failed:
        print(f"FAIL {len(failed)} retrieval regression case(s) failed", file=sys.stderr)
        for result in failed:
            print(
                f"- {result['id']}: intent {result['actual_intent']} expected {result['expected_intent']}; "
                f"missing services={result['missing_services']}",
                file=sys.stderr,
            )
        return 1
    print(f"PASS {len(results)} retrieval regression case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))
