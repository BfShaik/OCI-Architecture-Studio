# OCI Architecture Studio — Demo Readiness

Last updated: 2026-05-14

## Demo Readiness Checklist

| Area | Status | Notes |
|---|---|---|
| Backend API | Ready | `GET /health` and `POST /architecture-review` are working. |
| Frontend UI | Ready | Chat-style workflow includes demo prompt shortcuts, loading state, error state, structured results, and source cards. |
| Retrieval | Ready for MVP demo | Local OCI chunks include service, domain, intent tags, trust level, freshness score, and source URLs. |
| Release awareness | Ready for foundation demo | Release snapshot ingestion exists and release-aware prompts separate current-release context from local historical guidance. |
| Evals | Ready | Golden and edge-case evals pass. |
| Tests/build | Ready | Backend tests and frontend build pass. |
| Known caveat | Accepted | No full LLM synthesis, production embeddings, production vector store, or live release-impact comparison yet. |

## Recommended Demo Prompts

### 1. Basic OCI Architecture

Prompt:

```text
Design a highly available ecommerce platform on OCI.
```

Why this is a good demo:
- Exercises architecture intent.
- Shows multi-tier guidance, HA thinking, Object Storage/CDN context, and source citations.

Expected intent:
- `architecture`

Good response should include:
- storefront or web tier
- load balancing
- protected database tier
- Object Storage or CDN for static/catalog content
- assumptions, risks, next steps, and cited OCI sources

### 2. Migration

Prompt:

```text
Migrate EKS + RDS to OCI.
```

Why this is a good demo:
- Demonstrates cloud-to-cloud migration mapping.
- Verifies EKS-to-OKE and RDS-to-OCI database guidance.

Expected intent:
- `migration`

Good response should include:
- EKS to OCI Kubernetes Engine mapping
- RDS to OCI database target discovery
- migration waves
- dependency mapping
- validation and rollback

### 3. HA/DR

Prompt:

```text
Recommend OCI services for fintech DR.
```

Why this is a good demo:
- Shows resilience-specific routing instead of generic architecture advice.
- Surfaces compliance, audit, RTO/RPO, and runbook language.

Expected intent:
- `dr`

Good response should include:
- RTO/RPO tiers
- cross-region design
- Data Guard or database protection patterns
- DNS/failover, Vault, Logging, Monitoring
- compliance and audit considerations

### 4. Cost Optimization

Prompt:

```text
Build a cost-optimized web app on OCI.
```

Why this is a good demo:
- Shows cost intent and concrete optimization levers.
- Verifies the app does not recommend disabling required resilience controls.

Expected intent:
- `cost`

Good response should include:
- rightsizing
- autoscaling
- Object Storage where appropriate
- budgets, tagging, and usage monitoring
- backup and monitoring tradeoffs

### 5. Release Awareness

Prompt:

```text
A new OCI Object Storage release was announced. Does it change my architecture?
```

Why this is a good demo:
- Shows the new release-awareness foundation.
- Demonstrates that the app separates local knowledge from release context.

Expected intent:
- `release_awareness`

Good response should include:
- caution before declaring current impact
- matching Object Storage release context
- instruction to compare release snapshots with normal knowledge
- no unsupported claim that the latest release definitely changes the architecture

## Final Validation Summary

Latest local validation:

```text
Knowledge ingestion: passed
Release ingestion: passed
Backend tests: 22 passed
Golden evals: 6 passed, 0 failed
Edge-case evals: 8 passed, 0 failed
Frontend build: passed
API smoke tests: passed
```

## Completed In This Sprint

- Initial monorepo scaffold.
- FastAPI backend with typed API models.
- React/Vite frontend with structured architecture-review UI.
- Local OCI RAG ingestion and retrieval.
- Intent-aware orchestration.
- Golden and edge-case eval suites.
- Evaluation runner with Markdown/JSON reports.
- Citation-friendly retrieval metadata.
- Release source registry and release ingestion prototype.
- Freshness/staleness checks.
- CI workflow for tests, evals, ingestion smoke tests, and frontend build.

## Remaining Gaps

- Production semantic embeddings are not implemented.
- Production vector store is not implemented.
- Full LLM-based synthesis is not implemented.
- Release impact comparison is not implemented.
- OCI corpus coverage is still small.
- Release parsing is heuristic-based.
- UI does not yet include prompt history or saved reviews.

## Technical Debt

- Local hash embeddings are useful only for deterministic workflow validation.
- Oracle documentation cleanup still needs stronger boilerplate removal.
- Eval checks are keyword/heuristic based and should become more evidence-aware.
- Source metadata needs source version/date and freshness policy per source.
- Release snapshot matching needs stronger service/entity extraction.

## Sprint 2 Backlog

1. Add dedicated OCI sources for WAF, Vault, Cloud Guard, Logging, Monitoring, Budgets, IAM, Audit, and Data Guard.
2. Replace local hash embeddings with the selected production embedding provider.
3. Add a production vector store adapter while keeping JSON local mode.
4. Implement citation-aware LLM synthesis with strict grounding instructions.
5. Add release impact comparison between release snapshots and architecture recommendations.
6. Add release-impact eval cases.
7. Improve frontend source cards with grouped evidence and prompt history.
8. Add deployment/devcontainer or local setup automation.

## Top Risks

- Recommendations may still sound template-driven until LLM synthesis is added.
- Retrieval quality will degrade as the corpus grows without production embeddings.
- Release-awareness can still be misread as live intelligence unless the UI clearly marks snapshot-based context.
- OCI source coverage gaps can cause incomplete advice for security, observability, and DR scenarios.

## Next Highest-Value Build Block

The next highest-value block is **citation-aware LLM synthesis backed by production embeddings**.

That gives the demo a more natural advisory response while keeping the evaluation and citation guardrails already built in this sprint.
