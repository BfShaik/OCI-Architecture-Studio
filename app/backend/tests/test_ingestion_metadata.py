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
    assert "architecture" in metadata["intent_tags"]
    assert metadata["trust_level"] == "official"
    assert metadata["freshness_score"] == 0.9
