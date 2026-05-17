# GenAI Advisory Hardening

## Current State

OCI GenAI synthesis is active in staging.

```text
ADVISORY_SYNTHESIS_PROVIDER=oci_genai
OCI_GENAI_CHAT_MODEL_ID=<approved chat model>
OCI_GENAI_COMPARTMENT_ID=<approved compartment>
```

Current staging chat model:

```text
xai.grok-4.3
```

Do not print secret or tenancy-specific runtime values in docs or logs.

## Why Hardening Exists

GenAI output must stay:

- grounded in retrieved OCI evidence
- valid for the frontend schema
- clear about uncertainty
- free of invented OCI services
- citation-aware
- rollback-safe

## Prompt Inputs

The GenAI prompt includes:

- user question
- classified intent
- mapped source/target services
- workload/domain hints
- architecture pattern hints
- retrieved OCI chunks
- required response sections

## Fallback

If OCI GenAI fails, the backend falls back to deterministic synthesis.

Rollback switch:

```text
ADVISORY_SYNTHESIS_PROVIDER=deterministic
```

After rollback, restart the backend and run a smoke test.

## Validation

Run parity/eval checks after model, prompt, corpus, or runtime changes:

```bash
PYTHONPATH=app/backend/src app/backend/.venv/bin/python infra/scripts/genai_synthesis_parity_check.py \
  --cases evals/golden-prompts.jsonl \
  --cases evals/edge-cases.jsonl \
  --output-dir evals/reports/genai-parity
```

Check:

- no fallback on healthy GenAI requests
- valid JSON/schema
- citation coverage preserved
- no unsupported OCI claims
- latency and cost acceptable

## Embeddings

Staging uses OCI GenAI embeddings:

```text
EMBEDDING_PROVIDER=oci_genai
OCI_GENAI_EMBEDDING_MODEL_ID=cohere.embed-v4.0
OCI_GENAI_EMBEDDING_DIMENSIONS=1536
```

Rollback:

```text
EMBEDDING_PROVIDER=local
OCI_VECTOR_OBJECT_NAME=oci-rag-index.local-hash.json
OCI_VECTOR_DIMENSIONS=256
```

Always verify `/retrieval/health` after embedding changes.
