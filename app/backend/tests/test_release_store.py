import json

from oci_arch_studio_backend.services.intents import Intent
from oci_arch_studio_backend.services.releases import ReleaseSnapshotStore


def test_release_store_returns_freshness_note_for_matching_release(tmp_path) -> None:
    snapshot = tmp_path / "oci-release-snapshot.json"
    snapshot.write_text(
        json.dumps(
            {
                "releases": [
                    {
                        "title": "Object Storage Supports Amazon S3 Virtual-Hosted Style URLs",
                        "service": "Object Storage",
                        "service_domain": "storage",
                        "impact_tags": ["migration", "architecture"],
                        "impact_level": "review",
                        "source_url": "https://docs.oracle.com/example",
                        "release_date": "February 10, 2026",
                        "summary": "Object Storage compatibility update for S3 URL style.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    store = ReleaseSnapshotStore(snapshot)

    note = store.freshness_note(Intent.RELEASE_AWARENESS, "latest Object Storage update")

    assert note is not None
    assert "Object Storage" in note
    assert "release items" in note


def test_release_store_returns_impact_and_temporal_context(tmp_path) -> None:
    snapshot = tmp_path / "oci-release-snapshot.json"
    snapshot.write_text(
        json.dumps(
            {
                "generated_at": "2026-05-15T00:00:00+00:00",
                "releases": [
                    {
                        "title": "Secrets in Vault is now Secret Management Service",
                        "service": "Secret Management",
                        "service_domain": "security",
                        "impact_tags": ["security"],
                        "impact_level": "review",
                        "source_url": "https://docs.oracle.com/example",
                        "release_date": "January 22, 2026",
                        "summary": "Secrets in Vault is now Secret Management Service.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    store = ReleaseSnapshotStore(snapshot)
    impact = store.impact_summary("Does the latest Vault update change my security architecture?")
    temporal = store.temporal_context(knowledge_snapshot_path=tmp_path / "oci-rag-index.json")

    assert impact.snapshot_generated_at == "2026-05-15T00:00:00+00:00"
    assert impact.architecture_affecting_services == ["Secret Management"]
    assert "security" in impact.impact_categories
    assert temporal.knowledge_mode == "current_snapshot_with_release_overlay"
    assert temporal.current_knowledge_snapshot.endswith("oci-rag-index.json")
