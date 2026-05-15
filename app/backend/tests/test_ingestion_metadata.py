import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
INGEST_PATH = REPO_ROOT / "knowledge" / "ingestion" / "ingest.py"

spec = importlib.util.spec_from_file_location("knowledge_ingest", INGEST_PATH)
ingest = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(ingest)


def test_cleanup_chunk_text_removes_common_oracle_boilerplate() -> None:
    text = (
        "JavaScript must be enabled to correctly display this content "
        "OCI Load Balancer distributes traffic. Previous Next Copyright © Oracle"
    )

    cleaned = ingest.cleanup_chunk_text(text)

    assert "JavaScript must be enabled" not in cleaned
    assert "Previous Next" not in cleaned
    assert "Copyright" not in cleaned
    assert "OCI Load Balancer distributes traffic" in cleaned


def test_infer_source_metadata_adds_citation_ready_fields() -> None:
    source = {
        "id": "oci-load-balancer-overview",
        "title": "OCI Load Balancer Overview",
        "url": "https://docs.oracle.com/example",
        "source_type": "oci_service_doc",
    }

    metadata = ingest.infer_source_metadata(source, "2026-05-14T00:00:00+00:00", "fetched")

    assert metadata["source_url"] == source["url"]
    assert metadata["service"] == "Load Balancer"
    assert metadata["service_domain"] == "networking"
    assert metadata["service_category"] == "networking"
    assert metadata["category"] == "networking"
    assert "webapp" in metadata["workload_types"]
    assert "ecommerce" in metadata["domain_tags"]
    assert "architecture" in metadata["intent_tags"]
    assert metadata["trust_level"] == "official"
    assert metadata["freshness_score"] == 0.9
    assert metadata["metadata_schema_version"] == ingest.METADATA_SCHEMA_VERSION


def test_infer_source_metadata_accepts_registry_overrides() -> None:
    source = {
        "id": "oci-custom-ai-source",
        "title": "OCI Custom AI Source",
        "url": "https://docs.oracle.com/example",
        "source_type": "oci_service_doc",
        "service": "OCI Data Science",
        "service_domain": "ai_ml",
        "source_category": "ai",
        "workload_types": ["ai-inference"],
        "domain_tags": ["AI/ML"],
        "intent_tags": ["ai_ml", "architecture"],
        "architecture_patterns": ["model-serving"],
        "release_tags": ["model-serving"],
    }

    metadata = ingest.infer_source_metadata(source, "2026-05-14T00:00:00+00:00", "fallback")

    assert metadata["service"] == "OCI Data Science"
    assert metadata["service_domain"] == "ai_ml"
    assert metadata["source_category"] == "ai"
    assert metadata["release_tags"] == ["model-serving"]
    assert "ai-inference" in metadata["workload_types"]


def test_chunk_content_hash_is_stable() -> None:
    text = "OCI Object Storage supports durable architecture artifacts."

    assert ingest.chunk_content_hash(text) == ingest.chunk_content_hash(text)
    assert ingest.chunk_content_hash(text) != ingest.chunk_content_hash(text + " Updated.")


def test_select_sources_rejects_unknown_source_ids() -> None:
    sources = [{"id": "oci-object-storage-overview"}]

    selected = ingest.select_sources(sources, ["oci-object-storage-overview"])

    assert selected == sources


def test_merge_with_existing_index_replaces_only_refreshed_sources(tmp_path: Path) -> None:
    existing = {
        "generated_at": "old",
        "chunks": [
            {"id": "oci-object-storage-overview::1", "source_id": "oci-object-storage-overview"},
            {"id": "oci-load-balancer-overview::1", "source_id": "oci-load-balancer-overview"},
        ],
        "chunk_count": 2,
    }
    existing_path = tmp_path / "index.json"
    existing_path.write_text(__import__("json").dumps(existing), encoding="utf-8")
    refreshed = {
        "generated_at": "new",
        "chunks": [
            {"id": "oci-object-storage-overview::1", "source_id": "oci-object-storage-overview"},
            {"id": "oci-object-storage-overview::2", "source_id": "oci-object-storage-overview"},
        ],
        "chunk_count": 2,
    }

    merged = ingest.merge_with_existing_index(
        refreshed,
        existing_path,
        ["oci-object-storage-overview"],
    )

    assert merged["chunk_count"] == 3
    assert any(chunk["source_id"] == "oci-load-balancer-overview" for chunk in merged["chunks"])
    assert sum(chunk["source_id"] == "oci-object-storage-overview" for chunk in merged["chunks"]) == 2
