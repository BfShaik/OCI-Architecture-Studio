from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_CHUNK_FIELDS = ("id", "source_id", "title", "url", "source_type", "text", "embedding", "metadata")
REQUIRED_METADATA_FIELDS = (
    "service",
    "service_domain",
    "source_url",
    "source_id",
    "source_type",
    "source_group",
    "freshness_score",
    "trust_level",
    "metadata_schema_version",
    "content_hash",
    "vector_ready",
)
REQUIRED_RELEASE_FIELDS = (
    "id",
    "source_id",
    "title",
    "source_url",
    "release_date",
    "service",
    "summary",
    "impact_level",
    "trust_level",
    "ingested_timestamp",
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def missing_keys(payload: dict[str, Any], required: tuple[str, ...]) -> list[str]:
    return [key for key in required if payload.get(key) in (None, "", [])]


def validate_knowledge_index(payload: dict[str, Any], *, min_chunks: int) -> list[str]:
    errors: list[str] = []
    chunks = payload.get("chunks")
    if not isinstance(chunks, list):
        return ["knowledge index chunks must be a list"]

    declared_chunk_count = payload.get("chunk_count")
    if declared_chunk_count != len(chunks):
        errors.append(f"chunk_count {declared_chunk_count!r} does not match actual chunk count {len(chunks)}")
    if len(chunks) < min_chunks:
        errors.append(f"chunk count {len(chunks)} is below required minimum {min_chunks}")

    dimensions = payload.get("dimensions")
    for chunk in chunks:
        if not isinstance(chunk, dict):
            errors.append("chunk entry is not an object")
            continue

        chunk_id = str(chunk.get("id") or "<missing id>")
        for key in missing_keys(chunk, REQUIRED_CHUNK_FIELDS):
            errors.append(f"{chunk_id} missing required chunk field {key}")

        embedding = chunk.get("embedding")
        if not isinstance(embedding, list) or not embedding:
            errors.append(f"{chunk_id} embedding is missing or empty")
        elif dimensions and len(embedding) != int(dimensions):
            errors.append(f"{chunk_id} embedding dimension {len(embedding)} does not match index dimensions {dimensions}")

        metadata = chunk.get("metadata")
        if not isinstance(metadata, dict):
            errors.append(f"{chunk_id} metadata is missing or not an object")
            continue
        for key in missing_keys(metadata, REQUIRED_METADATA_FIELDS):
            errors.append(f"{chunk_id} missing required metadata field {key}")
        if metadata.get("source_id") and metadata.get("source_id") != chunk.get("source_id"):
            errors.append(f"{chunk_id} metadata source_id does not match chunk source_id")

    return errors


def validate_release_snapshot(payload: dict[str, Any], *, min_releases: int) -> list[str]:
    errors: list[str] = []
    releases = payload.get("releases")
    if not isinstance(releases, list):
        return ["release snapshot releases must be a list"]

    declared_release_count = payload.get("release_count")
    if declared_release_count != len(releases):
        errors.append(
            f"release_count {declared_release_count!r} does not match actual release count {len(releases)}"
        )
    if len(releases) < min_releases:
        errors.append(f"release count {len(releases)} is below required minimum {min_releases}")

    for release in releases:
        if not isinstance(release, dict):
            errors.append("release entry is not an object")
            continue
        release_id = str(release.get("id") or release.get("title") or "<missing id>")
        for key in missing_keys(release, REQUIRED_RELEASE_FIELDS):
            errors.append(f"{release_id} missing required release field {key}")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a knowledge refresh candidate snapshot pair.")
    parser.add_argument("--knowledge-index", type=Path, required=True)
    parser.add_argument("--release-snapshot", type=Path, required=True)
    parser.add_argument("--min-chunks", type=int, default=40)
    parser.add_argument("--min-releases", type=int, default=1)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    knowledge_index = load_json(args.knowledge_index)
    release_snapshot = load_json(args.release_snapshot)
    errors = [
        *validate_knowledge_index(knowledge_index, min_chunks=args.min_chunks),
        *validate_release_snapshot(release_snapshot, min_releases=args.min_releases),
    ]
    report = {
        "passed": not errors,
        "knowledge_index": str(args.knowledge_index),
        "release_snapshot": str(args.release_snapshot),
        "chunk_count": len(knowledge_index.get("chunks", [])),
        "release_count": len(release_snapshot.get("releases", [])),
        "metadata_schema_version": knowledge_index.get("metadata_schema_version"),
        "embedding_provider": knowledge_index.get("embedding_provider"),
        "errors": errors,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if errors:
        print("FAIL refresh candidate validation", file=sys.stderr)
        return 1
    print("PASS refresh candidate validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
