# Ingestion

OCI source ingestion code.

Initial target:
- define approved OCI source registry
- fetch source metadata
- normalize documents into retrievable records
- chunk source text
- create local deterministic embeddings
- write a JSON vector index to `knowledge/snapshots/oci-rag-index.json`
