# Sprint Current

## Sprint Goal

Maintain the validated OCI Architecture Studio staging baseline while advancing Sprint 2 retrieval promotion safely.

The current state uses `oci_object_storage` as the active staging retrieval provider after controlled config-only promotion. `local_json` remains the validated rollback provider. Oracle AI Vector Search remains guarded until schema, indexing, and live query parity are validated.

## Timebox

2 weeks

## Current Priorities

1. Monitor the promoted `oci_object_storage` staging provider
2. Improve advisory intelligence quality and confidence reporting
3. Expand source registry for WAF, Vault, Cloud Guard, Logging, Monitoring, Budgets, IAM, Audit, and Data Guard
4. Add vector-search dual-run parity against the Object Storage provider
5. Keep release-awareness snapshot flow honest and clearly point-in-time
6. Add HTTPS ingress plan for staging/demo readiness

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
- Status and two-week tracking docs
- first OCI landing-zone Terraform scaffold
- deployment scripts, smoke tests, and staging workflow
- dual-provider retrieval parity validation
- Object Storage retrieval promotion and rollback validation
- evidence-linked recommendations and confidence scoring
- advisory-quality eval suite

Out of scope:
- production RAG/vector database cutover
- LangGraph
- advanced memory systems
- production ingestion jobs beyond local CLI and Object Storage snapshots
- production-grade cloud deployment beyond the current staging slice
- HTTPS ingress and HA cloud runtime

## Demo Readiness

See `docs/demo-readiness.md` for the demo checklist, recommended prompts, Sprint 2 backlog, and closeout notes.

## Phase 2 Planning

See `docs/phase-2-architecture.md` for the productionization architecture, scalability roadmap, and recommended Sprint 2 implementation order.

## Status

See `docs/status.md` for the current completed/pending log.

Latest full validation on 2026-05-15 passed locally and in OCI staging:

- backend tests: `30 passed`
- golden evals: `6 passed`
- edge-case evals: `8 passed`
- retrieval regression: `14 passed`
- advisory-quality evals: `5 passed`
- frontend build: passed
- Terraform validation: passed for `dev`, `test`, and `staging`
- staging smoke and resource visibility checks: passed

## Two-Week Plan

See `docs/two-week-plan.md` for dated tasks from 2026-05-14 through 2026-05-28.
