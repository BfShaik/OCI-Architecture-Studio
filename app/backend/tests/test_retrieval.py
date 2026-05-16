import json

import pytest

from oci_arch_studio_backend.core.config import Settings
from oci_arch_studio_backend.services.embeddings import LocalHashingEmbedder
from oci_arch_studio_backend.services.intents import Intent, get_intent_profile
from oci_arch_studio_backend.services.retrieval import OciKnowledgeRetriever, build_retriever
from oci_arch_studio_backend.services.vector_store import (
    JsonVectorStore,
    OracleAiVectorSearchConfig,
    OracleAiVectorSearchStore,
    OciObjectStorageVectorConfig,
    OciObjectStorageVectorStore,
    VectorChunk,
    VectorSearchFilters,
)


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


def test_vector_store_boosts_intent_domain_and_pattern_metadata(tmp_path) -> None:
    embedder = LocalHashingEmbedder()
    index_path = tmp_path / "index.json"
    generic_text = "OCI architecture guidance should consider availability and operations."
    dr_text = "OCI Full Stack Disaster Recovery coordinates failover runbooks for DR."
    index_path.write_text(
        json.dumps(
            {
                "chunks": [
                    {
                        "id": "generic::1",
                        "title": "OCI Architecture Overview",
                        "url": "https://example.com/architecture",
                        "source_type": "oci_doc",
                        "text": generic_text,
                        "embedding": embedder.embed(generic_text),
                        "metadata": {
                            "service": "Architecture Center",
                            "service_domain": "architecture",
                            "intent_tags": ["architecture"],
                            "freshness_score": 0.9,
                            "trust_level": "official",
                            "architecture_patterns": ["reference-architecture"],
                        },
                    },
                    {
                        "id": "dr::1",
                        "title": "OCI Full Stack Disaster Recovery",
                        "url": "https://example.com/dr",
                        "source_type": "oci_doc",
                        "text": dr_text,
                        "embedding": embedder.embed(dr_text),
                        "metadata": {
                            "service": "Full Stack Disaster Recovery",
                            "service_domain": "resilience",
                            "intent_tags": ["dr"],
                            "freshness_score": 0.9,
                            "trust_level": "official",
                            "architecture_patterns": ["disaster-recovery"],
                        },
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    store = JsonVectorStore(index_path)
    results = store.search(
        embedder.embed("How should I plan disaster recovery?"),
        filters=VectorSearchFilters(
            intent="dr",
            service_domains=("resilience",),
            architecture_patterns=("disaster-recovery",),
        ),
    )

    assert results[0][0].id == "dr::1"


def test_service_mapping_biases_migration_retrieval(tmp_path) -> None:
    embedder = LocalHashingEmbedder()
    index_path = tmp_path / "index.json"
    generic_text = "OCI architecture guidance should consider availability and operations."
    oke_text = "OCI Kubernetes Engine provides a managed Kubernetes platform for container workloads."
    index_path.write_text(
        json.dumps(
            {
                "chunks": [
                    {
                        "id": "generic::1",
                        "title": "OCI Architecture Overview",
                        "url": "https://example.com/architecture",
                        "source_type": "oci_doc",
                        "text": generic_text,
                        "embedding": embedder.embed(generic_text),
                        "metadata": {
                            "service": "Architecture Center",
                            "service_domain": "architecture",
                            "intent_tags": ["architecture"],
                            "freshness_score": 0.9,
                            "trust_level": "official",
                            "architecture_patterns": ["reference-architecture"],
                        },
                    },
                    {
                        "id": "oke::1",
                        "title": "OCI Kubernetes Engine",
                        "url": "https://example.com/oke",
                        "source_type": "oci_doc",
                        "text": oke_text,
                        "embedding": embedder.embed(oke_text),
                        "metadata": {
                            "service": "OCI Kubernetes Engine",
                            "service_domain": "containers",
                            "intent_tags": ["migration", "architecture"],
                            "freshness_score": 0.9,
                            "trust_level": "official",
                            "architecture_patterns": ["container-platform"],
                            "migration_mappings": {"EKS": "OKE"},
                        },
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    retriever = OciKnowledgeRetriever(index_path=index_path, embedder=embedder)

    import asyncio

    results = asyncio.run(
        retriever.retrieve("Migrate EKS workloads to OCI.", get_intent_profile(Intent.MIGRATION))
    )

    assert results[0].chunk_id == "oke::1"
    assert results[0].migration_mappings == {"EKS": "OKE"}


def test_mapped_service_selection_prioritizes_operational_coverage(tmp_path) -> None:
    retriever = OciKnowledgeRetriever(index_path=tmp_path / "missing.json")

    ordered = retriever._prioritized_mapped_services(  # noqa: SLF001 - regression for mapped-service selection.
        (
            "Virtual Cloud Network",
            "OCI Kubernetes Engine",
            "Database Migration",
            "Load Balancer",
            "Container Registry",
            "Database Services",
            "Autonomous Database",
            "Logging",
            "Monitoring",
            "Identity and Access Management",
        )
    )

    assert ordered[:6] == (
        "OCI Kubernetes Engine",
        "Database Migration",
        "Load Balancer",
        "Container Registry",
        "Database Services",
        "Autonomous Database",
    )


def test_security_service_selection_prioritizes_landing_zone_controls(tmp_path) -> None:
    retriever = OciKnowledgeRetriever(index_path=tmp_path / "missing.json", top_k=6)
    reranked = [
        (_chunk("fsdr::1", "Full Stack Disaster Recovery", "resilience"), 0.96),
        (_chunk("db::1", "Database Services", "database"), 0.95),
        (_chunk("iam::1", "Identity and Access Management", "security"), 0.74),
        (_chunk("vcn::1", "Virtual Cloud Network", "networking"), 0.73),
        (_chunk("vault::1", "Vault", "security"), 0.72),
        (_chunk("cloud-guard::1", "Cloud Guard", "security"), 0.71),
        (_chunk("audit::1", "Audit", "security"), 0.7),
        (_chunk("logging::1", "Logging", "observability"), 0.69),
        (_chunk("monitoring::1", "Monitoring", "observability"), 0.68),
    ]

    selected = retriever._select_final_chunks(  # noqa: SLF001 - regression for landing-zone service accuracy.
        reranked,
        mapped_services=(
            "Audit",
            "Cloud Guard",
            "Logging",
            "Monitoring",
            "Vault",
            "Virtual Cloud Network",
            "Identity and Access Management",
        ),
        pattern_services=(),
        intent="security",
    )

    selected_services = [chunk.metadata["service"] for chunk, _score in selected]
    assert selected_services == [
        "Identity and Access Management",
        "Virtual Cloud Network",
        "Vault",
        "Cloud Guard",
        "Audit",
        "Logging",
    ]


def test_final_chunk_selection_adds_intent_diversity(tmp_path) -> None:
    retriever = OciKnowledgeRetriever(index_path=tmp_path / "missing.json", top_k=4)
    reranked = [
        (_chunk("arch::1", "Architecture Center", "architecture"), 0.9),
        (_chunk("arch::2", "Architecture Center", "architecture"), 0.89),
        (_chunk("net::1", "Load Balancer", "networking"), 0.7),
        (_chunk("db::1", "Database Services", "database"), 0.69),
        (_chunk("obs::1", "Monitoring", "observability"), 0.68),
    ]

    selected = retriever._select_final_chunks(  # noqa: SLF001 - regression for retrieval diversity.
        reranked,
        mapped_services=(),
        pattern_services=(),
        intent="architecture",
    )

    selected_domains = [chunk.metadata["service_domain"] for chunk, _score in selected]
    assert selected_domains == ["networking", "database", "observability", "architecture"]


def test_final_chunk_selection_protects_intent_critical_services(tmp_path) -> None:
    retriever = OciKnowledgeRetriever(index_path=tmp_path / "missing.json", top_k=6)
    reranked = [
        (_chunk("security::1", "Security Services", "security"), 0.96),
        (_chunk("cost::1", "Cost Management", "cost"), 0.95),
        (_chunk("lb::1", "Load Balancer", "networking"), 0.72),
        (_chunk("db::1", "Database Services", "database"), 0.71),
        (_chunk("object::1", "Object Storage", "storage"), 0.7),
        (_chunk("logging::1", "Logging", "observability"), 0.69),
        (_chunk("monitoring::1", "Monitoring", "observability"), 0.68),
    ]

    selected = retriever._select_final_chunks(  # noqa: SLF001 - regression for architecture-aware coverage.
        reranked,
        mapped_services=(),
        pattern_services=(),
        intent="saas_platform",
    )

    selected_services = [chunk.metadata["service"] for chunk, _score in selected]
    assert selected_services[:5] == [
        "Load Balancer",
        "Database Services",
        "Object Storage",
        "Logging",
        "Monitoring",
    ]


def _chunk(chunk_id: str, service: str, service_domain: str) -> VectorChunk:
    return VectorChunk(
        id=chunk_id,
        title=service,
        url="https://example.com",
        source_type="oci_doc",
        text=f"{service} guidance",
        embedding=[1.0, 0.0],
        metadata={"service": service, "service_domain": service_domain},
    )


def test_retriever_debug_trace_explains_reranking(tmp_path) -> None:
    embedder = LocalHashingEmbedder()
    index_path = tmp_path / "index.json"
    generic_text = "OCI architecture guidance should consider availability and operations."
    cloudwatch_text = "OCI Logging and Monitoring provide logs, metrics, alarms, and operational visibility."
    index_path.write_text(
        json.dumps(
            {
                "chunks": [
                    {
                        "id": "generic::1",
                        "title": "OCI Architecture Overview",
                        "url": "https://example.com/architecture",
                        "source_type": "oci_doc",
                        "text": generic_text,
                        "embedding": embedder.embed(generic_text),
                        "metadata": {
                            "service": "Architecture Center",
                            "service_domain": "architecture",
                            "intent_tags": ["architecture"],
                            "freshness_score": 0.9,
                            "trust_level": "official",
                            "architecture_patterns": ["reference-architecture"],
                        },
                    },
                    {
                        "id": "observability::1",
                        "title": "OCI Logging and Monitoring",
                        "url": "https://example.com/observability",
                        "source_type": "oci_doc",
                        "text": cloudwatch_text,
                        "embedding": embedder.embed(cloudwatch_text),
                        "metadata": {
                            "service": "Logging",
                            "service_domain": "observability",
                            "intent_tags": ["observability", "architecture"],
                            "freshness_score": 0.9,
                            "trust_level": "official",
                            "architecture_patterns": ["operational-visibility", "alarms"],
                            "workload_types": ["enterprise-app"],
                            "domain_tags": ["enterprise"],
                        },
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    retriever = OciKnowledgeRetriever(index_path=index_path, embedder=embedder)

    import asyncio

    results = asyncio.run(
        retriever.retrieve(
            "Migrate CloudWatch alarms to OCI observability.",
            get_intent_profile(Intent.OBSERVABILITY),
            debug_enabled=True,
        )
    )

    assert results[0].chunk_id == "observability::1"
    assert retriever.last_debug_trace is not None
    assert retriever.last_debug_trace.provider == "local_json"
    assert retriever.last_debug_trace.detected_intent == "observability"
    assert retriever.last_debug_trace.metadata_filters["intent"] == "observability"
    assert retriever.last_debug_trace.retrieved_chunk_diversity["observability"] >= 1
    assert "Logging" in retriever.last_debug_trace.mapped_oci_services
    assert retriever.last_debug_trace.selected_final_chunks[0] == "observability::1"
    assert any(
        "intent_match" in score.adjustments
        for score in retriever.last_debug_trace.retrieval_scores
        if score.chunk_id == "observability::1"
    )


def test_build_retriever_falls_back_when_oci_object_storage_settings_are_missing(tmp_path) -> None:
    settings = Settings(
        KNOWLEDGE_INDEX_PATH=tmp_path / "index.json",
        RETRIEVAL_PROVIDER="oci_object_storage",
    )

    retriever = build_retriever(settings)
    diagnostics = retriever.diagnostics()

    assert diagnostics["store"]["fallback_enabled"] is True
    assert diagnostics["store"]["fallback_active"] is True
    assert "OCI_OBJECT_STORAGE_NAMESPACE" in diagnostics["store"]["primary"]["missing_config"]


def test_build_retriever_can_require_oci_object_storage_settings(tmp_path) -> None:
    settings = Settings(
        KNOWLEDGE_INDEX_PATH=tmp_path / "index.json",
        RETRIEVAL_PROVIDER="oci_object_storage",
        RETRIEVAL_FALLBACK_ENABLED=False,
    )

    with pytest.raises(ValueError, match="OCI_OBJECT_STORAGE_NAMESPACE"):
        build_retriever(settings)


def test_build_retriever_falls_back_when_oci_embedding_settings_are_missing(tmp_path) -> None:
    settings = Settings(
        KNOWLEDGE_INDEX_PATH=tmp_path / "index.json",
        EMBEDDING_PROVIDER="oci_genai",
    )

    retriever = build_retriever(settings)
    diagnostics = retriever.diagnostics()

    assert diagnostics["embedding"]["fallback_enabled"] is True
    assert "OCI_GENAI_COMPARTMENT_ID" in diagnostics["embedding"]["activation_error"]


def test_build_retriever_can_require_oci_embedding_settings(tmp_path) -> None:
    settings = Settings(
        KNOWLEDGE_INDEX_PATH=tmp_path / "index.json",
        EMBEDDING_PROVIDER="oci_genai",
        EMBEDDING_FALLBACK_ENABLED=False,
    )

    with pytest.raises(ValueError, match="OCI_GENAI_COMPARTMENT_ID"):
        build_retriever(settings)


def test_oracle_ai_vector_search_store_is_guarded_until_enabled() -> None:
    store = OracleAiVectorSearchStore(OracleAiVectorSearchConfig())

    health = store.health()

    assert health["provider"] == "oracle_ai_vector_search"
    assert health["exists"] is False
    assert health["read_enabled"] is False
    assert "OCI_VECTOR_DB_DSN" in health["missing_config"]


def test_oci_object_storage_store_exists_uses_cached_chunks() -> None:
    class CachedObjectStorageStore(OciObjectStorageVectorStore):
        def __init__(self) -> None:
            super().__init__(
                OciObjectStorageVectorConfig(
                    namespace="example",
                    bucket_name="bucket",
                    object_name="index.json",
                )
            )
            self.read_count = 0
            self._chunks = [
                VectorChunk(
                    id="chunk::1",
                    title="Cached Chunk",
                    url="https://example.com",
                    source_type="oci_doc",
                    text="cached text",
                    embedding=[1.0],
                    metadata={},
                )
            ]

        def _read_object_text(self) -> str:
            self.read_count += 1
            raise AssertionError("cached exists should not read Object Storage")

    store = CachedObjectStorageStore()

    assert store.exists is True
    assert store.read_count == 0
