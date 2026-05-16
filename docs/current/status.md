# Current Status

Last updated: 2026-05-16

## Executive Summary

OCI Architecture Studio is running in staging with live OCI GenAI synthesis, OCI GenAI semantic embeddings, Oracle AI Vector Search retrieval, and rollback-safe Object Storage/local-hash paths. The current implementation is a validated internal-beta platform for OCI architecture advisory workflows, not yet a broad production OCI knowledge system.

## Live Staging Posture

| Area | Current value |
| --- | --- |
| Advisory synthesis | `oci_genai` |
| Chat model | `xai.grok-4.3` |
| Retrieval provider | `oracle_ai_vector_search` |
| Embedding provider | `oci_genai` |
| Embedding model | `cohere.embed-v4.0` |
| Vector dimensions | `1536` |
| Oracle vector table | `OCI_ARCHITECTURE_CHUNKS_V4` |
| Oracle vector index | `OCI_ARCH_CHUNKS_V4_VEC_IDX` |
| Active corpus | `60` chunks, `52` services, `15` domains |
| Retrieval fallback | inactive |
| Embedding guardrail | passing |

## Validation Snapshot

- Public `/health`: `200`
- Public `/retrieval/health`: `200`
- Retrieval regression: `32/32 passed`
- Golden evals: `18/18 passed`
- Edge evals: `8/8 passed`
- Focused backend tests: `29 passed`
- Public `/architecture-review` smoke: `200`, `synthesis_provider=oci_genai`, fallback disabled

`evals/team-real-prompts.jsonl` is not present in the repo or staging checkout. That is the only missing TASK-055 acceptance input.

## Completed Major Milestones

- OCI staging deployment on a Compute VM behind API Gateway.
- Oracle AI Vector Search active retrieval.
- OCI GenAI chat synthesis go-live.
- OCI GenAI embedding migration to `cohere.embed-v4.0` at 1536 dimensions.
- Retrieval/provider guardrail that refuses mismatched embedding provider/model/dimensions.
- Controlled in-process advisory orchestration with supervisor, specialist roles, final synthesis, and validation critic.
- Section-level citation traceability and evidence-linked recommendations.
- Saved review history with redaction, retention, export, and delete controls.
- Release-aware knowledge refresh scaffolding and VM cron path.
- Operational diagnostics endpoints for profile, health, readiness, infrastructure, analytics, retrieval, and orchestration.

## Current Rollback Paths

Embedding rollback:

```text
EMBEDDING_PROVIDER=local
OCI_VECTOR_OBJECT_NAME=oci-rag-index.local-hash.json
OCI_VECTOR_TABLE_NAME=OCI_ARCHITECTURE_CHUNKS
OCI_VECTOR_INDEX_NAME=OCI_ARCH_CHUNKS_VEC_IDX
OCI_VECTOR_DIMENSIONS=256
```

Retrieval-provider rollback:

```text
RETRIEVAL_PROVIDER=oci_object_storage
```

Emergency local rollback:

```text
RETRIEVAL_PROVIDER=local_json
```

After any rollback, restart the backend and verify `/retrieval/health` has `embedding_index_guardrail.ok=true`, the expected dimensions, and fallback state understood.

## Known Gaps

- `evals/team-real-prompts.jsonl` needs to be restored or created and run against staging.
- Corpus breadth is still curated and intentionally small.
- Query embedding cache is not implemented yet; add it if repeated-query cost or latency becomes material.
- Release impact analysis is deterministic and conservative; deeper semantic release analysis remains future work.
- The UI consumes topology metadata, but richer live diagram rendering is still future work.

## Next Logical Tasks

1. Add `evals/team-real-prompts.jsonl` and run it against live staging.
2. Monitor live v4 retrieval latency, fallback state, and quality.
3. Decide whether to add query embedding caching.
4. Continue documentation cleanup only where it improves operator clarity.
