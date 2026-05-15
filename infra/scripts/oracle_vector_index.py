from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_SRC = REPO_ROOT / "app" / "backend" / "src"
sys.path.append(str(BACKEND_SRC))

from oci_arch_studio_backend.services.vector_store import (  # noqa: E402
    OracleAiVectorSearchConfig,
    OracleAiVectorSearchStore,
    VectorChunk,
)


def load_chunks(index_path: Path) -> list[VectorChunk]:
    with index_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return [
        VectorChunk(
            id=str(chunk["id"]),
            title=str(chunk["title"]),
            url=chunk.get("url"),
            source_type=str(chunk.get("source_type", "oci_doc")),
            text=str(chunk["text"]),
            embedding=[float(value) for value in chunk["embedding"]],
            metadata=dict(chunk.get("metadata", {})),
        )
        for chunk in payload.get("chunks", [])
    ]


def local_index_health(chunks: list[VectorChunk], expected_dimensions: int) -> dict[str, Any]:
    empty_embeddings = [chunk.id for chunk in chunks if not chunk.embedding]
    dimension_mismatches = [
        {"chunk_id": chunk.id, "dimensions": len(chunk.embedding)}
        for chunk in chunks
        if chunk.embedding and len(chunk.embedding) != expected_dimensions
    ]
    metadata_missing = [
        chunk.id
        for chunk in chunks
        if not chunk.metadata.get("service") or not chunk.metadata.get("service_domain")
    ]
    return {
        "chunk_count": len(chunks),
        "expected_dimensions": expected_dimensions,
        "empty_embeddings": empty_embeddings[:20],
        "dimension_mismatches": dimension_mismatches[:20],
        "metadata_missing": metadata_missing[:20],
        "valid": not empty_embeddings and not dimension_mismatches and not metadata_missing,
    }


def build_store(args: argparse.Namespace) -> OracleAiVectorSearchStore:
    return OracleAiVectorSearchStore(
        OracleAiVectorSearchConfig(
            dsn=args.oci_vector_db_dsn,
            username=args.oci_vector_db_user,
            password=args.oci_vector_db_password,
            wallet_location=args.oci_vector_wallet_location,
            wallet_password=args.oci_vector_wallet_password,
            table_name=args.oci_vector_table_name,
            index_name=args.oci_vector_index_name,
            dimensions=args.oci_vector_dimensions,
            distance_metric=args.oci_vector_distance_metric,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage Oracle AI Vector Search indexes for OCI Architecture Studio.")
    parser.add_argument(
        "action",
        choices=("print-schema", "validate-local-index", "health", "create-schema", "create-index", "rebuild"),
    )
    parser.add_argument("--index-path", type=Path, default=REPO_ROOT / "knowledge" / "snapshots" / "oci-rag-index.json")
    parser.add_argument("--oci-vector-db-dsn")
    parser.add_argument("--oci-vector-db-user")
    parser.add_argument("--oci-vector-db-password")
    parser.add_argument("--oci-vector-wallet-location")
    parser.add_argument("--oci-vector-wallet-password")
    parser.add_argument("--oci-vector-table-name", default="OCI_ARCHITECTURE_CHUNKS")
    parser.add_argument("--oci-vector-index-name", default="OCI_ARCH_CHUNKS_VEC_IDX")
    parser.add_argument("--oci-vector-dimensions", type=int, default=256)
    parser.add_argument("--oci-vector-distance-metric", default="COSINE")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    store = build_store(args)

    if args.action == "print-schema":
        for statement in (*store.schema_sql(), store.vector_index_sql()):
            print(statement + ";\n")
        return 0

    chunks = load_chunks(args.index_path)
    local_health = local_index_health(chunks, args.oci_vector_dimensions)
    if args.action == "validate-local-index":
        print(json.dumps(local_health, indent=2))
        return 0 if local_health["valid"] else 1

    if not local_health["valid"] and args.action in {"rebuild"}:
        print(json.dumps({"status": "failed", "reason": "local index is not vector-ready", "local_index": local_health}, indent=2))
        return 1

    if args.action == "health":
        print(json.dumps({"local_index": local_health, "oracle_vector": store.health()}, indent=2))
        return 0 if args.dry_run or store.health().get("exists") else 1

    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run",
                    "action": args.action,
                    "local_index": local_health,
                    "oracle_vector": store.health(),
                },
                indent=2,
            )
        )
        return 0

    if args.action == "create-schema":
        store.create_schema()
        print(json.dumps({"status": "created_schema", "oracle_vector": store.health()}, indent=2))
        return 0

    if args.action == "create-index":
        store.create_vector_index()
        print(json.dumps({"status": "created_vector_index", "oracle_vector": store.health()}, indent=2))
        return 0

    if args.action == "rebuild":
        store.create_schema()
        upserted = store.upsert_chunks(chunks)
        print(json.dumps({"status": "rebuilt", "upserted": upserted, "oracle_vector": store.health()}, indent=2))
        return 0

    raise AssertionError(f"Unsupported action: {args.action}")


if __name__ == "__main__":
    raise SystemExit(main())
