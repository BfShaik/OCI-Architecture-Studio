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

    def search(self, query_embedding: list[float], top_k: int = 4) -> list[tuple[VectorChunk, float]]:
        chunks = self._load_chunks()
        scored = [
            (chunk, cosine_similarity(query_embedding, chunk.embedding))
            for chunk in chunks
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]

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
