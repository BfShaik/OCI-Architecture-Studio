import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
REFRESH_POLICY_PATH = REPO_ROOT / "knowledge" / "refresh" / "refresh_policy.py"

spec = importlib.util.spec_from_file_location("refresh_policy", REFRESH_POLICY_PATH)
refresh_policy = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(refresh_policy)


def test_new_release_items_uses_stable_content_key() -> None:
    previous = {
        "releases": [
            {
                "source_id": "oci-release-notes-all-services",
                "title": "Existing update",
                "release_date": "May 1, 2026",
                "service": "Object Storage",
                "summary": "Existing update summary.",
                "ingested_timestamp": "old",
            }
        ]
    }
    current = {
        "releases": [
            {
                "source_id": "oci-release-notes-all-services",
                "title": "Existing update",
                "release_date": "May 1, 2026",
                "service": "Object Storage",
                "summary": "Existing update summary.",
                "ingested_timestamp": "new",
            },
            {
                "source_id": "oci-release-notes-all-services",
                "title": "New security update",
                "release_date": "May 2, 2026",
                "service": "Secret Management",
                "summary": "New security update summary.",
            },
        ]
    }

    changed = refresh_policy.new_release_items(previous, current)

    assert len(changed) == 1
    assert changed[0]["title"] == "New security update"


def test_affected_source_ids_maps_release_service_and_impact() -> None:
    policy = {
        "impact_to_source_ids": {
            "security": ["oci-security-services-overview"],
            "migration": ["oci-database-migration-overview"],
        },
        "service_to_source_ids": {
            "Object Storage": ["oci-object-storage-overview"],
        },
        "important_impact_levels": ["review"],
    }
    releases = [
        {
            "service": "Object Storage",
            "services": ["Object Storage"],
            "impact_tags": ["migration", "security"],
            "impact_level": "review",
        }
    ]

    source_ids = refresh_policy.affected_source_ids(releases, policy)

    assert source_ids == [
        "oci-database-migration-overview",
        "oci-object-storage-overview",
        "oci-security-services-overview",
    ]
