import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RELEASE_INGEST_PATH = REPO_ROOT / "knowledge" / "refresh" / "ingest_releases.py"

spec = importlib.util.spec_from_file_location("release_ingest", RELEASE_INGEST_PATH)
release_ingest = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(release_ingest)


def test_release_item_classification_extracts_metadata() -> None:
    source = {
        "id": "oci-release-notes-all-services",
        "title": "OCI Release Notes",
        "url": "https://docs.oracle.com/example",
        "source_type": "oci_release_notes",
        "trust_level": "official",
    }
    item = (
        "Object Storage Supports Amazon S3 Virtual-Hosted Style URLs. "
        "Services: Object Storage. Release Date: February 10, 2026. "
        "This release can affect migration compatibility and application architecture."
    )

    release = release_ingest.classify_release_item(item, source, 1, "2026-05-14T00:00:00+00:00")

    assert release["service"] == "Object Storage"
    assert release["service_domain"] == "storage"
    assert release["release_date"] == "February 10, 2026"
    assert "migration" in release["impact_tags"]
    assert release["trust_level"] == "official"


def test_split_release_items_uses_fallback_text() -> None:
    text = (
        "Object Storage Supports Amazon S3 Virtual-Hosted Style URLs. Services: Object Storage. "
        "Release Date: February 10, 2026. This affects compatibility. "
        "Secrets in Vault is now Secret Management Service. Services: Secret Management. "
        "Release Date: January 22, 2026. This affects security architecture."
    )

    items = release_ingest.split_release_items(text, max_items=5)

    assert len(items) >= 2
    assert any("Object Storage" in item for item in items)
    assert any("Secret Management" in item for item in items)
