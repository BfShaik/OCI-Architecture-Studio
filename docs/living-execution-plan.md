# OCI Architecture Studio — Living Execution Plan

Last updated: 2026-05-16

## Purpose

This document is the active execution plan for moving OCI Architecture Studio from the `v1.0.1` internal beta baseline toward a stronger OCI-native enterprise beta. It is intentionally living: update it whenever a promotion gate passes, a gap is retired, or a new risk is discovered.

The plan favors OCI-native services, Terraform-managed infrastructure, deterministic fallback, local development compatibility, and small explainable increments. It does not introduce autonomous agents, hidden SaaS dependencies, external schedulers, external vector databases, GitHub Actions-based operational orchestration, or heavyweight workflow engines.

## Current Baseline

| Area | Current position | Baseline decision |
|---|---|---|
| Git baseline | `main` is the active branch. Current pushed closeout commit is `0a40470` with the Knowledge Refresh Status panel documented and deployed to staging. | Treat the latest pushed `main` commit and existing version tags as recovery points; do not move existing tags. |
| Retrieval | Staging uses `oci_object_storage` with `local_json` fallback. Oracle AI Vector Search is live, schema-loaded, and shadow-validated, but active DB-backed retrieval is not promoted. | Keep Object Storage active until refresh stability and refreshed vector parity pass. |
| Synthesis | Deterministic synthesis is default. OCI GenAI synthesis exists behind configuration and fails closed to deterministic fallback. | Keep deterministic default until live GenAI parity passes. |
| Embeddings | Deterministic local embeddings are the stable path. OCI GenAI embeddings are configurable but not the default. | Activate in shadow/parity mode before promotion. |
| Runtime | OCI VM staging is active behind OCI API Gateway, with direct VM rollback preserved. OKE profile examples exist. Knowledge refresh scheduling runs as a conservative cron job on the OCI backend VM. OCI DevOps metadata is scaffolded but not active. | Keep Gateway active and run refresh scheduling from the VM cron path. |
| IaC | Terraform covers core OCI foundation resources, API Gateway, Autonomous Database vector shadow infrastructure, backend VM cron refresh support, and deployment outputs. Staging Terraform state is configured for OCI Object Storage backend storage. | Keep the VM cron release-watch path active and stable-docs in safe mode until separately validated. |
| Observability | Health, readiness, infrastructure, analytics, fallback, governance, and diagnostics endpoints exist. OCI Logging/Monitoring/Notifications are represented when configured. | Add live metric/log emission only after readiness checks are stable. |
| Evaluation | Regression and advisory-quality suites cover retrieval, governance, migration, FinOps, release intelligence, runtime, and usability. | Keep every promotion tied to a quality gate. |
| Documentation | Internal beta docs are broad and mostly aligned, with accepted limitations documented. | Keep plan and status docs current as work advances. |

## Implemented Baseline Summary

The current working baseline includes:

- React/FastAPI advisory app deployed locally and in OCI staging.
- OCI API Gateway staging ingress with direct OCI VM rollback preserved.
- Active staging retrieval from OCI Object Storage using the validated `oci-rag-index.json` snapshot.
- Local JSON retrieval as deterministic rollback.
- Curated OCI corpus with 47 knowledge chunks/sources.
- Release-watch refresh on the OCI backend VM cron path with live fetch, quick gates, gated promotion, Object Storage upload, rollback support, and status visibility.
- Oracle AI Vector Search shadow infrastructure, table/index, and refreshed 47-chunk shadow sync.
- Deterministic synthesis as the default with OCI GenAI synthesis available behind configuration.
- Deterministic local embeddings as the default with OCI GenAI embeddings available behind configuration.
- Governance, risk, migration, FinOps, executive summary, topology, explainability, and auditability metadata in advisory responses.
- Knowledge Refresh Status UI panel showing VM cron state, gates, promotion/upload state, snapshot version, release-change count, affected-source count, and rollback posture.
- Regression and readiness gates for backend tests, frontend build/lint, retrieval health, retrieval regression, advisory evals, vector validation, Terraform validation, staging smoke, and operational readiness.

## Work In Progress / Not Yet Implemented

Keep these items in the active work queue until each has validation evidence and documentation updates:

