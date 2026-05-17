# OCI Native Retrieval Runbook

## Current State

Staging uses Oracle AI Vector Search with OCI GenAI embeddings.

| Area | Value |
| --- | --- |
| Retrieval | `RETRIEVAL_PROVIDER=oracle_ai_vector_search` |
| Embeddings | `EMBEDDING_PROVIDER=oci_genai` |
| Model | `cohere.embed-v4.0` |
| Dimensions | `1536` |
| Table | `OCI_ARCHITECTURE_CHUNKS_V4` |
| Index | `OCI_ARCH_CHUNKS_V4_VEC_IDX` |
| Rollback manifest | `oci-rag-index.local-hash.json` |

## Health Check

```bash
curl -fsS http://193.122.149.102:8000/retrieval/health
```

Expected:

```text
provider=oracle_ai_vector_search
embedding_provider=oci_genai
index_dimensions=1536
embedding_index_guardrail.ok=true
fallback_active=false
```

## Rebuild Index

Use this only after source/corpus changes or an approved embedding migration.

```bash
python knowledge/ingestion/ingest.py \
  --embedding-provider oci_genai \
  --oci-genai-embedding-model-id "$OCI_GENAI_EMBEDDING_MODEL_ID" \
  --oci-genai-compartment-id "$OCI_GENAI_COMPARTMENT_ID" \
  --oci-region us-ashburn-1
```

Verify the manifest:

```text
embedding_provider=oci_genai
embedding_model=<approved model>
dimensions=1536
chunk_count=<expected source count>
```

Then sync through the existing approved Object Storage/vector sync flow. Do not flip runtime flags before the new index is available.

## Promote Runtime

Apply through the reviewed runtime/Vault path:

```text
RETRIEVAL_PROVIDER=oracle_ai_vector_search
EMBEDDING_PROVIDER=oci_genai
OCI_GENAI_EMBEDDING_MODEL_ID=cohere.embed-v4.0
OCI_GENAI_EMBEDDING_DIMENSIONS=1536
OCI_VECTOR_TABLE_NAME=OCI_ARCHITECTURE_CHUNKS_V4
OCI_VECTOR_INDEX_NAME=OCI_ARCH_CHUNKS_V4_VEC_IDX
OCI_VECTOR_DIMENSIONS=1536
```

Restart backend and verify `/retrieval/health`.

## Rollback To Object Storage

```text
RETRIEVAL_PROVIDER=oci_object_storage
```

Restart backend and verify `/retrieval/health`.

## Rollback To Local Hash Embeddings

```text
EMBEDDING_PROVIDER=local
OCI_VECTOR_OBJECT_NAME=oci-rag-index.local-hash.json
OCI_VECTOR_TABLE_NAME=OCI_ARCHITECTURE_CHUNKS
OCI_VECTOR_INDEX_NAME=OCI_ARCH_CHUNKS_VEC_IDX
OCI_VECTOR_DIMENSIONS=256
```

Restart backend and verify:

```text
embedding_provider=local
index_dimensions=256
embedding_index_guardrail.ok=true
```

## Required Validation

```bash
python3 infra/scripts/smoke_oci_deployment.py \
  --api-base-url http://193.122.149.102:8000 \
  --frontend-url http://193.122.149.102:8000/

PYTHONPATH=app/backend/src app/backend/.venv/bin/python infra/scripts/retrieval_regression_check.py \
  --output-dir evals/reports/retrieval

PYTHONPATH=app/backend/src app/backend/.venv/bin/python evals/run_golden.py \
  --cases evals/golden-prompts.jsonl \
  --output-dir evals/reports/golden

PYTHONPATH=app/backend/src app/backend/.venv/bin/python evals/run_golden.py \
  --cases evals/edge-cases.jsonl \
  --output-dir evals/reports/edge-cases
```

## Important Rules

- Do not mix a 1536-dimension OCI GenAI embedder with a 256-dimension local hash index.
- Do not change embedding model, dimensions, table, or manifest independently.
- Keep rollback manifest `oci-rag-index.local-hash.json`.
- Do not print secrets, wallet passwords, or OCIDs in public docs.
