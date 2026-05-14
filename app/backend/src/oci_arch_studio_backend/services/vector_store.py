import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from oci_arch_studio_backend.services.embeddings import cosine_similarity


@dataclass(frozen=True)
class VectorChunk:
    id: str
    title: str
    url: str | None
    source_type: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any]


class JsonVectorStore:
    def __init__(self, index_path: Path) -> None:
        self.index_path = index_path
        self._chunks: list[VectorChunk] | None = None

    @property
    def exists(self) -> bool:
        return self.index_path.exists()

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 4,
        intent: str | None = None,
    ) -> list[tuple[VectorChunk, float]]:
        chunks = self._load_chunks()
        scored = [
            (chunk, self._rank_score(chunk, cosine_similarity(query_embedding, chunk.embedding), intent))
            for chunk in chunks
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]

    def _rank_score(self, chunk: VectorChunk, similarity: float, intent: str | None) -> float:
        metadata = chunk.metadata
        score = similarity
        if intent and intent in metadata.get("intent_tags", []):
            score += 0.08
        if metadata.get("trust_level") == "official":
            score += 0.03
        freshness_score = metadata.get("freshness_score")
        if isinstance(freshness_score, int | float):
            score += min(max(float(freshness_score), 0.0), 1.0) * 0.02
        return score

    def _load_chunks(self) -> list[VectorChunk]:
        if self._chunks is not None:
            return self._chunks

        if not self.index_path.exists():
            self._chunks = []
            return self._chunks

        with self.index_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        self._chunks = [
            VectorChunk(
                id=chunk["id"],
                title=chunk["title"],
                url=chunk.get("url"),
                source_type=chunk.get("source_type", "oci_doc"),
                text=chunk["text"],
                embedding=chunk["embedding"],
                metadata=chunk.get("metadata", {}),
            )
            for chunk in payload.get("chunks", [])
        ]
        return self._chunks
