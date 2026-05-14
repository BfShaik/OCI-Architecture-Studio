import json

from oci_arch_studio_backend.services.embeddings import LocalHashingEmbedder
from oci_arch_studio_backend.services.retrieval import OciKnowledgeRetriever


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
                        "metadata": {"chunk_index": 1},
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
    assert results[0].relevance_score is not None
