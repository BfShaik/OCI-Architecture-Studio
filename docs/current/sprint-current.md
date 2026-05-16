# Sprint Current

## Sprint Goal

Maintain the validated OCI Architecture Studio staging baseline while advancing enterprise-beta retrieval, knowledge refresh, and operational visibility safely.

The current state uses `oracle_ai_vector_search` as the active staging retrieval provider after gated promotion. Object Storage remains the immediate config-only rollback provider, `local_json` remains the local fallback provider, and `RETRIEVAL_FALLBACK_ENABLED=true` is retained on staging.

## Timebox / Status

The original two-week sprint is complete and archived in `docs/archive/two-week-plan.md`. Current work is now managed through the living enterprise-beta plan in `docs/current/living-execution-plan.md`.

## Current Priorities

1. Keep the Knowledge Refresh Status panel and `/knowledge/refresh/status` aligned with the OCI VM cron path.
2. Keep Oracle AI Vector Search active reads healthy while preserving the Object Storage rollback path.
3. Add OCI Monitoring custom metrics for refresh/gate health.

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
- Retrieval Provider Status UI panel
- beginner-friendly ingestion-to-retrieval operator flow documentation
- Oracle AI Vector Search active-read staging promotion and rollback validation
- executive and architecture-review advisory response layout refinement
- explainability UI for retrieval, governance, release-awareness, service selection, rejected alternatives, and confidence scoring
- release-context advisory UI with release matches, affected services, snapshot timing, temporal boundary, and maturity notes
- architecture map UI with topology summaries, lane-based service relationships, implementation path, and operational notes
- OCI architecture accuracy corpus and retrieval tuning for landing zones, EKS-to-OKE migration, database DR, analytics platforms, and observability
- secure saved review history and prompt/session recall
- section-level citation traceability with source-indexed recommendation evidence
- evidence-linked recommendations and confidence scoring
- advisory-quality eval suite

Out of scope:
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

- backend tests: `132 passed`
- frontend lint: passed
- frontend build: passed
- Terraform validation: passed for `dev`, `test`, and `staging`
- staging smoke passed through OCI API Gateway and direct VM rollback path
- active staging retrieval: `oracle_ai_vector_search`
- current registry corpus: 60 chunks/sources
- active staging retrieval snapshot: 60 chunks
- latest promoted release-watch refresh: 12 live release items
- Oracle AI Vector Search: active on staging with 60 chunks, fallback enabled but inactive; regression, smoke, prompt-level accuracy checks, and hash guardrails passed
- advisory UI: Decision Snapshot, priority cards, implementation exit criteria, comparison evidence, recommendation-confidence cards, and tradeoff cards are deployed to staging
- explainability UI: dedicated influence cards, service-selection rationale, rejected alternatives, mapped services, domain signals, and selected evidence labels are deployed to staging
- release-context UI: polished advisory panel is deployed to staging and passed local lint/build, backend tests, retrieval regression, local smoke, staging direct/API Gateway smoke, retrieval health, hash guardrails, and browser smoke
- architecture map UI: deployed to staging and passed local lint/build, focused topology/API tests, backend full suite, retrieval regression, local smoke, staging direct/API Gateway smoke, retrieval health, hash guardrails, and browser smoke
- OCI architecture accuracy: landing-zone, EKS-to-OKE, and database DR evals are in regression; live Gateway landing-zone evidence now prioritizes IAM, VCN, Vault, Cloud Guard, Audit, and Logging
- saved review history: redacted file-backed history APIs and left-rail UI are deployed to staging; validation traffic opts out of persistence, and local/staging tests, direct/API Gateway smoke, Gateway history redaction/delete smoke, and staging browser smoke passed
- section citation traceability: enriched section citation metadata and UI passed backend tests, frontend lint/build, retrieval regression, golden evals, architecture-realism evals, local browser smoke, staging focused tests, direct/gateway smoke, gateway traceability validation, and staging browser smoke
- OCI GenAI synthesis: implemented and configurable, not default
- OCI GenAI embeddings: `cohere.embed-v4.0` shadow candidate validated at 256 dimensions, not default

## Two-Week Plan Archive

See `docs/archive/two-week-plan.md` for the completed dated tasks from 2026-05-14 through 2026-05-28. It is no longer the active work tracker.

## Working In Progress List

The active WIP list now lives in `docs/current/living-execution-plan.md` under **Work In Progress / Not Yet Implemented**. Keep that list authoritative for the next small task.