| ID | Status | Item | Next validation |
|---|---|---|---|
| WIP-001 | Ready | Add a beginner-friendly ingestion/retrieval flow doc section: HTML/docs source -> chunks -> metadata -> embeddings -> `oci-rag-index.json` -> OCI Object Storage active retrieval -> Oracle AI Vector Search shadow sync. | Docs diff check; no code validation required. |
| WIP-002 | Ready | Add a read-only Retrieval Provider Status panel beside the refresh panel. | Frontend lint/build, backend retrieval health endpoint smoke, browser smoke. |
| WIP-003 | Ready | Expand the curated OCI corpus beyond 47 sources with high-value official OCI docs. | Corpus health, retrieval regression, golden/advisory eval subset, Object Storage upload if promoted. |
| WIP-004 | Gated | Run OCI GenAI embeddings in shadow mode and compare against local deterministic embeddings. | Embedding dimension validation, retrieval regression, Object Storage parity, Oracle shadow reload, rollback proof. |
| WIP-005 | Gated | Promote Oracle AI Vector Search from shadow to active retrieval only after refreshed parity passes. | Object Storage baseline, Oracle vector parity, retrieval regression, golden/edge eval subset, staging smoke, operational readiness, rollback drill. |
| WIP-006 | Gated | Run OCI GenAI synthesis live parity and decide whether to promote from deterministic default. | GenAI parity report, unsupported-claim check, citation coverage, latency/fallback metrics, deterministic rollback proof. |
| WIP-007 | Ready | Add OCI Monitoring custom metrics for refresh latency, gate failures, candidate promotion count, rollback count, and retrieval regression failures. | Operational readiness, OCI metric visibility, safe local fallback. |
| WIP-008 | Future | Move deployment automation from operator scripts toward OCI DevOps while preserving the current script-based rollback path. | OCI DevOps pipeline smoke, artifact parity with operator scripts, staging rollback validation. |
| WIP-009 | Future | Add full current-vs-historical release comparison and richer bi-temporal retrieval. | Release-aware evals, temporal snapshot tests, advisory regression. |
| WIP-010 | Future | Add saved review history, prompt/session history, and richer visualization rendering. | Frontend tests/build, UX smoke, storage/security review. |

## Priority Order

1. **Knowledge refresh stability**
   - Why first: refresh stability determines whether Object Storage and Oracle AI Vector Search stay aligned.
   - OCI-native target: backend OCI VM cron with operator-controlled rollback.
   - Initial increment: preflight `release-watch` in `no_fetch` plus `quick_gates` mode and prove authoritative snapshots do not change.

2. **Refresh candidate quality gate**
   - Why next: candidate snapshots must pass quality checks before any promotion.
   - OCI-native target: official OCI source refreshes, candidate reports, retrieval regression, and advisory/golden eval subsets.
   - Initial increment: run controlled candidate refresh and retain failed candidates under `knowledge/reports/runs/...`.

3. **Object Storage refresh promotion**
   - Why before vector sync: Object Storage remains the active retrieval provider and source of truth.
   - OCI-native target: OCI Object Storage manifests for `oci-rag-index.json` and `oci-release-snapshot.json`.
   - Initial increment: promote only a validated candidate, upload snapshots, and validate staging reads the refreshed manifest.

4. **Oracle AI Vector Search refresh sync**
   - Why after Object Storage promotion: Oracle vector shadow must be rebuilt from the same promoted snapshot.
   - OCI-native target: Oracle Database AI Vector Search shadow index.
   - Initial increment: rebuild the shadow index, validate counts and schema/index health, then run vector parity against Object Storage.

5. **OCI VM cron refresh runtime**
   - Why now: the backend VM is already inside OCI, has the repository and Python environment, and can run the same refresh policy without introducing an external scheduler.
   - OCI-native fit for current maturity: lightweight OCI Compute scheduling preserves local-dev parity while refresh quality gates mature.
   - Initial increment: install `/etc/cron.d/oci-architecture-studio-knowledge-refresh` with safe `no_fetch`, `quick_gates`, `candidate_only`, `upload=false` jobs.

6. **VM scheduled refresh dry run and activation**
   - Why staged: dry-run cron path proves logs, reports, and readiness before live upload/promotion.
   - OCI-native target: backend OCI VM cron release-watch first; stable-docs remains slower and conservative.
   - Initial increment: run safe `no_fetch`, `quick_gates`, `candidate_only`, `upload=false`, then activate gate-controlled release refresh.

7. **Return to Oracle vector promotion**
   - Why last: active semantic retrieval should wait for stable refresh, Object Storage promotion, and refreshed vector parity.
   - OCI-native target: Oracle AI Vector Search active provider with Object Storage and local JSON fallback.
   - Initial increment: run full refreshed parity, retrieval regression, golden/edge evals, and rollback validation before promotion.

