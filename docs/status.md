# OCI Architecture Studio — Status Log

Last updated: 2026-05-14

## Active Plan

- Two-week plan: `docs/two-week-plan.md`

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
- Added local RAG foundation:
  - OCI source registry
  - ingestion script
  - document fetching with offline fallback text
  - chunking
  - deterministic local embeddings
  - JSON vector index
  - cosine similarity retrieval
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
- Added backend tests for:
  - API health and architecture review
  - retrieval
  - intent classification
  - golden prompt intent-aware orchestration
- Verified current validation:
  - backend tests pass
  - frontend build passes
  - golden prompts route to expected intents
- Renamed GitHub repository to `OCI-Architecture-Studio`.
- Pushed current implementation to GitHub.

## Pending

- Add an automated eval runner that reads `evals/golden-prompts.md` or a structured eval file and produces pass/fail output.
- Replace deterministic local hash embeddings with a production embedding provider when model/provider decisions are finalized.
- Add a production vector store adapter while keeping the current JSON vector store for local development.
- Expand OCI source coverage for:
  - OKE
  - database migration
  - Object Storage
  - CDN / edge / WAF
  - Vault
  - Cloud Guard
  - Logging
  - Monitoring
  - Full Stack Disaster Recovery
  - Cost Analysis and Budgets
- Improve HTML ingestion quality to remove more documentation boilerplate.
- Add source metadata:
  - fetched timestamp
  - source version/date
  - service domain
  - intent tags
  - freshness status
- Implement real release-awareness workflow:
  - approved release source registry
  - release note ingestion
  - change classification
  - architecture impact analysis
  - stale-knowledge warnings
- Add stronger response generation:
  - actual prompt execution with an LLM
  - citation-aware answer synthesis
  - unsupported-claim checks
  - structured confidence or evidence notes
- Add frontend improvements:
  - clearer source cards
  - intent badge
  - loading states
  - error recovery
  - prompt history
- Add CI:
  - backend tests
  - frontend build
  - ingestion smoke test
  - golden prompt regression check
- Add deployment assets after the local vertical slice stabilizes.

## In Progress

- Ingestion cleanup:
  - basic HTML cleanup exists
  - more Oracle documentation boilerplate cleanup is still needed
- Source metadata:
  - current index includes generated timestamp, source id, title, URL, source type, chunk index, and fetch status
  - still needs service domain, intent tags, per-source fetched timestamp, and freshness status
- Source registry expansion:
  - added OKE, database migration, Full Stack Disaster Recovery, Cost Management, and Security Services
  - still needs WAF/CDN, Object Storage, Vault, Cloud Guard, Logging, Monitoring, and Budgets-specific sources
- Frontend result cards:
  - current UI shows intent, prompt template, source title, source type, score, and snippet
  - still needs clickable URLs, cleaner source cards, and prompt history
- Release-awareness scaffold:
  - release-aware intent and prompt template exist
  - release ingestion and impact comparison are not implemented yet

## Current Known Limitations

- The local RAG index is small and not a complete OCI documentation corpus.
- Embeddings are deterministic local hash embeddings, useful for workflow validation but not production semantic retrieval.
- Release awareness is currently intent-safe but not truly current; it asks for current release context rather than fetching live updates automatically.
- The backend returns intent-profiled recommendations, but full LLM-based synthesis is not implemented yet.
- Generated vector snapshots are local and gitignored.
