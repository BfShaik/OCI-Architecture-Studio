import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CORPUS_HEALTH_PATH = REPO_ROOT / "knowledge" / "ingestion" / "corpus_health.py"

spec = importlib.util.spec_from_file_location("corpus_health", CORPUS_HEALTH_PATH)
corpus_health = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(corpus_health)


def test_corpus_health_detects_complete_index() -> None:
    index = {
        "chunks": [
            {
                "id": "architecture::1",
                "source_id": "architecture",
                "embedding": [1.0, 0.0],
                "metadata": _metadata("Architecture Center", "architecture", "architecture"),
            },
            {
                "id": "database::1",
                "source_id": "database",
                "embedding": [0.9, 0.1],
                "metadata": _metadata("Database Services", "database", "migration"),
            },
            {
                "id": "security::1",
                "source_id": "security",
                "embedding": [0.8, 0.2],
                "metadata": _metadata("Vault", "security", "security"),
            },
            {
                "id": "observability::1",
                "source_id": "observability",
                "embedding": [0.7, 0.3],
                "metadata": _metadata("Monitoring", "observability", "observability"),
            },
            {
                "id": "cost::1",
                "source_id": "cost",
                "embedding": [0.6, 0.4],
                "metadata": _metadata("Cost Management", "cost", "cost-optimization"),
            },
            {
                "id": "resilience::1",
                "source_id": "resilience",
                "embedding": [0.5, 0.5],
                "metadata": _metadata("Full Stack Disaster Recovery", "resilience", "resilience"),
            },
            {
                "id": "networking::1",
                "source_id": "networking",
                "embedding": [0.4, 0.6],
                "metadata": _metadata("Virtual Cloud Network", "networking", "networking"),
            },
        ]
    }

    report = corpus_health.corpus_health(index, min_chunks=7)

    assert report["status"] == "passed"
    assert report["metadata_completeness"] == 1.0


def test_corpus_health_flags_empty_embeddings_and_missing_tags() -> None:
    index = {
        "chunks": [
            {
                "id": "bad::1",
                "source_id": "bad",
                "embedding": [],
                "metadata": {"content_hash": "abc"},
            }
        ]
    }

    report = corpus_health.corpus_health(index, min_chunks=2)

    assert report["status"] == "failed"
    assert report["missing_service_tags"] == ["bad::1"]
    assert report["empty_embeddings"] == ["bad::1"]


def _metadata(service: str, domain: str, category: str) -> dict[str, object]:
    return {
        "service": service,
        "service_domain": domain,
        "service_category": domain,
        "category": category,
        "intent_tags": ["architecture", "migration", "dr", "cost", "security", "observability"],
        "architecture_patterns": ["reference-architecture"],
        "workload_types": ["enterprise-app"],
        "domain_tags": ["enterprise"],
        "source_url": "https://example.com",
        "content_hash": f"{service}-hash",
        "parent_document_id": service,
        "section_title": service,
        "chunk_type": "service_guidance",
    }
