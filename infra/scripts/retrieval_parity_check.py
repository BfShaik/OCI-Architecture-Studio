from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_SRC = REPO_ROOT / "app" / "backend" / "src"
sys.path.append(str(BACKEND_SRC))

from oci_arch_studio_backend.core.config import Settings  # noqa: E402
from oci_arch_studio_backend.services.intents import IntentClassifier, get_intent_profile  # noqa: E402
from oci_arch_studio_backend.services.retrieval import build_retriever  # noqa: E402


REQUIRED_METADATA_FIELDS = (
    "chunk_id",
    "source_url",
    "service",
    "service_domain",
    "intent_tags",
    "fetched_timestamp",
    "freshness_score",
    "trust_level",
)


def load_cases(paths: list[Path]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
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


def metadata_completeness(citation: Any) -> float:
    present = 0
    for field in REQUIRED_METADATA_FIELDS:
        value = getattr(citation, field)
        if value not in (None, "", []):
            present += 1
    return round(present / len(REQUIRED_METADATA_FIELDS), 3)


def build_settings(
    provider: str,
    args: argparse.Namespace,
    object_name: str | None = None,
    fallback_enabled: bool | None = None,
) -> Settings:
    return Settings(
        KNOWLEDGE_INDEX_PATH=args.index_path,
        RETRIEVAL_PROVIDER=provider,
        RETRIEVAL_FALLBACK_ENABLED=args.retrieval_fallback_enabled if fallback_enabled is None else fallback_enabled,
        EMBEDDING_PROVIDER=args.embedding_provider,
        EMBEDDING_FALLBACK_ENABLED=args.embedding_fallback_enabled,
        OCI_REGION=args.oci_region,
        OCI_PROFILE=args.oci_profile,
        OCI_AUTH_MODE=args.oci_auth_mode,
        OCI_OBJECT_STORAGE_NAMESPACE=args.oci_namespace,
        OCI_VECTOR_BUCKET=args.oci_vector_bucket,
        OCI_VECTOR_OBJECT_NAME=object_name or args.oci_vector_object_name,
        OCI_GENAI_COMPARTMENT_ID=args.oci_genai_compartment_id,
        OCI_GENAI_EMBEDDING_MODEL_ID=args.oci_genai_embedding_model_id,
        OCI_GENAI_EMBEDDING_DIMENSIONS=args.oci_genai_embedding_dimensions,
        OCI_GENAI_ENDPOINT=args.oci_genai_endpoint,
        OCI_VECTOR_DB_DSN=args.oci_vector_db_dsn,
        OCI_VECTOR_DB_USER=args.oci_vector_db_user,
        OCI_VECTOR_DB_PASSWORD=args.oci_vector_db_password,
        OCI_VECTOR_TABLE_NAME=args.oci_vector_table_name,
        OCI_VECTOR_INDEX_NAME=args.oci_vector_index_name,
        OCI_VECTOR_DIMENSIONS=args.oci_vector_dimensions,
        OCI_VECTOR_DISTANCE_METRIC=args.oci_vector_distance_metric,
    )


async def run_provider_case(case: dict[str, Any], provider: str, retriever, classifier: IntentClassifier) -> dict[str, Any]:
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
    metadata_scores = [metadata_completeness(source) for source in citations]

    return {
        "provider": provider,
        "expected_intent": expected_intent,
        "actual_intent": intent.value,
        "latency_ms": latency_ms,
        "citation_count": len(citations),
        "top_chunks": [source.chunk_id for source in citations[:5]],
        "services": sorted(services),
        "service_domains": sorted({source.service_domain for source in citations if source.service_domain}),
        "architecture_patterns": sorted(
            {
                pattern
                for source in citations
                for pattern in source.architecture_patterns
            }
        ),
        "missing_services": missing_services,
        "missing_citations": missing_citations,
        "stale_citations": stale_citations,
        "metadata_completeness": round(mean(metadata_scores), 3) if metadata_scores else 0.0,
        "trust_levels": sorted({source.trust_level for source in citations if source.trust_level}),
        "citation_source_urls_present": not missing_citations,
    }


def compare_results(
    case: dict[str, Any],
    local: dict[str, Any],
    oci_native: dict[str, Any],
    min_top_overlap: float,
    max_latency_ms: float,
) -> dict[str, Any]:
    local_top = [chunk for chunk in local["top_chunks"] if chunk]
    oci_top = [chunk for chunk in oci_native["top_chunks"] if chunk]
    denominator = max(min(len(local_top), len(oci_top)), 1)
    overlap = len(set(local_top).intersection(oci_top)) / denominator
    latency_ratio = (
        round(float(oci_native["latency_ms"]) / max(float(local["latency_ms"]), 0.01), 2)
        if local["latency_ms"] is not None
        else None
    )
    mismatches: list[str] = []
    if local["actual_intent"] != oci_native["actual_intent"]:
        mismatches.append("intent mismatch")
    if overlap < min_top_overlap:
        mismatches.append(f"top chunk overlap below {min_top_overlap:.0%}")
    if local["missing_services"] or oci_native["missing_services"]:
        mismatches.append("required service evidence missing")
    if oci_native["missing_citations"]:
        mismatches.append("OCI-native provider returned citations without URLs")
    if len(oci_native["stale_citations"]) > len(local["stale_citations"]):
        mismatches.append("OCI-native provider surfaced more stale citations")
    if oci_native["metadata_completeness"] < local["metadata_completeness"]:
        mismatches.append("OCI-native provider has weaker metadata completeness")
    latency_warning = float(oci_native["latency_ms"]) > max_latency_ms
    if latency_warning:
        mismatches.append(f"OCI-native latency above {max_latency_ms} ms")

    passed = not mismatches
    return {
        "id": case.get("id"),
        "prompt": case.get("prompt"),
        "expected_intent": case.get("expected_intent"),
        "passed": passed,
        "mismatches": mismatches,
        "top_chunk_overlap": round(overlap, 3),
        "same_top_order": local_top == oci_top,
        "latency_ratio": latency_ratio,
        "latency_warning": latency_warning,
        "local": local,
        "oci_native": oci_native,
    }


def health_summary(retriever) -> dict[str, Any]:
    diagnostics = retriever.diagnostics()
    store = diagnostics.get("store", {})
    return {
        "provider": diagnostics.get("provider"),
        "embedding_model": diagnostics.get("embedding_model"),
        "store": store,
        "metrics": diagnostics.get("metrics", {}),
        "exists": isinstance(store, dict) and bool(store.get("exists")),
        "chunk_count": int(store.get("chunk_count", 0)) if isinstance(store, dict) else 0,
    }


def write_reports(
    results: list[dict[str, Any]],
    health: dict[str, Any],
    output_dir: Path,
    *,
    status: str,
    skip_reason: str | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    passed = sum(1 for result in results if result["passed"])
    failed = len(results) - passed
    avg_local_latency = round(mean(float(result["local"]["latency_ms"]) for result in results), 2) if results else 0.0
    avg_oci_latency = round(mean(float(result["oci_native"]["latency_ms"]) for result in results), 2) if results else 0.0
    avg_overlap = round(mean(float(result["top_chunk_overlap"]) for result in results), 3) if results else 0.0
    report = {
        "status": status,
        "skip_reason": skip_reason,
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "average_top_chunk_overlap": avg_overlap,
            "average_local_latency_ms": avg_local_latency,
            "average_oci_native_latency_ms": avg_oci_latency,
        },
        "health": health,
        "results": results,
        "promotion_criteria": [
            "All parity cases pass.",
            "Golden and edge eval pass rates remain unchanged.",
            "No required service evidence regressions.",
            "No citation URL regressions.",
            "No stale citation regressions.",
            "OCI-native latency remains acceptable for staging.",
            "Rollback to local_json is validated by configuration.",
        ],
    }
    (output_dir / "retrieval-parity-report.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Retrieval Parity Report",
        "",
        f"- Status: `{status}`",
        f"- Total cases: {len(results)}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        f"- Average top chunk overlap: {avg_overlap}",
        f"- Average local latency: `{avg_local_latency} ms`",
        f"- Average OCI-native latency: `{avg_oci_latency} ms`",
        "",
        "## Provider Health",
        "",
        f"- Local provider: `{health['local'].get('provider')}`",
        f"- Local chunks: `{health['local'].get('chunk_count')}`",
        f"- OCI-native provider: `{health['oci_native'].get('provider')}`",
        f"- OCI-native chunks: `{health['oci_native'].get('chunk_count')}`",
        "",
        "## Promotion Criteria",
        "",
        "- all parity cases pass",
        "- golden and edge eval pass rates remain unchanged",
        "- no grounding, citation, metadata, or stale-source regressions",
        "- rollback to `local_json` remains config-only",
        "",
        "## Cases",
        "",
    ]
    if skip_reason:
        lines.extend([f"- Skip reason: {skip_reason}", ""])
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        lines.extend(
            [
                f"### {status} {result['id']}",
                "",
                f"- Intent: `{result['local']['actual_intent']}` / `{result['oci_native']['actual_intent']}`",
                f"- Top chunk overlap: `{result['top_chunk_overlap']}`",
                f"- Same top order: `{result['same_top_order']}`",
                f"- Latency ratio: `{result['latency_ratio']}`",
                f"- Local top chunks: {', '.join(str(chunk) for chunk in result['local']['top_chunks'])}",
                f"- OCI-native top chunks: {', '.join(str(chunk) for chunk in result['oci_native']['top_chunks'])}",
                f"- Local services: {', '.join(result['local']['services']) or 'none'}",
                f"- OCI-native services: {', '.join(result['oci_native']['services']) or 'none'}",
            ]
        )
        if result["mismatches"]:
            lines.append(f"- Mismatches: {', '.join(result['mismatches'])}")
        lines.append("")

    (output_dir / "retrieval-parity-report.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare local and OCI-native retrieval providers.")
    parser.add_argument("--cases", type=Path, action="append", default=None)
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "evals" / "reports" / "retrieval-parity")
    parser.add_argument("--index-path", type=Path, default=REPO_ROOT / "knowledge" / "snapshots" / "oci-rag-index.json")
    parser.add_argument(
        "--baseline-provider",
        choices=("local_json", "oci_object_storage"),
        default="local_json",
        help="Provider to use as the known-good baseline.",
    )
    parser.add_argument(
        "--oci-native-provider",
        choices=("oci_object_storage", "oracle_ai_vector_search"),
        default="oci_object_storage",
        help="OCI-native provider to compare against the baseline.",
    )
    parser.add_argument("--embedding-provider", choices=("local", "oci_genai"), default="local")
    parser.add_argument("--retrieval-fallback-enabled", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--oci-region")
    parser.add_argument("--oci-profile", default="DEFAULT")
    parser.add_argument("--oci-auth-mode", choices=("config_file", "instance_principal", "resource_principal"), default="config_file")
    parser.add_argument("--embedding-fallback-enabled", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--oci-namespace")
    parser.add_argument("--oci-vector-bucket")
    parser.add_argument("--oci-vector-object-name", default="oci-rag-index.json")
    parser.add_argument("--oci-genai-compartment-id")
    parser.add_argument("--oci-genai-embedding-model-id")
    parser.add_argument("--oci-genai-embedding-dimensions", type=int)
    parser.add_argument("--oci-genai-endpoint")
    parser.add_argument("--oci-vector-db-dsn")
    parser.add_argument("--oci-vector-db-user")
    parser.add_argument("--oci-vector-db-password")
    parser.add_argument("--oci-vector-table-name", default="OCI_ARCHITECTURE_CHUNKS")
    parser.add_argument("--oci-vector-index-name", default="OCI_ARCH_CHUNKS_VEC_IDX")
    parser.add_argument("--oci-vector-dimensions", type=int, default=256)
    parser.add_argument("--oci-vector-distance-metric", default="COSINE")
    parser.add_argument("--min-top-overlap", type=float, default=0.8)
    parser.add_argument("--max-latency-ms", type=float, default=250.0)
    parser.add_argument("--allow-skip", action="store_true")
    return parser.parse_args()


async def async_main() -> int:
    args = parse_args()
    case_paths = args.cases or [
        REPO_ROOT / "evals" / "golden-prompts.jsonl",
        REPO_ROOT / "evals" / "edge-cases.jsonl",
    ]
    cases = load_cases(case_paths)
    classifier = IntentClassifier()

    if args.oci_native_provider == "oci_object_storage" and (not args.oci_namespace or not args.oci_vector_bucket):
        health = {
            "local": {},
            "oci_native": {
                "provider": args.oci_native_provider,
                "exists": False,
                "missing_config": ["OCI_OBJECT_STORAGE_NAMESPACE", "OCI_VECTOR_BUCKET"],
            },
        }
        write_reports(
            [],
            health,
            args.output_dir,
            status="skipped" if args.allow_skip else "failed",
            skip_reason="OCI Object Storage namespace and bucket are required for Object Storage parity.",
        )
        print(json.dumps(health, indent=2))
        return 0 if args.allow_skip else 1

    local_retriever = build_retriever(build_settings(args.baseline_provider, args, fallback_enabled=True))
    oci_retriever = build_retriever(build_settings(args.oci_native_provider, args, fallback_enabled=False))
    health = {
        "local": health_summary(local_retriever),
        "oci_native": health_summary(oci_retriever),
    }
    print(json.dumps(health, indent=2))
    if not health["local"]["exists"] or not health["oci_native"]["exists"]:
        skip_reason = "one or more retrieval providers are unavailable"
        write_reports(
            [],
            health,
            args.output_dir,
            status="skipped" if args.allow_skip else "failed",
            skip_reason=skip_reason,
        )
        print(f"{'SKIP' if args.allow_skip else 'FAIL'} {skip_reason}", file=sys.stderr)
        return 0 if args.allow_skip else 1
    if health["local"]["chunk_count"] != health["oci_native"]["chunk_count"]:
        print("FAIL provider chunk counts differ", file=sys.stderr)
        return 1

    results: list[dict[str, Any]] = []
    for case in cases:
        local = await run_provider_case(case, args.baseline_provider, local_retriever, classifier)
        oci_native = await run_provider_case(case, args.oci_native_provider, oci_retriever, classifier)
        results.append(
            compare_results(
                case=case,
                local=local,
                oci_native=oci_native,
                min_top_overlap=args.min_top_overlap,
                max_latency_ms=args.max_latency_ms,
            )
        )

    failed = [result for result in results if not result["passed"]]
    write_reports(results, health, args.output_dir, status="passed" if not failed else "failed")
    if failed:
        print(f"FAIL {len(failed)} parity case(s) failed", file=sys.stderr)
        for result in failed:
            print(f"- {result['id']}: {', '.join(result['mismatches'])}", file=sys.stderr)
        return 1
    print(f"PASS {len(results)} parity case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))
