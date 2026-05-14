# OCI Architecture Studio — Two-Week Plan

Plan window: 2026-05-14 to 2026-05-28

## Goal

Turn the current local RAG and intent-aware prototype into a stronger evaluation-driven foundation with cleaner ingestion, automated golden prompt checks, and a clearer path toward production retrieval.

## Tracking Legend

- `Not Started`
- `In Progress`
- `Done`
- `Blocked`

## Plan

| Date | Task | Outcome | Status |
|---|---|---|---|
| 2026-05-14 | Create project status log and two-week execution plan | Completed/pending work is visible in docs | Done |
| 2026-05-15 | Convert golden prompts into a structured machine-readable eval file | `evals/golden-prompts.jsonl` or equivalent exists | Done |
| 2026-05-18 | Build a local eval runner for golden prompts | Command prints pass/fail for intent and expected traits | Done |
| 2026-05-19 | Add eval runner to backend tests or a repo-level script | Golden prompt regression can run in CI later | Done |
| 2026-05-20 | Improve ingestion cleanup for Oracle documentation pages | Retrieved chunks contain less boilerplate | Done |
| 2026-05-21 | Add source metadata to vector index | Chunks include fetched timestamp, source id, service domain, and intent tags | Done |
| 2026-05-22 | Expand source registry for priority gaps | Add WAF/CDN, Object Storage, Vault, Cloud Guard, Logging, Monitoring, Budgets | In Progress |
| 2026-05-25 | Improve frontend result cards | Source cards show title, score, intent, URL, and concise snippet | Done |
| 2026-05-26 | Add release-awareness scaffold | Add release source registry and a placeholder release-impact flow | Done |
| 2026-05-27 | Add CI skeleton | GitHub Actions runs backend tests and frontend build | Done |
| 2026-05-28 | Sprint review and backlog update | Status log, roadmap, and next sprint tasks are updated | Done |

## Status Notes

- Current task count: 10 Done, 1 In Progress, 0 Not Started, 0 Blocked.
- Strict completion: 10 of 11 tasks, or 91%.
- Started or partially complete: 11 of 11 tasks, or 100%.
- Weighted progress estimate: 95%, counting `Done` as 100% and `In Progress` as 50%.
- 2026-05-15 structured golden evals are `Done`: `evals/golden-prompts.jsonl` exists.
- 2026-05-18 local eval runner is `Done`: `evals/run_golden.py` executes prompts and writes JSON/Markdown reports. Current suites pass 14 of 14 cases.
- 2026-05-19 eval runner integration is `Done`: the repo-level script is included in CI.
- 2026-05-20 ingestion cleanup is `Done`: script strips script/style/noscript/svg content, JavaScript warnings, footer markers, and common navigation/help text.
- 2026-05-21 source metadata is `Done`: the index includes source URL, service, service domain, intent tags, fetched timestamp, freshness score, trust level, architecture patterns, chunk index, and fetch status.
- 2026-05-22 source expansion is `In Progress`: registry now includes OKE, database migration, Full Stack Disaster Recovery, Cost Management, Security Services, Object Storage, and CDN / edge services. It still needs dedicated WAF, Vault, Cloud Guard, Logging, Monitoring, and Budgets-specific sources.
- 2026-05-25 frontend result cards are `Done`: UI shows intent, prompt template, source title, service, domain, source type, score, freshness, trust level, source URL, source tags, and snippet. Prompt history remains a Sprint 2 item.
- 2026-05-26 release-awareness scaffold is `Done`: release-aware intent, prompt template, release source registry, release ingestion, release classification, and release snapshot reader exist. Actual impact comparison remains future work.
- 2026-05-27 CI skeleton is `Done`: `.github/workflows/ci.yml` runs ingestion smoke test, backend tests, golden evals, and frontend build.
- 2026-05-28 sprint review and backlog update is `Done`: status, roadmap, demo closeout, Phase 2 architecture, and OCI deployment execution docs are current.

## Priority Order

1. Golden prompt eval runner
2. Ingestion quality
3. Source metadata and source expansion
4. Frontend clarity
5. CI skeleton
6. Release-awareness scaffold

## Risks

- Oracle documentation pages may include layout/navigation boilerplate that lowers retrieval quality.
- The local hashing embedder is useful for workflow validation but may produce weak semantic ranking for nuanced prompts.
- Release-awareness must not pretend to be current until live release sources and freshness metadata are implemented.

## Review Cadence

- Update task status whenever a task starts or completes.
- Add new tasks only when a real failure or gap appears.
- Keep this plan small enough to finish within the two-week window.
