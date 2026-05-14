from pathlib import Path

from oci_arch_studio_backend.core.config import Settings
from oci_arch_studio_backend.models.architecture import RetrievedSource
from oci_arch_studio_backend.services.embeddings import (
    Embedder,
    LocalHashingEmbedder,
    OciGenerativeAiEmbedder,
    OciGenerativeAiEmbeddingConfig,
)
from oci_arch_studio_backend.services.freshness import is_stale_source
from oci_arch_studio_backend.services.intents import IntentProfile
from oci_arch_studio_backend.services.retrieval_metrics import retrieval_metrics
from oci_arch_studio_backend.services.vector_store import (
    JsonVectorStore,
    OciObjectStorageVectorConfig,
    OciObjectStorageVectorStore,
    VectorSearchFilters,
    VectorStore,
)


class OciKnowledgeRetriever:
    """Retrieves OCI knowledge chunks from the local JSON vector index."""

    def __init__(
        self,
        index_path: Path,
        top_k: int = 6,
        embedder: Embedder | None = None,
        store: VectorStore | None = None,
        provider_name: str = "local_json",
    ) -> None:
        self.store = store or JsonVectorStore(index_path=index_path)
        self.top_k = top_k
        self.embedder = embedder or LocalHashingEmbedder()
        self.provider_name = provider_name

    async def retrieve(
        self,
        question: str,
        intent_profile: IntentProfile | None = None,
    ) -> list[RetrievedSource]:
        started_at = retrieval_metrics.start()
        intent = intent_profile.intent.value if intent_profile else None
        if not self.store.exists:
            sources = self._missing_index_sources()
            retrieval_metrics.record(
                started_at=started_at,
                provider=self.provider_name,
                embedding_model=self.embedder.model_name,
                result_count=len(sources),
                intent=intent,
                missing_index=True,
                warning="retrieval index is missing or unreachable",
            )
            return sources

        retrieval_query = self._build_retrieval_query(question, intent_profile)
        query_embedding = self.embedder.embed(retrieval_query)
        filters = self._build_filters(intent_profile)
        results = self.store.search(
            query_embedding=query_embedding,
            top_k=self.top_k,
            filters=filters,
        )

        if not results:
            sources = self._missing_index_sources()
            retrieval_metrics.record(
                started_at=started_at,
                provider=self.provider_name,
                embedding_model=self.embedder.model_name,
                result_count=0,
                intent=intent,
                missing_index=True,
                warning="retrieval returned no matching chunks",
            )
            return sources

        sources = [self._to_retrieved_source(chunk, score) for chunk, score in results]
        retrieval_metrics.record(
            started_at=started_at,
            provider=self.provider_name,
            embedding_model=self.embedder.model_name,
            result_count=len(sources),
            intent=intent,
        )
        return sources

    def diagnostics(self) -> dict[str, object]:
        return {
            "provider": self.provider_name,
            "embedding_model": self.embedder.model_name,
            "store": self.store.health(),
            "metrics": retrieval_metrics.snapshot(),
        }

    def _to_retrieved_source(self, chunk, score: float) -> RetrievedSource:
        metadata = chunk.metadata
        source_url = metadata.get("source_url") or chunk.url
        freshness_score = metadata.get("freshness_score")
        freshness_value = float(freshness_score) if isinstance(freshness_score, int | float) else None
        fetched_timestamp = metadata.get("fetched_timestamp")
        fetched_value = str(fetched_timestamp) if fetched_timestamp else None
        return RetrievedSource(
            chunk_id=chunk.id,
            title=chunk.title,
            source_type=chunk.source_type,
            url=chunk.url,
            source_url=str(source_url) if source_url else None,
            service=str(metadata.get("service")) if metadata.get("service") else None,
            service_domain=str(metadata.get("service_domain")) if metadata.get("service_domain") else None,
            intent_tags=[str(tag) for tag in metadata.get("intent_tags", [])],
            fetched_timestamp=fetched_value,
            freshness_score=freshness_value,
            trust_level=str(metadata.get("trust_level")) if metadata.get("trust_level") else None,
            architecture_patterns=[str(pattern) for pattern in metadata.get("architecture_patterns", [])],
            is_stale=is_stale_source(fetched_value, freshness_value),
            summary=chunk.text,
            relevance_score=round(score, 4),
        )

    def _missing_index_sources(self) -> list[RetrievedSource]:
        return [
            RetrievedSource(
                chunk_id="missing-index",
                title="Local OCI RAG index",
                source_type="missing_index",
                url=None,
                summary=(
                    "No local vector index was found. Run "
                    "`python knowledge/ingestion/ingest.py` from the repository root "
                    "to build `knowledge/snapshots/oci-rag-index.json`."
                ),
                relevance_score=0.0,
            ),
        ]

    def _build_retrieval_query(
        self,
        question: str,
        intent_profile: IntentProfile | None,
    ) -> str:
        if intent_profile is None:
            return question
        return " ".join((question, intent_profile.focus, *intent_profile.retrieval_terms))

    def _build_filters(self, intent_profile: IntentProfile | None) -> VectorSearchFilters:
        if intent_profile is None:
            return VectorSearchFilters()
        return VectorSearchFilters(
            intent=intent_profile.intent.value,
            release_aware=intent_profile.intent.value == "release_awareness",
        )


def build_retriever(settings: Settings, top_k: int = 6) -> OciKnowledgeRetriever:
    embedder: Embedder
    if settings.embedding_provider == "oci_genai":
        if not settings.oci_genai_compartment_id or not settings.oci_genai_embedding_model_id:
            raise ValueError(
                "OCI_GENAI_COMPARTMENT_ID and OCI_GENAI_EMBEDDING_MODEL_ID are required "
                "when EMBEDDING_PROVIDER=oci_genai."
            )
        embedder = OciGenerativeAiEmbedder(
            OciGenerativeAiEmbeddingConfig(
                region=settings.oci_region,
                profile=settings.oci_profile,
                auth_mode=settings.oci_auth_mode,
                compartment_id=settings.oci_genai_compartment_id,
                model_id=settings.oci_genai_embedding_model_id,
                endpoint=settings.oci_genai_endpoint,
            )
        )
    else:
        embedder = LocalHashingEmbedder()

    if settings.retrieval_provider == "oci_object_storage":
        if not settings.oci_object_storage_namespace or not settings.oci_vector_bucket:
            raise ValueError(
                "OCI_OBJECT_STORAGE_NAMESPACE and OCI_VECTOR_BUCKET are required "
                "when RETRIEVAL_PROVIDER=oci_object_storage."
            )
        store: VectorStore = OciObjectStorageVectorStore(
            OciObjectStorageVectorConfig(
                namespace=settings.oci_object_storage_namespace,
                bucket_name=settings.oci_vector_bucket,
                object_name=settings.oci_vector_object_name,
                region=settings.oci_region,
                profile=settings.oci_profile,
                auth_mode=settings.oci_auth_mode,
            )
        )
        provider_name = "oci_object_storage"
    else:
        store = JsonVectorStore(index_path=settings.knowledge_index_path)
        provider_name = "local_json"

    return OciKnowledgeRetriever(
        index_path=settings.knowledge_index_path,
        top_k=top_k,
        embedder=embedder,
        store=store,
        provider_name=provider_name,
    )


PlaceholderRetriever = OciKnowledgeRetriever
