# OCI Architecture Studio — Demo Readiness

Last updated: 2026-05-16

## Demo Readiness Checklist

| Area | Status | Notes |
|---|---|---|
| Backend API | Ready | `GET /health` and `POST /architecture-review` are working. |
| Frontend UI | Ready | Chat-style workflow includes demo prompt shortcuts, loading state, error state, structured results, and source cards. |
| Operations UI | Ready | Read-only Knowledge Refresh Status panel is visible at the top of the workspace and shows VM cron refresh state, gate result, Object Storage upload status, snapshot version, release-change count, affected-source count, and rollback posture. |
| Retrieval | Ready | Oracle AI Vector Search is active in staging with the 60-chunk architecture corpus; Object Storage and `local_json` remain tested rollback providers. |
| Release awareness | Ready for foundation demo | Release-watch refresh is active on the backend OCI VM cron path with live release fetch, quick gates, gated promotion, and Object Storage upload. Release-aware prompts still separate current release context from historical/local guidance. |
| Evals | Ready | Golden and edge-case evals pass. |
| Tests/build | Ready | Backend tests, frontend lint, and frontend build pass. |
| Known caveat | Accepted | OCI GenAI synthesis and OCI GenAI embeddings are optional rather than default; full current-vs-historical answer comparison remains deferred. |

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
Focused backend tests: 29 passed
Golden evals: 18 passed, 0 failed
Edge-case evals: 8 passed, 0 failed
Retrieval regression: 32 passed, 0 failed
Oracle AI Vector Search active-read validation: passed with cohere.embed-v4.0 at 1536 dimensions
Frontend build: passed
OCI staging smoke tests: passed
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
- Release source registry and release ingestion foundation.
- Freshness/staleness checks.
- CI workflow for tests, evals, ingestion smoke tests, and frontend build.
- OCI staging deployment.
- OCI Object Storage retrieval parity validation.
- OCI Object Storage retrieval promotion and rollback validation.
- Architecture diagrams and operational runbooks.

## Remaining Gaps

- `evals/team-real-prompts.jsonl` is not present yet, so that acceptance set still needs to be restored or created.
- Oracle AI Vector Search active reads are promoted and validated; Object Storage and the previous local-hash table remain rollback paths.
- OCI GenAI synthesis is active in staging with deterministic fallback design retained.
- Release impact analysis exists for snapshots and affected sources/chunks; release-watch refresh is live and gated, while full current-vs-historical answer comparison is not implemented.
- OCI corpus coverage is still small.
- Release parsing is heuristic-based.
- UI includes saved review history, section traceability, and review-history retention/export/delete controls.

## Technical Debt

- Local hash embeddings are useful only for deterministic workflow validation.
- Oracle documentation cleanup still needs stronger boilerplate removal.
- Eval checks are keyword/heuristic based and should become more evidence-aware.
- Source metadata needs source version/date and freshness policy per source.
- Release snapshot matching needs stronger service/entity extraction.

## Sprint 2 Backlog

1. Add dedicated OCI sources for WAF, Vault, Cloud Guard, Logging, Monitoring, Budgets, IAM, Audit, and Data Guard.
2. Restore or create `evals/team-real-prompts.jsonl` and run it against staging.
3. Keep Oracle AI Vector Search and Object Storage rollback snapshots aligned.
4. Monitor live OCI GenAI synthesis and embedding latency/cost before adding query embedding caching.
5. Add full current-vs-historical release comparison in release-aware responses.
6. Expand release-impact eval cases as the corpus grows.
7. Continue polishing frontend source cards, saved-review workflow, and export affordances.
8. Add HTTPS ingress for staging/demo.

## Top Risks

- Some recommendations may still sound template-driven while deterministic synthesis remains the default.
- Retrieval quality will degrade as the corpus grows without production embeddings.
- Release-awareness can still be misread as live intelligence unless the UI clearly marks snapshot-based context.
- OCI source coverage gaps can cause incomplete advice for security, observability, and DR scenarios.

## Next Highest-Value Build Block

The next highest-value block is **OCI GenAI synthesis parity**, run in shadow/evaluation mode without changing the deterministic default.

That moves answer quality forward while preserving the validated advisory workflow and rollback-safe deterministic synthesis path.
