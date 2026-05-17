# Product Requirements

## Purpose

OCI Architecture Studio is an AI-powered OCI architecture review assistant. It helps teams produce grounded, structured, citation-backed recommendations for OCI architecture, migration, resilience, security, observability, AI/ML, analytics, SaaS, and cost questions.

## Current Runtime Contract

| Area | Local/default | Staging/current |
| --- | --- | --- |
| Synthesis | `deterministic` | `oci_genai` |
| Retrieval | `local_json` | `oracle_ai_vector_search` |
| Embeddings | `local` | `oci_genai` |
| Chat model | unset | `xai.grok-4.3` |
| Embedding model | local hash | `cohere.embed-v4.0` |
| Dimensions | 256 | 1536 |
| Vector table | local/Object Storage manifest | `OCI_ARCHITECTURE_CHUNKS_V4` |

Staging overrides are applied through the reviewed runtime/Vault path. Local defaults stay simple so contributors can run the app without OCI credentials.

## Primary User Flow

1. User enters an OCI architecture question in the frontend.
2. Frontend calls `POST /architecture-review`.
3. Backend classifies intent and maps source services to OCI services when relevant.
4. Backend retrieves evidence from the configured retrieval provider.
5. Backend synthesizes a structured answer with the configured synthesis provider.
6. Backend returns recommendations, assumptions, risks, citations, confidence, topology, governance, migration/FinOps, release context, and optional debug metadata.
7. Frontend displays the answer in review-friendly sections with visible links and actions.

## Required Capabilities

- Support architecture, migration, DR, cost, observability, AI/ML, security, modernization, SaaS, analytics, release-awareness, and general prompts.
- Use retrieved OCI evidence before synthesis.
- Return a stable API schema for the frontend.
- Show citations and source links.
- Surface `synthesis_provider` and `synthesis_fallback_used`.
- Expose retrieval health and embedding/index guardrail state.
- Keep rollback paths config-only.
- Keep local development independent of live OCI connectivity.

## Current Implemented Capabilities

- React/Vite frontend and FastAPI backend.
- OCI GenAI synthesis in staging with deterministic fail-closed fallback.
- Oracle AI Vector Search retrieval in staging.
- OCI GenAI embeddings in staging with `cohere.embed-v4.0` at 1536 dimensions.
- Local JSON retrieval and local hash embeddings for development and rollback.
- Object Storage vector manifest rollback.
- Controlled in-process orchestration with supervisor, bounded specialists, final synthesis, and validation critic.
- Section-level citations, evidence links, confidence signals, topology metadata, governance metadata, migration/FinOps metadata, and release context.
- Saved review history with retention/export/delete controls.
- Release-watch refresh path through backend VM cron.
- Golden, edge, retrieval, and quality evals.
- Health, retrieval health, orchestration health, operations health/readiness/infrastructure/analytics endpoints.

## Important API/Config Contract

Main API:

- `GET /health`
- `POST /architecture-review`
- `GET /retrieval/health`
- `GET /orchestration/health`
- `GET /operations/health`
- `GET /operations/readiness`
- `GET /operations/infrastructure`
- `GET /operations/analytics`

Main runtime flags:

- `ADVISORY_SYNTHESIS_PROVIDER=deterministic|oci_genai`
- `RETRIEVAL_PROVIDER=local_json|oci_object_storage|oracle_ai_vector_search`
- `EMBEDDING_PROVIDER=local|oci_genai`
- `OCI_GENAI_COMPARTMENT_ID`
- `OCI_GENAI_CHAT_MODEL_ID`
- `OCI_GENAI_EMBEDDING_MODEL_ID`
- `OCI_GENAI_EMBEDDING_DIMENSIONS`
- `OCI_VECTOR_TABLE_NAME`
- `OCI_VECTOR_INDEX_NAME`
- `OCI_VECTOR_DIMENSIONS`

## Rollback Requirements

Synthesis rollback:

```text
ADVISORY_SYNTHESIS_PROVIDER=deterministic
```

Retrieval rollback:

```text
RETRIEVAL_PROVIDER=oci_object_storage
```

Emergency local retrieval:

```text
RETRIEVAL_PROVIDER=local_json
```

Embedding rollback:

```text
EMBEDDING_PROVIDER=local
OCI_VECTOR_OBJECT_NAME=oci-rag-index.local-hash.json
OCI_VECTOR_TABLE_NAME=OCI_ARCHITECTURE_CHUNKS
OCI_VECTOR_INDEX_NAME=OCI_ARCH_CHUNKS_VEC_IDX
OCI_VECTOR_DIMENSIONS=256
```

After any rollback, restart the backend and verify `/health`, `/retrieval/health`, and a representative `/architecture-review` request.

## Evaluation Requirements

Before promotion or after material changes, run:

- backend tests
- frontend lint/build
- retrieval regression
- golden prompts
- edge cases
- staging smoke
- `/retrieval/health`

Current missing eval input:

- `evals/team-real-prompts.jsonl` should be restored or recreated for team-real prompt validation.

## Non-Goals

- No autonomous agent execution.
- No LangGraph runtime.
- No persistent agent memory.
- No production HA claim yet.
- No live request-time release reconciliation.
- No full OCI documentation mirror.
- No removal of deterministic/local rollback paths.
