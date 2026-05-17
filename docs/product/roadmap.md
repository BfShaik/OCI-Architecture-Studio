# Roadmap

This roadmap summarizes the current product path. Detailed task history lives in [../current/living-execution-plan.md](../current/living-execution-plan.md).

## Completed

### MVP Advisory Flow

- React/FastAPI app
- `/architecture-review` API
- typed response schema
- prompt templates
- local knowledge ingestion
- golden and edge evals
- citation display

### Grounded Retrieval

- local JSON retrieval
- OCI Object Storage retrieval
- Oracle AI Vector Search provider
- active Oracle vector retrieval in staging
- retrieval regression and parity checks
- rollback to Object Storage or local JSON

### OCI GenAI Synthesis

- OCI GenAI chat adapter
- retrieval-grounded prompt builder
- deterministic fallback
- GenAI parity/go-live validation
- staging promotion through `ADVISORY_SYNTHESIS_PROVIDER=oci_genai`

### OCI GenAI Embeddings

- OCI GenAI embedding adapter
- `cohere.embed-v4.0` active in staging
- 1536-dimension vector index
- embedding/index guardrail
- local-hash rollback manifest retained

### Advisory Experience

- controlled in-process orchestration
- validation critic
- section-level citations
- evidence links
- saved review history
- redaction/export/delete controls
- top-sticky prompt/options composer

### Operations

- OCI VM staging deployment
- health and retrieval health endpoints
- operational diagnostics
- release-watch cron path
- smoke scripts and eval runners
- version tag `v1.0.4`

## Current Focus

1. Keep staging stable on OCI GenAI synthesis and Oracle AI Vector Search.
2. Add or restore `evals/team-real-prompts.jsonl`.
3. Monitor GenAI quality, latency, cost, and fallback behavior.
4. Monitor v4 retrieval quality and decide whether query embedding caching is needed.
5. Keep docs and runbooks aligned with runtime changes.

## Future

- broader OCI corpus coverage
- richer release-aware comparison
- production HTTPS/domain hardening
- production HA/runtime hardening
- custom OCI Monitoring metrics
- OCI DevOps deployment automation
- richer topology visualization
- optional LLM-as-judge evaluation after deterministic gates stay stable

## Deferred

- LangGraph
- autonomous agent execution
- persistent agent memory
- new embedding model experiments before the current v4 path has real usage history
- Oracle vector schema redesign before current staging usage stabilizes
