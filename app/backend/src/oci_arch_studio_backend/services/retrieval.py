from pathlib import Path

from oci_arch_studio_backend.models.architecture import RetrievedSource
from oci_arch_studio_backend.services.embeddings import LocalHashingEmbedder
from oci_arch_studio_backend.services.intents import IntentProfile
from oci_arch_studio_backend.services.vector_store import JsonVectorStore


class OciKnowledgeRetriever:
    """Retrieves OCI knowledge chunks from the local JSON vector index."""

    def __init__(
        self,
        index_path: Path,
        top_k: int = 4,
        embedder: LocalHashingEmbedder | None = None,
    ) -> None:
        self.store = JsonVectorStore(index_path=index_path)
        self.top_k = top_k
        self.embedder = embedder or LocalHashingEmbedder()

    async def retrieve(
        self,
        question: str,
        intent_profile: IntentProfile | None = None,
    ) -> list[RetrievedSource]:
        if not self.store.exists:
            return self._missing_index_sources()

        retrieval_query = self._build_retrieval_query(question, intent_profile)
        query_embedding = self.embedder.embed(retrieval_query)
        results = self.store.search(query_embedding=query_embedding, top_k=self.top_k)

        if not results:
            return self._missing_index_sources()

        return [
            RetrievedSource(
                chunk_id=chunk.id,
                title=chunk.title,
                source_type=chunk.source_type,
                url=chunk.url,
                summary=chunk.text,
                relevance_score=round(score, 4),
            )
            for chunk, score in results
        ]

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


PlaceholderRetriever = OciKnowledgeRetriever
