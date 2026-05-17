# Internal Beta Readiness

Last updated: 2026-05-17

## Decision

OCI Architecture Studio is ready for controlled internal-beta use in staging.

It is not yet a production HA service and not a full OCI documentation mirror.

## Current Staging Baseline

| Area | State |
| --- | --- |
| Synthesis | OCI GenAI active |
| Retrieval | Oracle AI Vector Search active |
| Embeddings | OCI GenAI `cohere.embed-v4.0`, 1536 dimensions |
| Corpus | 60 curated chunks |
| UI | Review workflow, citations, history controls, pinned composer |
| Operations | Health, retrieval health, readiness, analytics |
| Rollback | deterministic synthesis, Object Storage/local retrieval, local hash embeddings |

## Validation Snapshot

- `/health`: passing
- `/retrieval/health`: passing
- `/architecture-review`: returns `synthesis_provider=oci_genai`
- Retrieval regression: `32/32`
- Golden evals: `18/18`
- Edge evals: `8/8`

## Accepted Beta Limits

- Team-real prompt eval file is missing and should be restored.
- Corpus coverage is intentionally small.
- Release awareness is snapshot-based.
- Cost guidance is advisory and does not read live billing data.
- Governance metadata supports human review; it is not policy enforcement.
- Production HA, HTTPS/domain hardening, and custom OCI Monitoring metrics remain future work.

## Before Wider Rollout

1. Restore `evals/team-real-prompts.jsonl`.
2. Run team-real prompts against staging.
3. Review answer quality with architects.
4. Track GenAI cost and latency.
5. Confirm rollback procedure still works.
