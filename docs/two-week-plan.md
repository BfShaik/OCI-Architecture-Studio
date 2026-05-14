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
| 2026-05-15 | Convert golden prompts into a structured machine-readable eval file | `evals/golden-prompts.jsonl` or equivalent exists | Not Started |
| 2026-05-18 | Build a local eval runner for golden prompts | Command prints pass/fail for intent and expected traits | Not Started |
| 2026-05-19 | Add eval runner to backend tests or a repo-level script | Golden prompt regression can run in CI later | Not Started |
| 2026-05-20 | Improve ingestion cleanup for Oracle documentation pages | Retrieved chunks contain less boilerplate | In Progress |
| 2026-05-21 | Add source metadata to vector index | Chunks include fetched timestamp, source id, service domain, and intent tags | In Progress |
| 2026-05-22 | Expand source registry for priority gaps | Add WAF/CDN, Object Storage, Vault, Cloud Guard, Logging, Monitoring, Budgets | In Progress |
| 2026-05-25 | Improve frontend result cards | Source cards show title, score, intent, URL, and concise snippet | In Progress |
| 2026-05-26 | Add release-awareness scaffold | Add release source registry and a placeholder release-impact flow | In Progress |
| 2026-05-27 | Add CI skeleton | GitHub Actions runs backend tests and frontend build | Not Started |
| 2026-05-28 | Sprint review and backlog update | Status log, roadmap, and next sprint tasks are updated | Not Started |

## Status Notes

- 2026-05-20 ingestion cleanup is `In Progress`: script strips script/style/noscript/svg content, JavaScript warnings, and common Oracle footer markers. More boilerplate cleanup is still needed.
- 2026-05-21 source metadata is `In Progress`: the index includes generated timestamp, source id, title, URL, source type, chunk index, and fetch status. It still needs service domain, intent tags, per-source fetched timestamp, and freshness status.
- 2026-05-22 source expansion is `In Progress`: registry now includes OKE, database migration, Full Stack Disaster Recovery, Cost Management, and Security Services. It still needs WAF/CDN, Object Storage, Vault, Cloud Guard, Logging, Monitoring, and Budgets-specific sources.
- 2026-05-25 frontend result cards are `In Progress`: UI shows intent, prompt template, source title, source type, score, and snippet. It still needs clearer source cards, clickable URLs, better snippet trimming, and prompt history.
- 2026-05-26 release-awareness scaffold is `In Progress`: release-aware intent and prompt template exist. It still needs a release source registry, release ingestion, and actual impact comparison flow.

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
