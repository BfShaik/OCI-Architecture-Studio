# Active Execution Plan

Last updated: 2026-05-17

This page is the short operating plan. Historical task detail belongs in reports and archive docs.

## Current Baseline

| Area | Current staging value |
| --- | --- |
| Synthesis | `ADVISORY_SYNTHESIS_PROVIDER=oci_genai` |
| Chat model | `xai.grok-4.3` |
| Retrieval | `RETRIEVAL_PROVIDER=oracle_ai_vector_search` |
| Embeddings | `EMBEDDING_PROVIDER=oci_genai` |
| Embedding model | `cohere.embed-v4.0` |
| Dimensions | `1536` |
| Vector table | `OCI_ARCHITECTURE_CHUNKS_V4` |
| Rollback | deterministic synthesis, Object Storage retrieval, local hash embeddings |

## Recently Completed

- OCI GenAI synthesis promoted in staging.
- OCI GenAI embeddings promoted in staging.
- Oracle AI Vector Search promoted as active retrieval.
- Prompt/options composer stays pinned at top of the UI.
- Team presentation deck created and updated for the current GenAI state.
- Front-door docs simplified and aligned with code/config flags.

## Current Priorities

1. Create or restore `evals/team-real-prompts.jsonl`.
2. Run team-real prompts against staging.
3. Monitor OCI GenAI answer quality, fallback state, latency, and cost.
4. Monitor Oracle vector retrieval quality.
5. Add query embedding cache only if latency or repeated-query cost becomes material.

## Do Not Do Yet

- Do not change the embedding model again until the current v4 path has real usage history.
- Do not redesign the Oracle vector schema.
- Do not add LangGraph, autonomous agents, or persistent memory.
- Do not remove deterministic/local rollback paths.

## Validation Before Promotion

Run these before any meaningful runtime change:

```bash
python3 infra/scripts/smoke_oci_deployment.py \
  --api-base-url http://193.122.149.102:8000 \
  --frontend-url http://193.122.149.102:8000/

PYTHONPATH=app/backend/src app/backend/.venv/bin/python evals/run_golden.py \
  --cases evals/golden-prompts.jsonl \
  --output-dir evals/reports/golden

PYTHONPATH=app/backend/src app/backend/.venv/bin/python evals/run_golden.py \
  --cases evals/edge-cases.jsonl \
  --output-dir evals/reports/edge-cases

PYTHONPATH=app/backend/src app/backend/.venv/bin/python infra/scripts/retrieval_regression_check.py \
  --output-dir evals/reports/retrieval
```

## Source Of Truth

- Current runtime: [status.md](status.md)
- Architecture diagrams: [../architecture/architecture-diagrams.md](../architecture/architecture-diagrams.md)
- Retrieval rollback: [../runbooks/oci-native-retrieval-runbook.md](../runbooks/oci-native-retrieval-runbook.md)
- Operations: [../runbooks/operational-runbook.md](../runbooks/operational-runbook.md)
