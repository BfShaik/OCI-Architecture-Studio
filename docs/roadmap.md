# Roadmap

## Phase 1 — MVP Foundation
Status: Planned

Deliverables:
- monorepo setup
- README and AGENTS
- backend scaffold
- frontend scaffold
- prompt templates
- first OCI knowledge ingestion
- first architecture advisor flow

Exit criteria:
- A user can submit an OCI architecture question through the UI.
- The backend returns a structured response through retrieval and orchestration placeholders.
- The response includes assumptions, recommendations, risks, citations, and next steps.
- At least one eval fixture captures expected behavior for the vertical slice.

## Phase 2 — Grounded Retrieval
Status: Planned

Deliverables:
- curated seed corpus
- document chunking and metadata model
- local retrieval adapter
- citation enforcement
- regression evals for grounded answers

## Phase 3 — Release-Aware Knowledge
Status: Planned

Deliverables:
- OCI source registry
- refresh job scaffold
- snapshot metadata
- change classification
- release impact summaries
