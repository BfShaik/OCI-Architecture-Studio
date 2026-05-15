from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_SRC = REPO_ROOT / "app" / "backend" / "src"
sys.path.append(str(BACKEND_SRC))

from oci_arch_studio_backend.core.config import Settings  # noqa: E402
from oci_arch_studio_backend.services.retrieval import build_retriever  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate retrieval provider health.")
    parser.add_argument(
        "--provider",
        choices=("local_json", "oci_object_storage", "oracle_ai_vector_search"),
        default="local_json",
    )
    parser.add_argument("--index-path", type=Path, default=REPO_ROOT / "knowledge" / "snapshots" / "oci-rag-index.json")
    parser.add_argument("--embedding-provider", choices=("local", "oci_genai"), default="local")
    parser.add_argument("--oci-region")
    parser.add_argument("--oci-profile", default="DEFAULT")
    parser.add_argument("--oci-auth-mode", choices=("config_file", "instance_principal"), default="config_file")
    parser.add_argument("--oci-namespace")
    parser.add_argument("--oci-vector-bucket")
    parser.add_argument("--oci-vector-object-name", default="knowledge/oci-rag-index.json")
    parser.add_argument("--oci-genai-compartment-id")
    parser.add_argument("--oci-genai-embedding-model-id")
    parser.add_argument("--oci-genai-endpoint")
    parser.add_argument("--oci-vector-db-dsn")
    parser.add_argument("--oci-vector-db-user")
    parser.add_argument("--oci-vector-db-password")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = Settings(
        KNOWLEDGE_INDEX_PATH=args.index_path,
        RETRIEVAL_PROVIDER=args.provider,
        EMBEDDING_PROVIDER=args.embedding_provider,
        OCI_REGION=args.oci_region,
        OCI_PROFILE=args.oci_profile,
        OCI_AUTH_MODE=args.oci_auth_mode,
        OCI_OBJECT_STORAGE_NAMESPACE=args.oci_namespace,
        OCI_VECTOR_BUCKET=args.oci_vector_bucket,
        OCI_VECTOR_OBJECT_NAME=args.oci_vector_object_name,
        OCI_GENAI_COMPARTMENT_ID=args.oci_genai_compartment_id,
        OCI_GENAI_EMBEDDING_MODEL_ID=args.oci_genai_embedding_model_id,
        OCI_GENAI_ENDPOINT=args.oci_genai_endpoint,
        OCI_VECTOR_DB_DSN=args.oci_vector_db_dsn,
        OCI_VECTOR_DB_USER=args.oci_vector_db_user,
        OCI_VECTOR_DB_PASSWORD=args.oci_vector_db_password,
    )
    retriever = build_retriever(settings)
    diagnostics = retriever.diagnostics()
    print(json.dumps(diagnostics, indent=2))

    store = diagnostics["store"]
    if not isinstance(store, dict) or not store.get("exists"):
        print("FAIL retrieval store is missing or unreachable", file=sys.stderr)
        return 1
    if int(store.get("chunk_count", 0)) == 0:
        print("FAIL retrieval store has zero chunks", file=sys.stderr)
        return 1
    print("PASS retrieval health")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
