# OCI Architecture Studio — Status Log

Last updated: 2026-05-14

## Active Plan

- Two-week plan: `docs/two-week-plan.md`

## Plan Progress

Current two-week task count:

| Status | Count | Percent of total |
|---|---:|---:|
| Done | 9 | 82% |
| In Progress | 1 | 9% |
| Not Started | 1 | 9% |
| Blocked | 0 | 0% |
| Total | 11 | 100% |

Strict completion:
- 9 of 11 tasks completed
- 82% complete

Started or partially complete:
- 10 of 11 tasks touched
- 91% started

Weighted progress estimate:
- Done tasks count as 100%
- In-progress tasks count as 50%
- Current weighted progress: 86%

This progress is based on `docs/two-week-plan.md`.

## Completed

- Created initial monorepo scaffold.
- Added FastAPI backend with:
  - `GET /health`
  - `POST /architecture-review`
  - typed request and response models
  - environment-based configuration
  - modular API, service, model, and config structure
- Added React + Vite frontend with:
  - chat-style architecture advisor UI
  - backend API integration
  - structured rendering for recommendations, assumptions, risks, sources, and next steps
  - demo prompt shortcuts
  - loading and error states
  - intent badges and citation metadata cards
- Added local RAG foundation:
  - OCI source registry
  - ingestion script
  - document fetching with offline fallback text
  - boilerplate cleanup
  - chunking
  - citation-ready chunk metadata
  - deterministic local embeddings
  - JSON vector index
  - cosine similarity retrieval
- Added release-awareness foundation:
  - OCI release source registry
  - release ingestion script
  - release classification by service, domain, impact tags, and impact level
  - separate release snapshot under `knowledge/snapshots/oci-release-snapshot.json`
  - freshness/staleness checks for retrieved sources and release-aware prompts
- Added intent-aware orchestration:
  - `product_overview`
  - `architecture`
  - `migration`
  - `dr`
  - `cost`
  - `security`
  - `release_awareness`
  - `general`
- Added intent-specific prompt templates under `prompts/`.
- Added golden prompt regression suite under `evals/golden-prompts.md`.
- Added machine-readable golden eval dataset under `evals/golden-prompts.jsonl`.
- Added edge-case eval dataset under `evals/edge-cases.jsonl`.
- Added local golden eval runner under `evals/run_golden.py`.
- Added evaluation architecture design under `docs/evaluation-architecture.md`.
- Added CI workflow under `.github/workflows/ci.yml`.
- Added backend tests for:
  - API health and architecture review
  - retrieval
  - intent classification
  - golden prompt intent-aware orchestration
  - ingestion cleanup and metadata generation
  - release ingestion and classification
  - stale-source detection
- Verified current validation:
  - backend tests pass
  - frontend build passes
  - golden prompts route to expected intents
  - golden eval runner passes 6 of 6 cases
  - edge-case eval runner passes 8 of 8 cases
  - eval runner now checks retrieval support and stale or unverified guidance
- Added demo readiness closeout under `docs/demo-readiness.md`.
- Renamed GitHub repository to `OCI-Architecture-Studio`.
- Pushed current implementation to GitHub.

## Pending

- Replace deterministic local hash embeddings with a production embedding provider when model/provider decisions are finalized.
- Add a production vector store adapter while keeping the current JSON vector store for local development.
- Expand OCI source coverage for:
  - dedicated WAF
  - dedicated Vault
  - dedicated Cloud Guard
  - dedicated Logging
  - dedicated Monitoring
  - Budgets-specific documentation
- Improve HTML ingestion quality to remove more documentation boilerplate.
- Add richer source metadata:
  - source version/date
  - per-service owners
  - source freshness policy
- Implement real release-awareness workflow:
  - architecture impact analysis
  - explicit current-vs-historical recommendation comparison
- Add stronger response generation:
  - actual prompt execution with an LLM
  - citation-aware answer synthesis
  - unsupported-claim checks
  - structured confidence or evidence notes
- Add frontend improvements:
  - prompt history
- Add deployment assets after the local vertical slice stabilizes.

## In Progress

- Ingestion cleanup:
  - common script/style/footer/help boilerplate cleanup exists
  - more Oracle documentation boilerplate cleanup is still needed
- Source metadata:
  - current index includes source URL, service, service domain, intent tags, fetched timestamp, freshness score, trust level, architecture patterns, chunk index, and fetch status
  - still needs source version/date and richer ownership metadata
- Source registry expansion:
  - added OKE, database migration, Full Stack Disaster Recovery, Cost Management, Security Services, Object Storage, and CDN / edge services
  - still needs dedicated WAF, Vault, Cloud Guard, Logging, Monitoring, and Budgets-specific sources
- Release-awareness scaffold:
  - release-aware intent, prompt template, release registry, release ingestion, and release snapshot reader exist
  - impact comparison is not implemented yet

## Current Known Limitations

- The local RAG index is small and not a complete OCI documentation corpus.
- Embeddings are deterministic local hash embeddings, useful for workflow validation but not production semantic retrieval.
- Release awareness has a local release snapshot foundation, but it is not yet a full live release intelligence workflow.
- The backend returns intent-profiled recommendations, but full LLM-based synthesis is not implemented yet.
- Generated vector snapshots are local and gitignored.