## Linear Task Queue

Execute one task at a time. A task can move to `Done` only after its validation evidence is captured in this plan or a linked report.

| ID | Status | Task | Validation Gate |
|---|---|---|---|
| TASK-001 | Done | Add read-only Terraform remote state readiness checker for OCI Object Storage backend. | Passed `python3 -m py_compile infra/scripts/check_terraform_remote_state_readiness.py`; passed local `--skip-oci` readiness mode. |
| TASK-002 | Done | Document manual remote state migration workflow and rollback checklist. | Terraform README/runbook updated; migration remains operator-run and non-automated. |
| TASK-003 | Done | Add API Gateway readiness validation for configured endpoint and OCIDs. | Passed `tests/test_operational_hardening.py`, `tests/test_api.py`, `py_compile` for operational readiness script, and `git diff --check`. |
| TASK-004 | Done | Prepare API Gateway staging cutover checklist and rollback path. | Terraform validate and Gateway smoke commands documented; default-off behavior preserved. |
| TASK-005 | Done | Run OCI GenAI synthesis readiness/parity in skip-safe mode, then live mode when config exists. | Skip-safe parity run wrote `evals/reports/genai-synthesis-parity`; status skipped because `OCI_GENAI_COMPARTMENT_ID` and `OCI_GENAI_CHAT_MODEL_ID` are absent; deterministic default preserved. |
| TASK-006 | Done | Add OCI GenAI embedding activation checklist and diagnostics expectations. | Passed `tests/test_operational_hardening.py`, `tests/test_api.py`, and `git diff --check`; activation gates documented. |
| TASK-007 | Done | Validate Oracle AI Vector Search schema/index prerequisites without active-provider promotion. | Earlier local index validation passed; later TASK-027/TASK-031 loaded and validated the live shadow table/index with 47 chunks. |
| TASK-008 | Done | Add Oracle AI Vector Search dual-read parity workflow against Object Storage retrieval. | `retrieval_parity_check.py` supports `--oci-native-provider oracle_ai_vector_search`; later shadow vector validation passed against the refreshed Object Storage baseline. |
| TASK-009 | Blocked | Promote semantic retrieval through configuration only after parity approval. | Blocked until final refreshed Oracle AI Vector Search active-provider parity, smoke, regression, operational readiness, and rollback checks pass; promotion and rollback runbook documented. |
| TASK-012 | Done | Define OCI DevOps delivery contract around existing operator artifact flow. | OCI DevOps artifact/stage/rollback contract documented; operator script remains fallback. |
| TASK-013 | Done | Wire OCI DevOps metadata into runtime readiness checks for active deployments. | Passed `tests/test_operational_hardening.py`, `tests/test_api.py`, and `py_compile`; diagnostics distinguish inactive, partial, and promotion-ready DevOps metadata. |
| TASK-014 | Done | Expand official OCI corpus for highest-value advisory gaps. | Added Budgets, Security Zones, and Compute Autoscaling sources; offline index rebuild produced 47 chunks; retrieval regression 18/18, advisory-quality 5/5, golden 18/18 passed. |
| TASK-015 | Done | Harden release-intelligence freshness and selective reindex reporting. | Added refresh `lifecycle` summary covering candidate, gate, promotion, upload, rollback, and query-time refresh state; passed `tests/test_refresh_policy.py`, `git diff --check`, and no-fetch release-watch validation with 47 chunks. |
| TASK-016 | Done | Cut a new internal beta baseline after all active gates pass. | Local/backend/frontend/eval/Terraform gates passed; staging Object Storage refreshed to 47 chunks; staging smoke, retrieval health, operational readiness, and internal beta readiness passed with expected API Gateway/OCI DevOps warnings. |
| TASK-017 | Done | Select and execute the next OCI-native promotion increment. | Chose default-off Terraform readiness for API Gateway plus Oracle Autonomous AI Database/Vector Search rather than any live promotion. |
| TASK-018 | Done | Add default-off Terraform scaffold for Oracle Autonomous AI Database vector-search shadow mode. | Passed `terraform fmt -recursive`, `git diff --check`, and Terraform validate for dev/test/staging. Non-mutating staging plan kept API Gateway and Autonomous Database disabled; existing backend replacement drift remains a known do-not-apply condition. |
| TASK-019 | Done | Resolve staging Terraform drift before live API Gateway or database apply. | Added targeted `metadata["user_data"]` ignore for backend cloud-init bootstrap drift; passed Terraform fmt/check/validate; non-mutating staging plan now shows no real infrastructure changes, only new outputs. |
| TASK-020 | Done | Run API Gateway live preflight plan without cutover apply. | API Gateway-enabled staging plan proposed only `oci_apigateway_gateway.api[0]` and `oci_apigateway_deployment.backend[0]` creates; backend and all existing resources were no-op. |
| TASK-021 | Done | Apply OCI API Gateway and run smoke validation. | Gateway and deployment applied; route backend context fixed to `${request.path[path]}`; subnet HTTPS 443 opened; Gateway smoke, Gateway operational readiness, direct backend rollback smoke, and post-apply Terraform no-change plan passed. Runtime diagnostics still required a backend code/config sync before final promotion-ready reporting. |
| TASK-022 | Done | Update staging runtime API Gateway metadata without replacing backend VM. | Backend VM env now includes API Gateway endpoint/OCID and deployed code matches the repo; Gateway smoke, direct backend rollback smoke, and operational readiness passed with `api_gateway.active=true` and `api_gateway.promotion_ready=true`. Remaining readiness warning is OCI DevOps metadata only. |
| TASK-023 | Done | Run Oracle Autonomous AI Database / AI Vector Search live preflight plan. | Passed Terraform validate; staging plan with database enablement proposed exactly 3 creates, 0 changes, 0 destroys: vector DB NSG, TCPS ingress rule, and Autonomous Database. Binary plan artifact was removed because it can carry sensitive values. |
| TASK-024 | Done | Harden Autonomous Database admin secret handling before apply. | Added generated password support and OCI Vault secret storage for the vector database admin password; dev/test/staging Terraform init, fmt, and validate passed; staging preflight now shows 5 creates, 0 changes, 0 destroys. |
| TASK-025 | Done | Apply Oracle Autonomous AI Database vector-search shadow infrastructure. | Applied exactly 5 resources, 0 changes, 0 destroys: generated password, Vault secret, vector DB NSG, TCPS ingress rule, and Autonomous Database. Post-apply no-change plan, Gateway smoke, operational readiness, and backend regression tests passed. Active retrieval remains `oci_object_storage`. |
| TASK-026 | Done | Validate live Oracle AI Vector Search connectivity and schema/index prerequisites. | Added wallet-aware Oracle vector configuration, validated mTLS connectivity from the backend VM to the Autonomous Database private endpoint, and confirmed the vector table is not created yet. Active retrieval remains `oci_object_storage`. |
| TASK-027 | Done | Create Oracle AI Vector Search schema and load shadow index. | Deployed wallet-aware code, created Oracle vector schema and index, upserted 47 chunks, fixed Oracle LOB materialization before connection close, and passed health plus vector retrieval validation with 0.967 average top-chunk overlap. Active retrieval remains `oci_object_storage`. |
| TASK-028 | Done | Refresh Pipeline Preflight. | Passed direct `refresh_policy.py --mode release-watch --no-fetch --quick-gates`; fixed selective-refresh embedding validation argument propagation; passed forced temp-snapshot quick gates with retrieval health and 26-case retrieval regression; authoritative snapshot SHA-256 hashes remained unchanged; passed backend refresh/status tests and `git diff --check`. |
| TASK-029 | Done | Refresh Candidate Quality Gate. | Added candidate-only refresh mode and candidate snapshot validator; controlled forced `release-watch` candidate run passed without promotion or upload: 47 chunks, 5 releases, candidate metadata/release integrity validation, retrieval health, 26-case retrieval regression, 18/18 golden evals, and 5/5 advisory-quality evals. Authoritative snapshot SHA-256 hashes remained unchanged. |
| TASK-030 | Done | Object Storage Refresh Promotion. | Promoted a validated controlled `release-watch` candidate with 47 chunks and 5 releases; uploaded refreshed `oci-rag-index.json` and `oci-release-snapshot.json` to OCI Object Storage bucket `oci-architecture-studio-staging-knowledge-snapshots`; Object Storage retrieval health passed, 26-case retrieval regression passed, Gateway smoke passed, and operational readiness passed with known OCI DevOps/rebuildability warnings only. |
| TASK-031 | Done | Oracle Vector Refresh Sync. | Rebuilt Oracle AI Vector Search shadow index from the promoted snapshot on the staging backend VM; upserted 47 chunks; table/index health passed with 47 chunks, 44 services, 14 service domains, valid schema, and no missing config; vector validation passed 26 cases with 0.977 average top-chunk overlap. Active retrieval remains `oci_object_storage`. |
| TASK-034 | Done | VM Cron Refresh Dry Run. | Installed `/etc/cron.d/oci-architecture-studio-knowledge-refresh` on the OCI backend VM and ran safe release-watch plus stable-docs dry runs. Release-watch passed with `status=no_change`, `promoted=false`, `authoritative_snapshots_updated=false`, and `oci_upload_performed=false`; stable-docs passed candidate validation, retrieval health, and 26-case retrieval regression without promotion or upload. Gateway smoke, Object Storage retrieval health, operational readiness, Terraform no-change plan, and refresh status endpoint visibility passed. |
| TASK-035 | Done | VM Cron Release Refresh Activation. | Activated release-watch VM cron with live release fetch, gate-controlled promotion, and Object Storage upload while keeping stable-docs safe-mode. First live candidate was blocked by gates, so release parsing now marks inferred dates and release-watch reindexes affected knowledge sources from stable curated fallback by default. The corrected manual activation passed candidate validation, retrieval health, and 26-case retrieval regression; promoted 47 chunks and 12 release items; uploaded `oci-rag-index.json` and `oci-release-snapshot.json`; Gateway smoke, Object Storage retrieval health, operational readiness, backend tests, and Terraform no-change plan passed. Oracle AI Vector Search shadow was rebuilt from the promoted snapshot and passed 26-case vector validation with 0.977 average top-chunk overlap. |
| TASK-036 | Next | Return To Oracle Vector Promotion. | Resume active Oracle vector promotion only after refresh is stable; run Object Storage baseline, Oracle shadow parity, retrieval regression, and golden/edge evals. |
| TASK-037 | Done | Add read-only Knowledge Refresh Status panel plan. | Scope is UI visibility only: consume `/knowledge/refresh/status`, show VM cron run state, gate result, promotion/upload state, snapshot version, affected source count, and rollback posture. No query-time refresh or external scheduler is introduced. |
| TASK-038 | Done | Add typed frontend API support for refresh status. | Added TypeScript status models and API helper for `/knowledge/refresh/status`; existing architecture review API contract is unchanged. |
| TASK-039 | Done | Render Knowledge Refresh Status panel in the main UI. | Added read-only panel showing last run, pass/fail status, Object Storage upload, snapshot version, gate result, promotion status, release count, affected source count, and rollback state with a reload action. |
| TASK-040 | Done | Validate and document refresh status panel. | Frontend build passed, backend refresh status endpoint subset passed, `git diff --check` passed, browser smoke verified panel rendering and reload, and README/plan documentation were updated. |
| TASK-041 | Next | Document the ingestion-to-retrieval flow for operators and reviewers. | Add a concise explainer covering HTML/docs source -> chunks -> metadata -> embeddings -> `oci-rag-index.json` -> OCI Object Storage -> Oracle AI Vector Search shadow sync; run `git diff --check`. |
| TASK-042 | Planned | Add Retrieval Provider Status UI panel. | Frontend lint/build, `/retrieval/health` smoke, browser smoke. |
| TASK-043 | Planned | Expand curated official OCI corpus beyond 47 sources. | Corpus health, retrieval regression, golden/advisory eval subset, Object Storage upload if promoted. |
| TASK-044 | Gated | Run OCI GenAI embeddings shadow activation. | Embedding dimension validation, retrieval regression, Object Storage parity, Oracle shadow reload, rollback proof. |
| TASK-045 | Gated | Run Oracle AI Vector Search active-read promotion gate. | Object Storage baseline, Oracle vector parity, retrieval regression, golden/edge eval subset, staging smoke, operational readiness, rollback drill. |

