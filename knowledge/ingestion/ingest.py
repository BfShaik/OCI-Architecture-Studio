from __future__ import annotations

import argparse
import hashlib
import json
import re
import ssl
import sys
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_SRC = REPO_ROOT / "app" / "backend" / "src"
sys.path.append(str(BACKEND_SRC))

from oci_arch_studio_backend.services.embeddings import (  # noqa: E402
    LocalHashingEmbedder,
    OciGenerativeAiEmbedder,
    OciGenerativeAiEmbeddingConfig,
)


BOILERPLATE_PATTERNS = (
    r"JavaScript must be enabled to correctly display this content",
    r"Previous\s+Next",
    r"Was this article helpful\?.*?$",
    r"About Oracle.*?$",
    r"Copyright\s+©.*?$",
    r"Oracle Account\s+Manage your account.*?$",
)

SERVICE_METADATA: dict[str, dict[str, object]] = {
    "architecture-center": {
        "service": "Architecture Center",
        "service_domain": "architecture",
        "intent_tags": ["architecture", "general"],
        "architecture_patterns": ["reference-architecture", "well-architected"],
    },
    "well-architected": {
        "service": "Well-Architected Framework",
        "service_domain": "architecture",
        "intent_tags": ["architecture", "cost", "security", "dr", "general"],
        "architecture_patterns": ["well-architected", "operational-excellence"],
    },
    "vcn": {
        "service": "Virtual Cloud Network",
        "service_domain": "networking",
        "intent_tags": ["architecture", "security", "dr", "general"],
        "architecture_patterns": ["network-isolation", "private-subnets"],
    },
    "load-balancer": {
        "service": "Load Balancer",
        "service_domain": "networking",
        "intent_tags": ["architecture", "dr", "general"],
        "architecture_patterns": ["public-ingress", "high-availability"],
    },
    "object-storage": {
        "service": "Object Storage",
        "service_domain": "storage",
        "intent_tags": ["architecture", "cost", "dr", "general"],
        "architecture_patterns": ["static-assets", "backup-storage", "lifecycle-management"],
    },
    "cdn": {
        "service": "CDN",
        "service_domain": "edge",
        "intent_tags": ["architecture", "cost", "security", "general"],
        "architecture_patterns": ["edge-delivery", "origin-offload"],
    },
    "compute": {
        "service": "Compute",
        "service_domain": "compute",
        "intent_tags": ["architecture", "cost", "general"],
        "architecture_patterns": ["application-tier", "autoscaling"],
    },
    "iam": {
        "service": "Identity and Access Management",
        "service_domain": "security",
        "intent_tags": ["security", "architecture", "migration", "general"],
        "architecture_patterns": ["least-privilege", "compartment-strategy", "access-governance"],
    },
    "network-security-groups": {
        "service": "Network Security Groups",
        "service_domain": "networking",
        "intent_tags": ["security", "architecture", "dr", "general"],
        "architecture_patterns": ["network-isolation", "east-west-controls"],
    },
    "database-migration": {
        "service": "Database Migration",
        "service_domain": "database",
        "intent_tags": ["migration", "general"],
        "architecture_patterns": ["migration-waves", "cutover"],
    },
    "autonomous-database": {
        "service": "Autonomous Database",
        "service_domain": "database",
        "intent_tags": ["architecture", "migration", "dr", "cost", "general"],
        "architecture_patterns": ["managed-database", "data-tier", "backup-recovery"],
    },
    "database": {
        "service": "Database Services",
        "service_domain": "database",
        "intent_tags": ["architecture", "migration", "dr", "cost", "general"],
        "architecture_patterns": ["data-tier", "backup-recovery"],
    },
    "kubernetes": {
        "service": "OCI Kubernetes Engine",
        "service_domain": "containers",
        "intent_tags": ["architecture", "migration", "general"],
        "architecture_patterns": ["container-platform", "node-pools"],
    },
    "full-stack-dr": {
        "service": "Full Stack Disaster Recovery",
        "service_domain": "resilience",
        "intent_tags": ["dr", "architecture", "general"],
        "architecture_patterns": ["disaster-recovery", "failover-runbook"],
    },
    "cost-management": {
        "service": "Cost Management",
        "service_domain": "cost",
        "intent_tags": ["cost", "general"],
        "architecture_patterns": ["budgets", "tagging", "rightsizing"],
    },
    "vault": {
        "service": "Vault",
        "service_domain": "security",
        "intent_tags": ["security", "architecture", "dr", "general"],
        "architecture_patterns": ["key-management", "secrets-management", "encryption"],
    },
    "logging": {
        "service": "Logging",
        "service_domain": "observability",
        "intent_tags": ["architecture", "security", "dr", "general"],
        "architecture_patterns": ["auditability", "operational-visibility"],
    },
    "monitoring": {
        "service": "Monitoring",
        "service_domain": "observability",
        "intent_tags": ["architecture", "cost", "dr", "general"],
        "architecture_patterns": ["operational-visibility", "alarms", "slo-monitoring"],
    },
    "cloud-guard": {
        "service": "Cloud Guard",
        "service_domain": "security",
        "intent_tags": ["security", "architecture", "general"],
        "architecture_patterns": ["posture-management", "threat-detection"],
    },
    "waf": {
        "service": "Web Application Firewall",
        "service_domain": "edge",
        "intent_tags": ["security", "architecture", "general"],
        "architecture_patterns": ["edge-protection", "application-security"],
    },
    "security": {
        "service": "Security Services",
        "service_domain": "security",
        "intent_tags": ["security", "dr", "architecture", "general"],
        "architecture_patterns": ["least-privilege", "auditability"],
    },
}


class HtmlTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            cleaned = " ".join(data.split())
            if cleaned:
                self.parts.append(cleaned)

    def text(self) -> str:
        return normalize_text(" ".join(self.parts))


def normalize_text(text: str) -> str:
    for pattern in BOILERPLATE_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def cleanup_chunk_text(text: str) -> str:
    text = normalize_text(text)
    text = re.sub(r"\b(Contents|Search|Menu|Breadcrumb)\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ssl_context() -> ssl.SSLContext | None:
    try:
        import certifi
    except ImportError:
        return None

    return ssl.create_default_context(cafile=certifi.where())


def fetch_text(url: str, timeout: int) -> str:
    request = Request(
        url,
        headers={"User-Agent": "OCI-Architecture-Studio-Ingestion/0.1"},
    )
    with urlopen(request, timeout=timeout, context=ssl_context()) as response:
        html = response.read().decode("utf-8", errors="ignore")

    parser = HtmlTextExtractor()
    parser.feed(html)
    return parser.text()


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    words = text.split()
    chunks: list[str] = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if chunk:
            chunks.append(chunk)
        if end == len(words):
            break
        start = end - chunk_overlap

    return chunks


def load_registry(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return payload["sources"]


def select_sources(
    sources: list[dict[str, str]],
    source_ids: list[str] | None,
) -> list[dict[str, str]]:
    if not source_ids:
        return sources
    requested = set(source_ids)
    selected = [source for source in sources if source["id"] in requested]
    missing = sorted(requested - {source["id"] for source in selected})
    if missing:
        raise ValueError(f"Unknown source id(s): {', '.join(missing)}")
    return selected


def infer_source_metadata(source: dict[str, str], fetched_timestamp: str, fetch_status: str) -> dict[str, object]:
    source_id = source["id"].replace("oci-", "")
    matched: dict[str, object] | None = None
    for key, metadata in SERVICE_METADATA.items():
        if key in source_id:
            matched = metadata
            break

    metadata = dict(matched or {})
    metadata.setdefault("service", source["title"].replace("OCI ", "").replace(" Overview", ""))
    metadata.setdefault("service_domain", "general")
    metadata.setdefault("intent_tags", ["general"])
    metadata.setdefault("architecture_patterns", [])
    metadata.update(
        {
            "source_url": source["url"],
            "fetched_timestamp": fetched_timestamp,
            "freshness_score": 0.9 if fetch_status == "fetched" else 0.65,
            "trust_level": source.get("trust_level", "official"),
            "release_version": source.get("release_version", "unknown"),
        }
    )
    return metadata


def build_embedder(args: argparse.Namespace):
    if args.embedding_provider == "oci_genai":
        if not args.oci_genai_compartment_id or not args.oci_genai_embedding_model_id:
            raise ValueError(
                "--oci-genai-compartment-id and --oci-genai-embedding-model-id are required "
                "when --embedding-provider=oci_genai"
            )
        return OciGenerativeAiEmbedder(
            OciGenerativeAiEmbeddingConfig(
                region=args.oci_region,
                profile=args.oci_profile,
                auth_mode=args.oci_auth_mode,
                compartment_id=args.oci_genai_compartment_id,
                model_id=args.oci_genai_embedding_model_id,
                endpoint=args.oci_genai_endpoint,
            )
        )
    return LocalHashingEmbedder(dimensions=args.dimensions)


def build_index(args: argparse.Namespace) -> dict[str, object]:
    embedder = build_embedder(args)
    all_sources = load_registry(args.registry)
    sources = select_sources(all_sources, args.source_ids)
    chunks: list[dict[str, object]] = []
    generated_at = datetime.now(UTC).isoformat()

    for source in sources:
        fallback_text = source.get("fallback_text", "")
        text = fallback_text
        fetch_status = "fallback"

        if not args.no_fetch:
            try:
                fetched = fetch_text(source["url"], timeout=args.timeout)
                if len(fetched.split()) >= args.min_fetched_words:
                    text = f"{fallback_text} {fetched[: args.max_source_chars]}"
                    fetch_status = "fetched"
            except (TimeoutError, URLError, OSError):
                fetch_status = "fallback"

        source_metadata = infer_source_metadata(source, generated_at, fetch_status)
        for index, chunk in enumerate(
            chunk_text(text, chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap),
            start=1,
        ):
            clean_chunk = cleanup_chunk_text(chunk)
            chunks.append(
                {
                    "id": f"{source['id']}::{index}",
                    "source_id": source["id"],
                    "title": source["title"],
                    "url": source["url"],
                    "source_type": source["source_type"],
                    "text": clean_chunk,
                    "embedding": embedder.embed(clean_chunk),
                    "metadata": {
                        "chunk_index": index,
                        "chunk_word_count": len(clean_chunk.split()),
                        "content_hash": chunk_content_hash(clean_chunk),
                        "fetch_status": fetch_status,
                        "vector_ready": True,
                        **source_metadata,
                    },
                }
            )

    refreshed_source_ids = [source["id"] for source in sources]
    return {
        "generated_at": generated_at,
        "embedding_model": embedder.model_name,
        "embedding_provider": args.embedding_provider,
        "dimensions": args.dimensions if args.embedding_provider == "local" else None,
        "metadata_schema_version": "2026-05-oci-native-v1",
        "vector_migration": {
            "local_json_compatible": True,
            "oci_object_storage_manifest_ready": True,
            "oracle_ai_vector_search_schema_ready": True,
            "oracle_ai_vector_search_read_enabled": False,
        },
        "source_count": len(all_sources),
        "refreshed_source_ids": refreshed_source_ids,
        "selective_refresh": bool(args.source_ids),
        "chunk_count": len(chunks),
        "chunks": chunks,
    }


def merge_with_existing_index(
    new_index: dict[str, object],
    existing_index_path: Path | None,
    refreshed_source_ids: list[str],
) -> dict[str, object]:
    if not existing_index_path or not existing_index_path.exists() or not refreshed_source_ids:
        return new_index

    with existing_index_path.open("r", encoding="utf-8") as file:
        existing_index = json.load(file)

    refreshed = set(refreshed_source_ids)
    retained_chunks = [
        chunk
        for chunk in existing_index.get("chunks", [])
        if chunk.get("source_id") not in refreshed
    ]
    merged_chunks = [*retained_chunks, *new_index.get("chunks", [])]
    merged_index = dict(existing_index)
    merged_index.update(
        {
            key: value
            for key, value in new_index.items()
            if key not in {"chunks", "chunk_count"}
        }
    )
    merged_index["chunks"] = merged_chunks
    merged_index["chunk_count"] = len(merged_chunks)
    merged_index["selective_refresh"] = True
    merged_index["refreshed_source_ids"] = refreshed_source_ids
    return merged_index


def upload_index_to_object_storage(index: dict[str, object], args: argparse.Namespace) -> None:
    if not args.oci_upload_bucket:
        return
    if not args.oci_namespace:
        raise ValueError("--oci-namespace is required when --oci-upload-bucket is set")

    try:
        import oci
    except ImportError as exc:
        raise RuntimeError("OCI SDK is required for Object Storage upload.") from exc

    if args.oci_auth_mode == "instance_principal":
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        client_config = {"region": args.oci_region} if args.oci_region else {}
        object_storage = oci.object_storage.ObjectStorageClient(client_config, signer=signer)
    elif args.oci_auth_mode == "resource_principal":
        signer = oci.auth.signers.get_resource_principals_signer()
        client_config = {"region": args.oci_region} if args.oci_region else {}
        object_storage = oci.object_storage.ObjectStorageClient(client_config, signer=signer)
    else:
        client_config = oci.config.from_file(profile_name=args.oci_profile)
        if args.oci_region:
            client_config["region"] = args.oci_region
        object_storage = oci.object_storage.ObjectStorageClient(client_config)

    object_storage.put_object(
        namespace_name=args.oci_namespace,
        bucket_name=args.oci_upload_bucket,
        object_name=args.oci_upload_object,
        put_object_body=json.dumps(index, indent=2).encode("utf-8"),
    )
    print(f"Uploaded vector manifest to oci://{args.oci_upload_bucket}/{args.oci_upload_object}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build local OCI RAG index.")
    parser.add_argument(
        "--registry",
        type=Path,
        default=REPO_ROOT / "knowledge" / "source_registry.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "knowledge" / "snapshots" / "oci-rag-index.json",
    )
    parser.add_argument("--dimensions", type=int, default=256)
    parser.add_argument("--embedding-provider", choices=("local", "oci_genai"), default="local")
    parser.add_argument("--oci-region")
    parser.add_argument("--oci-profile", default="DEFAULT")
    parser.add_argument("--oci-auth-mode", choices=("config_file", "instance_principal", "resource_principal"), default="config_file")
    parser.add_argument("--oci-genai-compartment-id")
    parser.add_argument("--oci-genai-embedding-model-id")
    parser.add_argument("--oci-genai-endpoint")
    parser.add_argument("--oci-namespace")
    parser.add_argument("--oci-upload-bucket")
    parser.add_argument("--oci-upload-object", default="knowledge/oci-rag-index.json")
    parser.add_argument("--chunk-size", type=int, default=180)
    parser.add_argument("--chunk-overlap", type=int, default=30)
    parser.add_argument("--max-source-chars", type=int, default=14000)
    parser.add_argument("--min-fetched-words", type=int, default=120)
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument(
        "--source-id",
        dest="source_ids",
        action="append",
        default=None,
        help="Refresh only this source id. Can be provided multiple times.",
    )
    parser.add_argument(
        "--existing-index",
        type=Path,
        default=None,
        help="Existing index to merge with when --source-id is used.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    index = build_index(args)
    index = merge_with_existing_index(
        index,
        args.existing_index,
        [str(source_id) for source_id in index.get("refreshed_source_ids", [])],
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as file:
        json.dump(index, file, indent=2)
        file.write("\n")
    upload_index_to_object_storage(index, args)

    print(
        f"Wrote {index['chunk_count']} chunks from {index['source_count']} sources "
        f"to {args.output}"
    )


if __name__ == "__main__":
    main()
