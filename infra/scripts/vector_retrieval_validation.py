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


def load_cases(paths: list[Path]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in paths:
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    cases.append(json.loads(line))
    return cases


def build_settings(provider: str, args: argparse.Namespace, *, fallback_enabled: bool) -> Settings:
    return Settings(
        KNOWLEDGE_INDEX_PATH=args.index_path,
        RETRIEVAL_PROVIDER=provider,
        RETRIEVAL_FALLBACK_ENABLED=fallback_enabled,
        EMBEDDING_PROVIDER=args.embedding_provider,
        EMBEDDING_FALLBACK_ENABLED=args.embedding_fallback_enabled,
        OCI_GENAI_COMPARTMENT_ID=args.oci_genai_compartment_id,
        OCI_GENAI_EMBEDDING_MODEL_ID=args.oci_genai_embedding_model_id,
        OCI_GENAI_EMBEDDING_DIMENSIONS=args.oci_genai_embedding_dimensions,
        OCI_VECTOR_DB_DSN=args.oci_vector_db_dsn,
        OCI_VECTOR_DB_USER=args.oci_vector_db_user,
        OCI_VECTOR_DB_PASSWORD=args.oci_vector_db_password,
        OCI_VECTOR_TABLE_NAME=args.oci_vector_table_name,
        OCI_VECTOR_INDEX_NAME=args.oci_vector_index_name,
        OCI_VECTOR_DIMENSIONS=args.oci_vector_dimensions,
        OCI_VECTOR_DISTANCE_METRIC=args.oci_vector_distance_metric,
    )


async def run_case(case: dict[str, Any], retriever, classifier: IntentClassifier) -> dict[str, Any]:
    prompt = str(case["prompt"])
    intent = classifier.classify(prompt)
    profile = get_intent_profile(intent)
    started_at = perf_counter()
    sources = await retriever.retrieve(prompt, intent_profile=profile)
    latency_ms = round((perf_counter() - started_at) * 1000, 2)
    return {
        "id": case.get("id"),
        "intent": intent.value,
        "latency_ms": latency_ms,
        "top_chunks": [source.chunk_id for source in sources[:5]],
        "services": sorted({source.service for source in sources if source.service}),
        "service_domains": sorted({source.service_domain for source in sources if source.service_domain}),
        "citation_count": len(sources),
        "citation_urls_present": all(bool(source.source_url or source.url) for source in sources),
    }


def compare(local: dict[str, Any], vector: dict[str, Any]) -> dict[str, Any]:
    local_top = [chunk for chunk in local["top_chunks"] if chunk]
    vector_top = [chunk for chunk in vector["top_chunks"] if chunk]
    denominator = max(min(len(local_top), len(vector_top)), 1)
    overlap = len(set(local_top).intersection(vector_top)) / denominator
    return {
        "id": local["id"],
        "top_chunk_overlap": round(overlap, 3),
        "same_intent": local["intent"] == vector["intent"],
        "local": local,
        "oracle_vector": vector,
    }


def write_report(report: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "vector-retrieval-validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Vector Retrieval Validation",
        "",
        f"- Status: `{report['status']}`",
        f"- Cases: `{report['summary']['total']}`",
        f"- Average local latency: `{report['summary']['average_local_latency_ms']} ms`",
        f"- Average Oracle vector latency: `{report['summary']['average_oracle_vector_latency_ms']} ms`",
        f"- Average top chunk overlap: `{report['summary']['average_top_chunk_overlap']}`",
        "",
    ]
    if report.get("skip_reason"):
        lines.append(f"- Skip reason: {report['skip_reason']}")
    for result in report.get("results", []):
        lines.extend(
            [
                "",
                f"## {result['id']}",
                f"- Same intent: `{result['same_intent']}`",
                f"- Top chunk overlap: `{result['top_chunk_overlap']}`",
                f"- Local chunks: {', '.join(str(chunk) for chunk in result['local']['top_chunks'])}",
                f"- Oracle vector chunks: {', '.join(str(chunk) for chunk in result['oracle_vector']['top_chunks'])}",
            ]
        )
    (output_dir / "vector-retrieval-validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare local retrieval with Oracle AI Vector Search retrieval.")
    parser.add_argument("--cases", type=Path, action="append", default=None)
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "evals" / "reports" / "vector-retrieval")
    parser.add_argument("--index-path", type=Path, default=REPO_ROOT / "knowledge" / "snapshots" / "oci-rag-index.json")
    parser.add_argument("--embedding-provider", choices=("local", "oci_genai"), default="local")
    parser.add_argument("--embedding-fallback-enabled", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--oci-genai-compartment-id")
    parser.add_argument("--oci-genai-embedding-model-id")
    parser.add_argument("--oci-genai-embedding-dimensions", type=int)
    parser.add_argument("--oci-vector-db-dsn")
    parser.add_argument("--oci-vector-db-user")
    parser.add_argument("--oci-vector-db-password")
    parser.add_argument("--oci-vector-table-name", default="OCI_ARCHITECTURE_CHUNKS")
    parser.add_argument("--oci-vector-index-name", default="OCI_ARCH_CHUNKS_VEC_IDX")
    parser.add_argument("--oci-vector-dimensions", type=int, default=256)
    parser.add_argument("--oci-vector-distance-metric", default="COSINE")
    parser.add_argument("--allow-skip", action="store_true")
    return parser.parse_args()


async def async_main() -> int:
    args = parse_args()
    cases = load_cases(args.cases or [REPO_ROOT / "evals" / "golden-prompts.jsonl"])
    classifier = IntentClassifier()
    local = build_retriever(build_settings("local_json", args, fallback_enabled=True))
    vector = build_retriever(build_settings("oracle_ai_vector_search", args, fallback_enabled=False))
    local_health = local.diagnostics()
    vector_health = vector.diagnostics()
    if not isinstance(vector_health.get("store"), dict) or not vector_health["store"].get("exists"):
        report = {
            "status": "skipped" if args.allow_skip else "failed",
            "skip_reason": "Oracle AI Vector Search is unavailable or not configured.",
            "health": {"local": local_health, "oracle_vector": vector_health},
            "summary": {
                "total": 0,
                "average_local_latency_ms": 0.0,
                "average_oracle_vector_latency_ms": 0.0,
                "average_top_chunk_overlap": 0.0,
            },
            "results": [],
        }
        write_report(report, args.output_dir)
        print(json.dumps(report, indent=2))
        return 0 if args.allow_skip else 1

    results = []
    for case in cases:
        local_result = await run_case(case, local, classifier)
        vector_result = await run_case(case, vector, classifier)
        results.append(compare(local_result, vector_result))
    report = {
        "status": "passed",
        "health": {"local": local_health, "oracle_vector": vector_health},
        "summary": {
            "total": len(results),
            "average_local_latency_ms": round(mean(result["local"]["latency_ms"] for result in results), 2) if results else 0.0,
            "average_oracle_vector_latency_ms": round(mean(result["oracle_vector"]["latency_ms"] for result in results), 2) if results else 0.0,
            "average_top_chunk_overlap": round(mean(result["top_chunk_overlap"] for result in results), 3) if results else 0.0,
        },
        "results": results,
    }
    write_report(report, args.output_dir)
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))
