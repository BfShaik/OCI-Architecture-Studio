import importlib.util
import json
from argparse import Namespace
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


def refresh_args(tmp_path: Path) -> Namespace:
    knowledge_index = tmp_path / "snapshots" / "oci-rag-index.json"
    release_snapshot = tmp_path / "snapshots" / "oci-release-snapshot.json"
    policy = tmp_path / "refresh_policy.json"
    source_registry = tmp_path / "source_registry.json"
    release_registry = tmp_path / "release_registry.json"
    knowledge_index.parent.mkdir(parents=True)
    knowledge_index.write_text(
        json.dumps(
            {
                "generated_at": "2026-05-01T00:00:00+00:00",
                "embedding_model": "local-hashing-v1",
                "embedding_provider": "local",
                "metadata_schema_version": "test-v1",
                "chunk_count": 1,
                "chunks": [{"id": "old::1", "source_id": "old", "text": "old"}],
            }
        ),
        encoding="utf-8",
    )
    release_snapshot.write_text(
        json.dumps(
            {
                "generated_at": "2026-05-01T00:00:00+00:00",
                "releases": [
                    {
                        "source_id": "release-source",
                        "title": "Old update",
                        "release_date": "May 1, 2026",
                        "service": "Object Storage",
                        "summary": "Old update.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    policy.write_text(
        json.dumps(
            {
                "policy_version": "test",
                "important_impact_levels": ["review"],
                "impact_to_source_ids": {"security": ["oci-security-services-overview"]},
                "service_to_source_ids": {"Object Storage": ["oci-object-storage-overview"]},
                "cadence": {"release_watch": "hourly"},
            }
        ),
        encoding="utf-8",
    )
    source_registry.write_text(json.dumps({"sources": [{"id": "oci-object-storage-overview"}]}), encoding="utf-8")
    release_registry.write_text(json.dumps({"sources": []}), encoding="utf-8")
    return Namespace(
        mode="release-watch",
        policy=policy,
        source_registry=source_registry,
        release_registry=release_registry,
        knowledge_index=knowledge_index,
        release_snapshot=release_snapshot,
        report_dir=tmp_path / "reports",
        dimensions=8,
        embedding_provider="local",
        oci_region=None,
        oci_profile="DEFAULT",
        oci_auth_mode="config_file",
        oci_genai_compartment_id=None,
        oci_genai_embedding_model_id=None,
        oci_genai_endpoint=None,
        oci_namespace=None,
        oci_upload_bucket=None,
        oci_upload_object="knowledge/oci-rag-index.json",
        chunk_size=180,
        chunk_overlap=30,
        max_source_chars=14000,
        min_fetched_words=120,
        max_items_per_source=12,
        timeout=8,
        no_fetch=True,
        force=False,
        skip_gates=False,
        quick_gates=True,
        rollback_on_failure=True,
        rollback_latest=False,
    )


def test_refresh_promotes_candidate_only_after_gates_pass(tmp_path: Path, monkeypatch) -> None:
    args = refresh_args(tmp_path)

    def fake_release_snapshot(_args):
        return {
            "generated_at": "2026-05-02T00:00:00+00:00",
            "releases": [
                {
                    "id": "new-release",
                    "source_id": "release-source",
                    "title": "New Object Storage security update",
                    "release_date": "May 2, 2026",
                    "service": "Object Storage",
                    "services": ["Object Storage"],
                    "impact_tags": ["security"],
                    "impact_level": "review",
                    "summary": "New Object Storage security update.",
                }
            ],
        }

    def fake_knowledge_index(_args, source_ids, existing_index_path=None):
        assert existing_index_path == args.knowledge_index
        return {
            "generated_at": "2026-05-02T00:00:00+00:00",
            "embedding_model": "local-hashing-v1",
            "embedding_provider": "local",
            "metadata_schema_version": "test-v2",
            "refreshed_source_ids": source_ids,
            "chunk_count": 1,
            "chunks": [{"id": "new::1", "source_id": source_ids[0], "text": "new"}],
        }

    monkeypatch.setattr(refresh_policy, "build_release_snapshot", fake_release_snapshot)
    monkeypatch.setattr(refresh_policy, "build_selective_knowledge_index", fake_knowledge_index)
    monkeypatch.setattr(
        refresh_policy,
        "run_post_refresh_gates",
        lambda *_args: [{"command": "test gate", "returncode": 0, "passed": True}],
    )

    report = refresh_policy.execute_refresh_policy(args)

    promoted_index = json.loads(args.knowledge_index.read_text(encoding="utf-8"))
    status = json.loads((args.report_dir / "knowledge-refresh-status.json").read_text(encoding="utf-8"))
    assert report["status"] == "promoted"
    assert report["promoted"] is True
    assert promoted_index["chunks"][0]["id"] == "new::1"
    assert status["current_promoted_snapshot"]["status"] == "promoted"
    assert status["current_promoted_snapshot"]["lineage"]["knowledge_snapshot_version"].startswith("knowledge-")


def test_failed_gates_do_not_overwrite_authoritative_snapshots(tmp_path: Path, monkeypatch) -> None:
    args = refresh_args(tmp_path)
    original_index = args.knowledge_index.read_text(encoding="utf-8")

    monkeypatch.setattr(
        refresh_policy,
        "build_release_snapshot",
        lambda _args: {
            "generated_at": "2026-05-02T00:00:00+00:00",
            "releases": [
                {
                    "id": "new-release",
                    "source_id": "release-source",
                    "title": "New Object Storage security update",
                    "release_date": "May 2, 2026",
                    "service": "Object Storage",
                    "services": ["Object Storage"],
                    "impact_tags": ["security"],
                    "impact_level": "review",
                    "summary": "New Object Storage security update.",
                }
            ],
        },
    )
    monkeypatch.setattr(
        refresh_policy,
        "build_selective_knowledge_index",
        lambda _args, source_ids, existing_index_path=None: {
            "generated_at": "2026-05-02T00:00:00+00:00",
            "embedding_model": "local-hashing-v1",
            "embedding_provider": "local",
            "metadata_schema_version": "test-v2",
            "refreshed_source_ids": source_ids,
            "chunk_count": 1,
            "chunks": [{"id": "new::1", "source_id": source_ids[0], "text": "new"}],
        },
    )
    monkeypatch.setattr(
        refresh_policy,
        "run_post_refresh_gates",
        lambda *_args: [{"command": "test gate", "returncode": 1, "passed": False}],
    )

    report = refresh_policy.execute_refresh_policy(args)

    assert report["status"] == "failed_gate"
    assert report["promoted"] is False
    assert args.knowledge_index.read_text(encoding="utf-8") == original_index


def test_rollback_latest_restores_previous_promoted_snapshot(tmp_path: Path, monkeypatch) -> None:
    args = refresh_args(tmp_path)
    original_index = args.knowledge_index.read_text(encoding="utf-8")
    monkeypatch.setattr(
        refresh_policy,
        "build_release_snapshot",
        lambda _args: {
            "generated_at": "2026-05-02T00:00:00+00:00",
            "releases": [
                {
                    "id": "new-release",
                    "source_id": "release-source",
                    "title": "New Object Storage security update",
                    "release_date": "May 2, 2026",
                    "service": "Object Storage",
                    "services": ["Object Storage"],
                    "impact_tags": ["security"],
                    "impact_level": "review",
                    "summary": "New Object Storage security update.",
                }
            ],
        },
    )
    monkeypatch.setattr(
        refresh_policy,
        "build_selective_knowledge_index",
        lambda _args, source_ids, existing_index_path=None: {
            "generated_at": "2026-05-02T00:00:00+00:00",
            "embedding_model": "local-hashing-v1",
            "embedding_provider": "local",
            "metadata_schema_version": "test-v2",
            "refreshed_source_ids": source_ids,
            "chunk_count": 1,
            "chunks": [{"id": "new::1", "source_id": source_ids[0], "text": "new"}],
        },
    )
    monkeypatch.setattr(
        refresh_policy,
        "run_post_refresh_gates",
        lambda *_args: [{"command": "test gate", "returncode": 0, "passed": True}],
    )
    refresh_policy.execute_refresh_policy(args)

    rollback = refresh_policy.rollback_latest(args)

    assert rollback["passed"] is True
    assert args.knowledge_index.read_text(encoding="utf-8") == original_index
