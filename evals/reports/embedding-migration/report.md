# Embedding Migration Report

Date: 2026-05-16

## Summary

- Promoted embedding provider: `oci_genai`
- Embedding model: `cohere.embed-v4.0`
- Region: `us-ashburn-1`
- Dimensions: `1536`
- Active retrieval provider: `oracle_ai_vector_search`
- Active Oracle vector table: `OCI_ARCHITECTURE_CHUNKS_V4`
- Active vector index: `OCI_ARCH_CHUNKS_V4_VEC_IDX`
- Chunk count: `60`
- Service count: `52`
- Service domain count: `15`
- Fallback active: `false`
- Guardrail: passed, configured provider/model/dimensions match index metadata

`cohere.embed-english-v3.0` was not usable in this tenancy/region during diagnostics, so the operator-approved best visible embedding target was `cohere.embed-v4.0`. The migration used a separate 1536-dimension Oracle vector table, leaving the previous 256-dimension local-hash table available for rollback.

## Validation

- Local focused tests: `29 passed`
- Candidate retrieval health: passed with fallback disabled
- Candidate retrieval regression: `32 passed, 0 failed`
- Live staging `/health`: `200`
- Live staging `/retrieval/health`: `200`
- Live staging retrieval regression: `32 passed, 0 failed`
- Live golden evals: `18 passed, 0 failed`
- Live edge evals: `8 passed, 0 failed`
- Public `/architecture-review` smoke: `200`, `synthesis_provider=oci_genai`, `synthesis_fallback_used=false`, six citations

`evals/team-real-prompts.jsonl` is not present in the repo or staging checkout, so that acceptance input could not be executed.

## Retrieval Lift

| Prompt | Local hash top 3 | Cohere v4 top 3 | Result |
| --- | --- | --- | --- |
| `saas-multi-region-002` | `oci-load-balancer-overview::1`, `oci-database-overview::1`, `oci-object-storage-overview::1` | `oci-load-balancer-overview::1`, `oci-database-overview::1`, `oci-object-storage-overview::1` | improved from missing `Logging` to pass |
| `hybrid-cloud-migration-003` | `oci-kubernetes-engine-overview::1`, `oci-database-migration-overview::1`, `oci-database-overview::1` | `oci-kubernetes-engine-overview::1`, `oci-load-balancer-overview::1`, `oci-logging-overview::1` | pass before and after |
| `vector-migration-eks-rds-001` | `oci-kubernetes-engine-overview::1`, `oci-database-migration-overview::1`, `oci-database-overview::1` | `oci-kubernetes-engine-overview::1`, `oci-load-balancer-overview::1`, `oci-logging-overview::1` | improved from missing `Monitoring` to pass |
| `vector-saas-resiliency-001` | `oci-load-balancer-overview::1`, `oci-database-overview::1`, `oci-object-storage-overview::1` | `oci-load-balancer-overview::1`, `oci-database-overview::1`, `oci-object-storage-overview::1` | improved from missing `Logging` to pass |

Overall retrieval regression improved from `28/32` on the active local-hash baseline to `32/32` after the OCI GenAI embedding migration plus candidate-pool/ranking fixes.

## Cost And Latency

- Reindex input estimate: `29,272` characters, `3,654` words, approximately `7,318` input tokens using a conservative `characters / 4` estimate.
- Query sample: first `20` eval prompts, `2,100` characters, approximately `525` input tokens total, or `26.2` tokens/query.
- Per-query embedding cost risk: expected to be well below `$0.001` at this prompt size, but exact USD depends on the active OCI Generative AI embedding price for the tenancy SKU.
- Live retrieval regression completed in a few seconds for `32` prompts. Public `/architecture-review` smoke remained HTTP `200`; no fallback was used.

## Rollback Readiness

- Previous hash manifest preserved in Object Storage as `oci-rag-index.local-hash.json`.
- Previous Oracle vector table remains `OCI_ARCHITECTURE_CHUNKS` at `256` dimensions.
- Rollback env shape:
  - `EMBEDDING_PROVIDER=local`
  - `OCI_VECTOR_TABLE_NAME=OCI_ARCHITECTURE_CHUNKS`
  - `OCI_VECTOR_INDEX_NAME=OCI_ARCH_CHUNKS_VEC_IDX`
  - `OCI_VECTOR_DIMENSIONS=256`
  - `OCI_VECTOR_OBJECT_NAME=oci-rag-index.local-hash.json`

After rollback, restart the backend and confirm `/retrieval/health` reports `embedding_provider=local`, `index_dimensions=256`, guardrail OK, and fallback inactive.
