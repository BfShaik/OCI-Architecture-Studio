import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RELEASE_INTELLIGENCE_PATH = REPO_ROOT / "knowledge" / "refresh" / "release_intelligence.py"

spec = importlib.util.spec_from_file_location("release_intelligence", RELEASE_INTELLIGENCE_PATH)
release_intelligence = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(release_intelligence)


def test_release_intelligence_classifies_change_categories_and_risk() -> None:
    release = release_intelligence.normalize_release_item(
        {
            "id": "release::1",
            "title": "Object Storage deprecates legacy S3 compatibility behavior",
            "service": "Object Storage",
            "service_domain": "storage",
            "summary": "Deprecated endpoint behavior can affect migration compatibility and application architecture.",
            "impact_tags": ["migration"],
        }
    )

    assert "deprecated-behavior" in release["change_categories"]
    assert "compatibility-risk" in release["change_categories"]
    assert release["severity"] == "high"
    assert release["service_mapping_review_required"] is True
    assert release["regression_required"] is True


def test_release_impact_analysis_maps_sources_chunks_and_eval_cases(tmp_path: Path) -> None:
    cases = tmp_path / "cases.jsonl"
    cases.write_text(
        json.dumps(
            {
                "id": "migration-object-storage",
                "prompt": "Migrate S3 object storage compatibility to OCI Object Storage.",
                "expected_intent": "migration",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    knowledge_index = {
        "chunks": [
            {
                "id": "oci-object-storage-overview::1",
                "source_id": "oci-object-storage-overview",
                "metadata": {"service": "Object Storage", "service_domain": "storage"},
            }
        ]
    }
    release = release_intelligence.normalize_release_item(
        {
            "id": "release::1",
            "title": "Object Storage supports Amazon S3 virtual-hosted style URLs",
            "service": "Object Storage",
            "services": ["Object Storage"],
            "service_domain": "storage",
            "summary": "This compatibility update affects S3 migration guidance.",
            "impact_tags": ["migration"],
        }
    )

    impact = release_intelligence.impact_analysis(
        releases=[release],
        knowledge_index=knowledge_index,
        eval_case_paths=[cases],
        policy={},
    )

    assert "oci-object-storage-overview" in impact["affected_source_ids"]
    assert "oci-object-storage-overview::1" in impact["affected_chunk_ids"]
    assert "migration-object-storage" in impact["impacted_eval_cases"]
    assert "targeted_regression" in impact["refresh_actions"]


def test_release_overlay_marks_affected_chunks_current() -> None:
    knowledge_index = {
        "chunks": [
            {
                "id": "oci-object-storage-overview::1",
                "source_id": "oci-object-storage-overview",
                "metadata": {"service": "Object Storage"},
            }
        ]
    }
    release = {"id": "release::1", "title": "Object Storage update", "change_categories": ["migration-relevance"], "release_date": "May 1, 2026"}
    impact = {
        "affected_source_ids": ["oci-object-storage-overview"],
        "affected_chunk_ids": ["oci-object-storage-overview::1"],
    }

    updated = release_intelligence.apply_release_overlay(knowledge_index, [release], impact)
    metadata = updated["chunks"][0]["metadata"]

    assert metadata["release_impacted"] is True
    assert metadata["release_item_ids"] == ["release::1"]
    assert metadata["current_knowledge"] is True
    assert metadata["valid_to"] is None
