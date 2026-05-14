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
