import json

import pytest

from oci_arch_studio_backend.core.config import Settings
from oci_arch_studio_backend.services.embeddings import LocalHashingEmbedder
from oci_arch_studio_backend.services.retrieval import OciKnowledgeRetriever, build_retriever
from oci_arch_studio_backend.services.vector_store import JsonVectorStore, VectorSearchFilters


def test_retriever_returns_ranked_chunks(tmp_path) -> None:
    embedder = LocalHashingEmbedder()
    index_path = tmp_path / "index.json"
    chunk_text = (
        "OCI Load Balancer supports highly available application entry points "
        "with backend health checks."
    )
    index_path.write_text(
        json.dumps(
            {
                "chunks": [
                    {
                        "id": "load-balancer::1",
                        "title": "OCI Load Balancer Overview",
                        "url": "https://example.com/load-balancer",
                        "source_type": "oci_service_doc",
                        "text": chunk_text,
                        "embedding": embedder.embed(chunk_text),
                        "metadata": {
                            "chunk_index": 1,
                            "source_url": "https://example.com/load-balancer",
                            "service": "Load Balancer",
                            "service_domain": "networking",
                            "intent_tags": ["architecture"],
                            "fetched_timestamp": "2026-05-14T00:00:00+00:00",
                            "freshness_score": 0.9,
                            "trust_level": "official",
                            "architecture_patterns": ["public-ingress"],
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    retriever = OciKnowledgeRetriever(index_path=index_path, embedder=embedder)

    import asyncio

    results = asyncio.run(retriever.retrieve("How do I make web ingress highly available?"))

    assert results[0].chunk_id == "load-balancer::1"
    assert results[0].title == "OCI Load Balancer Overview"
    assert results[0].service == "Load Balancer"
    assert results[0].service_domain == "networking"
    assert results[0].source_url == "https://example.com/load-balancer"
    assert results[0].trust_level == "official"
    assert not results[0].is_stale
    assert results[0].relevance_score is not None


def test_vector_store_filters_by_service_domain(tmp_path) -> None:
    embedder = LocalHashingEmbedder()
    index_path = tmp_path / "index.json"
    network_text = "OCI Load Balancer supports public ingress and backend health checks."
    storage_text = "OCI Object Storage stores static assets and backups durably."
    index_path.write_text(
        json.dumps(
            {
                "chunks": [
                    {
                        "id": "load-balancer::1",
                        "title": "OCI Load Balancer Overview",
                        "url": "https://example.com/load-balancer",
                        "source_type": "oci_service_doc",
                        "text": network_text,
                        "embedding": embedder.embed(network_text),
                        "metadata": {
                            "source_url": "https://example.com/load-balancer",
                            "service_domain": "networking",
                            "intent_tags": ["architecture"],
                            "freshness_score": 0.9,
                            "trust_level": "official",
                        },
                    },
                    {
                        "id": "object-storage::1",
                        "title": "OCI Object Storage Overview",
                        "url": "https://example.com/object-storage",
                        "source_type": "oci_service_doc",
                        "text": storage_text,
                        "embedding": embedder.embed(storage_text),
                        "metadata": {
                            "source_url": "https://example.com/object-storage",
                            "service_domain": "storage",
                            "intent_tags": ["architecture", "cost"],
                            "freshness_score": 0.9,
                            "trust_level": "official",
                        },
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    store = JsonVectorStore(index_path)
    results = store.search(
        embedder.embed("Where should static assets go?"),
        filters=VectorSearchFilters(service_domain="storage"),
    )

    assert [chunk.id for chunk, _score in results] == ["object-storage::1"]


def test_build_retriever_requires_oci_vector_settings(tmp_path) -> None:
    settings = Settings(
        KNOWLEDGE_INDEX_PATH=tmp_path / "index.json",
        RETRIEVAL_PROVIDER="oci_object_storage",
    )

    with pytest.raises(ValueError, match="OCI_OBJECT_STORAGE_NAMESPACE"):
        build_retriever(settings)


def test_build_retriever_requires_oci_embedding_settings(tmp_path) -> None:
    settings = Settings(
        KNOWLEDGE_INDEX_PATH=tmp_path / "index.json",
        EMBEDDING_PROVIDER="oci_genai",
    )

    with pytest.raises(ValueError, match="OCI_GENAI_COMPARTMENT_ID"):
        build_retriever(settings)
