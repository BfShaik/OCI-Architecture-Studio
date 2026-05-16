# OCI Architecture Studio — Two-Week Plan Archive

Plan window: 2026-05-14 to 2026-05-28

## Goal

Completed the original foundation sprint and extended it into a validated staging baseline with OCI deployment, release-awareness, retrieval regression, Object Storage active retrieval, Oracle AI Vector Search shadow validation, and operational visibility.

This file is now an archive. Current work should be tracked in `docs/current/living-execution-plan.md`.

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
| 2026-05-22 | Expand source registry for priority gaps | Added WAF/CDN, Object Storage, Vault, Cloud Guard, Logging, Monitoring, Budgets, IAM, Audit, and other priority OCI sources; broader corpus expansion continues in the living plan | Done |
| 2026-05-25 | Improve frontend result cards | Source cards show title, score, intent, URL, and concise snippet | Done |
| 2026-05-26 | Add release-awareness scaffold | Add release source registry and a placeholder release-impact flow | Done |
| 2026-05-27 | Add CI skeleton | GitHub Actions runs backend tests and frontend build | Done |
| 2026-05-28 | Sprint review and backlog update | Status log, roadmap, and next sprint tasks are updated | Done |

## Closeout Notes

- Final task count: 11 Done, 0 In Progress, 0 Not Started, 0 Blocked.
- Strict completion: 11 of 11 tasks, or 100%.
- The remaining work is no longer part of this two-week archive; it is tracked in `docs/current/living-execution-plan.md`.
- 2026-05-15 structured golden evals are `Done`: `evals/golden-prompts.jsonl` exists.
- 2026-05-18 local eval runner is `Done`: `evals/run_golden.py` executes prompts and writes JSON/Markdown reports. Current suites pass 14 of 14 cases.
- 2026-05-19 eval runner integration is `Done`: the repo-level script is included in CI.
- 2026-05-20 ingestion cleanup is `Done`: script strips script/style/noscript/svg content, JavaScript warnings, footer markers, and common navigation/help text.
- 2026-05-21 source metadata is `Done`: the index includes source URL, service, service domain, intent tags, fetched timestamp, freshness score, trust level, architecture patterns, chunk index, and fetch status.
- 2026-05-22 source expansion is `Done` for the original sprint scope: the registry now includes priority OCI architecture, networking, compute, storage, database, security, observability, cost, DevOps, data/AI, and reference architecture sources. Broader official OCI corpus expansion remains a future enterprise-beta task.
- 2026-05-25 frontend result cards are `Done`: UI shows intent, prompt template, source title, service, domain, source type, score, freshness, trust level, source URL, source tags, and snippet. Prompt history remains a future UX item.
- 2026-05-26 release-awareness scaffold is `Done`: release-aware intent, prompt template, release source registry, release ingestion, release classification, release snapshot reader, deterministic impact analysis, and affected source/chunk reporting exist. Full live release reconciliation remains future work.
- 2026-05-27 CI skeleton is `Done`: `.github/workflows/ci.yml` runs ingestion smoke test, backend tests, golden evals, and frontend build. Operational scheduling and deployment orchestration are not handled by GitHub Actions.
- 2026-05-28 sprint review and backlog update is `Done`: status, roadmap, demo closeout, Phase 2 architecture, and OCI deployment execution docs are current.
- Post-plan update: OCI staging deployment is live and validated behind OCI API Gateway, with direct VM rollback preserved.
- Post-plan update: `oci_object_storage` retrieval parity passed against `local_json`, staging promotion completed, and rollback to `local_json` was validated.
- Post-plan update: Oracle AI Vector Search shadow infrastructure, table/index, sync, and parity validation are complete; active reads remain gated in the living plan.
- Post-plan update: release-watch refresh runs on the OCI backend VM cron path with gated promotion and Object Storage upload; stable-doc refresh remains conservative.
- Post-plan update: the Knowledge Refresh Status UI panel is implemented, staged, and documented.

## Follow-On Priority Order

The original two-week plan is complete. Follow-on priorities are tracked in `docs/current/living-execution-plan.md`:

1. Document the ingestion-to-retrieval flow.
2. Add Retrieval Provider Status UI.
3. Expand official OCI corpus coverage.
4. Run OCI GenAI embedding shadow/parity activation.
5. Promote Oracle AI Vector Search active reads only after parity and rollback gates pass.

## Risks

- Oracle documentation pages may include layout/navigation boilerplate that lowers retrieval quality.
- The local hashing embedder is useful for workflow validation but may produce weak semantic ranking for nuanced prompts.
- Release-awareness must not pretend to be live intelligence until watcher, impact analysis, and selective reindexing are implemented.
- Oracle AI Vector Search should not become active until it passes parity against the Object Storage provider.

## Review Cadence

- Do not add new work to this archive.
- Use `docs/current/living-execution-plan.md` for current task status.
- Update this archive only if correcting historical facts.
