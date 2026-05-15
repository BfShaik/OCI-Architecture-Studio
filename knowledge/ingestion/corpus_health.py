from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REQUIRED_METADATA = (
    "service",
    "service_domain",
    "service_category",
    "intent_tags",
    "architecture_patterns",
    "workload_types",
    "domain_tags",
    "source_url",
    "content_hash",
    "parent_document_id",
    "section_title",
    "chunk_type",
)


def load_index(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def corpus_health(index: dict[str, Any], *, min_chunks: int = 1) -> dict[str, Any]:
    chunks = list(index.get("chunks", []))
    ids = [str(chunk.get("id")) for chunk in chunks]
    source_ids = [str(chunk.get("source_id")) for chunk in chunks if chunk.get("source_id")]
    content_hashes = [
        str(chunk.get("metadata", {}).get("content_hash"))
        for chunk in chunks
        if chunk.get("metadata", {}).get("content_hash")
    ]
    metadata_scores = [_metadata_score(chunk.get("metadata", {})) for chunk in chunks]
    missing_service_tags = [
        chunk.get("id")
        for chunk in chunks
        if not chunk.get("metadata", {}).get("service") or not chunk.get("metadata", {}).get("service_domain")
    ]
    empty_embeddings = [
        chunk.get("id")
        for chunk in chunks
        if not chunk.get("embedding") or not any(abs(float(value)) > 0 for value in chunk.get("embedding", []))
    ]
    duplicate_ids = sorted(item for item, count in Counter(ids).items() if count > 1)
    duplicate_hashes = sorted(item for item, count in Counter(content_hashes).items() if count > 1)
    source_chunk_counts = Counter(source_ids)
    orphaned_chunks = [
        chunk.get("id")
        for chunk in chunks
        if not chunk.get("source_id") or not chunk.get("metadata", {}).get("parent_document_id")
    ]
    domain_counts = Counter(
        str(chunk.get("metadata", {}).get("service_domain"))
        for chunk in chunks
        if chunk.get("metadata", {}).get("service_domain")
    )
    category_counts = Counter(
        str(chunk.get("metadata", {}).get("category"))
        for chunk in chunks
        if chunk.get("metadata", {}).get("category")
    )
    coverage_gaps = _coverage_gaps(chunks)
    failures = []
    if len(chunks) < min_chunks:
        failures.append(f"chunk count {len(chunks)} below minimum {min_chunks}")
    if missing_service_tags:
        failures.append(f"{len(missing_service_tags)} chunk(s) missing service tags")
    if empty_embeddings:
        failures.append(f"{len(empty_embeddings)} chunk(s) have empty embeddings")
    if duplicate_ids:
        failures.append(f"{len(duplicate_ids)} duplicate chunk id(s)")
    if duplicate_hashes:
        failures.append(f"{len(duplicate_hashes)} duplicate content hash(es)")
    if orphaned_chunks:
        failures.append(f"{len(orphaned_chunks)} orphaned chunk(s)")
    if coverage_gaps:
        failures.append("retrieval coverage gaps: " + ", ".join(coverage_gaps))

    return {
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "chunk_count": len(chunks),
        "source_count": len(set(source_ids)),
        "service_count": len({chunk.get("metadata", {}).get("service") for chunk in chunks if chunk.get("metadata", {}).get("service")}),
        "service_domain_count": len(domain_counts),
        "metadata_completeness": round(sum(metadata_scores) / len(metadata_scores), 3) if metadata_scores else 0.0,
        "missing_service_tags": missing_service_tags[:20],
        "empty_embeddings": empty_embeddings[:20],
        "duplicate_ids": duplicate_ids[:20],
        "duplicate_content_hashes": duplicate_hashes[:20],
        "orphaned_chunks": orphaned_chunks[:20],
        "service_domain_counts": dict(sorted(domain_counts.items())),
        "category_counts": dict(sorted(category_counts.items())),
        "source_chunk_counts": dict(sorted(source_chunk_counts.items())),
        "coverage_gaps": coverage_gaps,
    }


def _metadata_score(metadata: dict[str, Any]) -> float:
    present = sum(1 for field in REQUIRED_METADATA if metadata.get(field) not in (None, "", []))
    return present / len(REQUIRED_METADATA)


def _coverage_gaps(chunks: list[dict[str, Any]]) -> list[str]:
    required_domains = {"architecture", "networking", "database", "security", "observability", "cost", "resilience"}
    required_categories = {"migration", "cost-optimization", "security", "resilience"}
    domains = {str(chunk.get("metadata", {}).get("service_domain")) for chunk in chunks}
    categories = {str(chunk.get("metadata", {}).get("category")) for chunk in chunks}
    intent_tags = {
        str(tag)
        for chunk in chunks
        for tag in chunk.get("metadata", {}).get("intent_tags", [])
    }
    gaps = [f"domain:{domain}" for domain in sorted(required_domains - domains)]
    gaps.extend(f"category:{category}" for category in sorted(required_categories - categories))
    for intent in ("architecture", "migration", "dr", "cost", "security", "observability"):
        if intent not in intent_tags:
            gaps.append(f"intent:{intent}")
    return gaps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate OCI Architecture Studio corpus health.")
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--min-chunks", type=int, default=1)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = corpus_health(load_index(args.index), min_chunks=args.min_chunks)
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