## Phase Gates

| Phase | Status | Promotion gate | Rollback path |
|---|---|---|---|
| Remote Terraform state readiness | Not Started | Readiness checker passes without mutating state; runbook updated. | Continue local Terraform state. |
| API Gateway promotion | Done | Terraform validate, API Gateway endpoint smoke, backend direct path retained until cutover verified. | Disable `enable_api_gateway`; use direct VM backend endpoint. |
| OCI GenAI shadow activation | Not Started | Parity report shows no unsupported claims increase, no fallback-only result, acceptable latency, citation coverage preserved. | `SYNTHESIS_PROVIDER=deterministic`; deterministic fallback remains enabled. |
| OCI GenAI embeddings shadow activation | Not Started | Embedding dimension validation passes; retrieval regression does not degrade; fallback diagnostics clean. | `EMBEDDING_PROVIDER=local`; retain existing vector manifest. |
| Oracle AI Vector Search shadow mode | Done | Schema/index validation passes; dual-read parity acceptable across golden, edge, and retrieval regression cases. | Keep `RETRIEVAL_PROVIDER=oci_object_storage`. |
| Semantic retrieval active promotion | Not Started | Active-provider staging smoke, retrieval health, vector validation, eval suites, and rollback drill pass. | Restore `RETRIEVAL_PROVIDER=oci_object_storage` or `local_json`. |
| Scheduled refresh activation | VM Cron Release-Watch Active | Backend VM cron now runs live release-watch with gated promotion/upload; stable-docs remains safe-mode. | Set release-watch cron back to `VM_REFRESH_CANDIDATE_ONLY=true VM_REFRESH_UPLOAD=false`; continue operator-triggered refresh. |
| OCI DevOps delivery promotion | Not Started | Pipeline deploys same artifact path as operator scripts; staging smoke and readiness gates pass. | Use existing operator scripts. |

