# Sprint Current

## Sprint Goal

Maintain the validated OCI Architecture Studio staging baseline while advancing enterprise-beta retrieval, knowledge refresh, and operational visibility safely.

The current state uses `oci_object_storage` as the active staging retrieval provider after controlled config-only promotion. `local_json` remains the validated rollback provider. Oracle AI Vector Search is shadow-loaded and validated, but active reads remain gated until final parity, regression, smoke, operational readiness, and rollback checks pass.

## Timebox / Status

The original two-week sprint is complete and archived in `docs/archive/two-week-plan.md`. Current work is now managed through the living enterprise-beta plan in `docs/current/living-execution-plan.md`.

## Current Priorities

1. Keep the Knowledge Refresh Status panel and `/knowledge/refresh/status` aligned with the OCI VM cron path.
2. Add a beginner-friendly ingestion-to-retrieval flow doc section.
3. Add a read-only Retrieval Provider Status panel for active provider, chunk count, Object Storage source, fallback status, and Oracle vector shadow posture.
4. Expand the curated official OCI corpus beyond 47 sources.
5. Run OCI GenAI embeddings in shadow/parity mode before any embedding promotion.
6. Promote Oracle AI Vector Search active reads only after refreshed parity and rollback gates pass.
7. Add OCI Monitoring custom metrics for refresh/gate health.

## Sprint Scope

In scope:
- FastAPI backend with health and architecture review endpoints
- React + Vite chat-style interface
- Local RAG index with source-shaped records
- citation-friendly retrieval metadata
- Intent-aware orchestration with structured response
- release source registry and release snapshot foundation
- Prompt templates and golden prompt assets
- edge-case evals and validation reports
- demo prompt shortcuts and polished source cards
- Status and living execution plan docs
- first OCI landing-zone Terraform scaffold
- deployment scripts, smoke tests, and staging workflow
- dual-provider retrieval parity validation
- Object Storage retrieval promotion and rollback validation
- backend OCI VM cron release-watch refresh with gated Object Storage upload
- Knowledge Refresh Status UI panel
- Oracle AI Vector Search shadow table/index and sync validation
- evidence-linked recommendations and confidence scoring
- advisory-quality eval suite

Out of scope:
- Oracle AI Vector Search active-read cutover until promotion gates pass
- LangGraph
- advanced memory systems
- external schedulers or GitHub Actions for operational orchestration
- production-grade HA cloud runtime
- live OCI GenAI default mode before parity validation

## Demo Readiness

See `docs/current/demo-readiness.md` for the demo checklist, recommended prompts, backlog, and closeout notes.

## Phase 2 Planning

See `docs/architecture/phase-2-architecture.md` for the productionization architecture and scalability roadmap. Use `docs/current/living-execution-plan.md` for the current implementation order.

## Status

See `docs/current/status.md` for the current completed/pending log.

Latest validation/current posture:

- backend tests: `129 passed`
- frontend lint: passed
- frontend build: passed
- Terraform validation: passed for `dev`, `test`, and `staging`
- staging smoke passed through OCI API Gateway and direct VM rollback path
- active staging retrieval: `oci_object_storage`
- current corpus: 47 chunks/sources
- latest promoted release-watch refresh: 12 live release items
- Oracle AI Vector Search: shadow-loaded and validated, not active
- OCI GenAI synthesis/embeddings: implemented and configurable, not default

## Two-Week Plan Archive

See `docs/archive/two-week-plan.md` for the completed dated tasks from 2026-05-14 through 2026-05-28. It is no longer the active work tracker.

## Working In Progress List

The active WIP list now lives in `docs/current/living-execution-plan.md` under **Work In Progress / Not Yet Implemented**. Keep that list authoritative for the next small task.
