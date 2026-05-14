# OCI Architecture Studio

## Purpose

OCI Architecture Studio is an AI-powered OCI architecture intelligence platform focused on:
- OCI architecture guidance
- migration advisory
- cost optimization
- release-aware knowledge synchronization

## Repo Layout

- `docs/` — product and architecture documentation
- `app/frontend/` — user interface
- `app/backend/` — API and orchestration
- `knowledge/` — ingestion, classification, refresh pipeline code
- `prompts/` — versioned prompt templates
- `evals/` — test prompts and regression cases
- `infra/` — deployment and CI/CD assets
- `tests/` — unit and integration tests

## Engineering Principles

- Keep the initial implementation simple and vertical-slice oriented.
- Prefer modular boundaries between retrieval, orchestration, API models, and UI.
- Treat prompts and evals as first-class source assets.
- Do not add full RAG, LangGraph, or advanced memory systems until the first grounded advisor flow is working and evaluated.
- Use type-safe models where appropriate, especially at API boundaries.