## Required Validation Matrix

Run the appropriate subset after each increment; run the full matrix before a new baseline tag.

| Validation | Command or check | Required for |
|---|---|---|
| Backend unit tests | `PYTHONPATH=src .venv/bin/python -m pytest tests` from `app/backend` | Backend, retrieval, synthesis, diagnostics, governance changes |
| Frontend build | `npm run build` from `app/frontend` | UI and response rendering changes |
| Golden evals | `PYTHONPATH=app/backend/src app/backend/.venv/bin/python evals/run_golden.py --output-dir evals/reports/golden` | Advisory behavior changes |
| Edge/advisory/evaluation suites | `evals/run_golden.py --cases ...` | Reasoning, governance, migration, FinOps, executive, runtime changes |
| Retrieval regression | `infra/scripts/retrieval_regression_check.py` | Retrieval, corpus, embedding, reranking, vector changes |
| Vector validation | `infra/scripts/vector_retrieval_validation.py --allow-skip` | Oracle AI Vector Search work |
| GenAI parity | `infra/scripts/genai_synthesis_parity_check.py` | OCI GenAI synthesis activation |
| Terraform validation | `terraform fmt -check -recursive infra/terraform` and env-specific `terraform validate` | IaC changes |
| Deployment config validation | `infra/scripts/validate_deployment_config.py` | Runtime/deployment changes |
| Operational readiness | `infra/scripts/operational_readiness_check.py` | Runtime, OCI integrations, diagnostics |
| Internal beta readiness | `infra/scripts/internal_beta_readiness_check.py` | Baseline promotion/tagging |
| Staging smoke | `infra/scripts/smoke_oci_deployment.py` | Staging promotion or endpoint changes |

## Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Remote state migration mistake | Terraform drift or difficult rollback | Add readiness checker first; migration remains manual and reviewed. |
| API Gateway cutover breaks access | Staging outage or demo interruption | Keep direct backend path until Gateway smoke passes; document rollback variable. |
| GenAI output becomes generic or unsupported | Advisory quality regression | Require parity reports, hallucination checks, citations, and deterministic fallback. |
| Vector search loses citation parity | Weak grounding and lower trust | Dual-read against Object Storage before active promotion; keep Object Storage fallback. |
| Scheduler refresh corrupts snapshots/index | Retrieval regression | Keep VM cron in safe mode until dry run passes; require candidate gates before upload/promotion; retain previous snapshots and rollback provider. |
| DevOps pipeline diverges from operator scripts | Deployment inconsistency | Define pipeline contract around existing scripts/artifacts before promotion. |
| Docs overstate runtime maturity | Stakeholder trust risk | Update limitations with every promotion and avoid production claims before validation. |

## Next Actionable Increment

Current task: `TASK-041`.

Document the ingestion-to-retrieval flow:

1. Explain how `knowledge/source_registry.json` and official OCI docs/fallback text become chunks.
2. Show where metadata and embeddings are added.
3. Show how `knowledge/snapshots/oci-rag-index.json` becomes the promoted Object Storage manifest.
4. Show how the same promoted snapshot is loaded into Oracle AI Vector Search shadow mode.
5. Keep Oracle vector active-provider promotion gated behind `TASK-045`.

## Operating Rules

- Inspect before implementing.
- Prefer the smallest promotion that produces measurable OCI-native progress.
- Keep local development and deterministic fallback working.
- Do not promote a provider without rollback proof.
- Do not make staging default changes without validation evidence.
- Commit and push validated increments continuously.
- Update this plan whenever reality changes.
