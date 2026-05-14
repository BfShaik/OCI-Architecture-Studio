# Roadmap

## Phase 1 — MVP Foundation
Status: In Progress

Deliverables:
- monorepo setup — Done
- README and AGENTS — Done
- backend scaffold — Done
- frontend scaffold — Done
- prompt templates — Done
- first OCI knowledge ingestion — Done
- first architecture advisor flow — Done
- local RAG index — Done
- intent-aware orchestration — Done
- golden prompt suite — Done
- project status and two-week plan — Done
- edge-case eval suite — Done
- demo readiness checklist — Done

Exit criteria:
- A user can submit an OCI architecture question through the UI. — Done
- The backend returns a structured response through local retrieval and intent-aware orchestration. — Done
- The response includes intent, prompt template, assumptions, recommendations, risks, citations, and next steps. — Done
- Golden prompts capture expected behavior for core product intents. — Done
- A machine-readable eval runner exists. — Done

## Phase 2 — Grounded Retrieval
Status: In Progress

Architecture plan: `docs/phase-2-architecture.md`

Deliverables:
- curated seed corpus — In Progress
- document chunking — Done
- metadata model — Done
- local retrieval adapter — Done
- citation display — Done
- regression evals for grounded answers — Done
- production embedding provider — Pending
- production vector store adapter — Pending

## Phase 3 — Release-Aware Knowledge
Status: Scaffolded

Deliverables:
- OCI release source registry — Done
- refresh job scaffold — Done
- snapshot freshness metadata — Done
- change classification — MVP Done
- release impact summaries — Pending
- stale-knowledge warnings — MVP Done
