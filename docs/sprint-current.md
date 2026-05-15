# Sprint Current

## Sprint Goal

Build the first working OCI Architecture Studio vertical slice with local RAG, intent-aware orchestration, golden/edge regression, release-awareness foundation, demo-ready UI, and a validated first OCI deployment scaffold.

Sprint 2 has started with an incremental OCI-native retrieval migration. The first slice keeps `local_json` as the default while adding OCI embedding/Object Storage hooks, a guarded Oracle AI Vector Search boundary, metadata-aware ranking, and retrieval regression checks.

## Timebox

2 weeks

## Current Priorities

1. Convert golden prompts to structured evals
2. Build local eval runner
3. Improve ingestion cleanup
4. Add source metadata
5. Expand source registry
6. Improve frontend result cards
7. Add CI skeleton
8. Add release-awareness foundation
9. Prepare demo readiness closeout
10. Prepare first OCI deployment execution scaffold

## Sprint Scope

In scope:
- FastAPI backend with health and architecture review endpoints
- React + Vite chat-style interface
- Local RAG index with source-shaped records
- citation-friendly retrieval metadata
- Intent-aware orchestration with structured response
- release source registry and release snapshot prototype
- Prompt templates and golden prompt assets
- edge-case evals and validation reports
- demo prompt shortcuts and polished source cards
- Status and two-week tracking docs
- first OCI landing-zone Terraform scaffold
- deployment scripts, smoke tests, and staging workflow

Out of scope:
- production RAG/vector database cutover
- LangGraph
- advanced memory systems
- production ingestion jobs beyond local CLI snapshots
- production-grade cloud deployment beyond the current staging slice
- HTTPS ingress and HA cloud runtime

## Demo Readiness

See `docs/demo-readiness.md` for the demo checklist, recommended prompts, Sprint 2 backlog, and closeout notes.

## Phase 2 Planning

See `docs/phase-2-architecture.md` for the productionization architecture, scalability roadmap, and recommended Sprint 2 implementation order.

## Status

See `docs/status.md` for the current completed/pending log.

Latest full validation on 2026-05-15 passed locally and in OCI staging:

- backend tests: `29 passed`
- golden evals: `6 passed`
- edge-case evals: `8 passed`
- retrieval regression: `14 passed`
- frontend build: passed
- Terraform validation: passed for `dev`, `test`, and `staging`
- staging smoke and resource visibility checks: passed

## Two-Week Plan

See `docs/two-week-plan.md` for dated tasks from 2026-05-14 through 2026-05-28.
