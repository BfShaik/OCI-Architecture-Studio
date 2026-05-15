# OCI Architecture Studio — Living Execution Plan

Last updated: 2026-05-15

## Purpose

This document is the active execution plan for moving OCI Architecture Studio from the `v1.0.0` internal beta baseline toward a stronger OCI-native enterprise beta. It is intentionally living: update it whenever a promotion gate passes, a gap is retired, or a new risk is discovered.

The plan favors OCI-native services, Terraform-managed infrastructure, deterministic fallback, local development compatibility, and small explainable increments. It does not introduce autonomous agents, hidden SaaS dependencies, external schedulers, external vector databases, GitHub Actions-based operational orchestration, or heavyweight workflow engines.

## Current Baseline

| Area | Current position | Baseline decision |
|---|---|---|
| Git baseline | `main` and `v1.0.0` point at the internal beta release baseline. Current execution branch is `codex/oci-native-continuous-execution`. | Treat `v1.0.0` as the stable recovery point. |
| Retrieval | Staging uses `oci_object_storage` with `local_json` fallback. Oracle AI Vector Search provider/tooling exists but active DB-backed retrieval is not promoted. | Keep Object Storage active until vector parity passes. |
| Synthesis | Deterministic synthesis is default. OCI GenAI synthesis exists behind configuration and fails closed to deterministic fallback. | Keep deterministic default until live GenAI parity passes. |
| Embeddings | Deterministic local embeddings are the stable path. OCI GenAI embeddings are configurable but not the default. | Activate in shadow/parity mode before promotion. |
| Runtime | OCI VM staging is active. OKE and Functions-compatible profiles exist. API Gateway and OCI DevOps metadata are scaffolded but not active. | Promote ingress and delivery one gate at a time. |
| IaC | Terraform covers core OCI foundation resources and optional API Gateway/Functions/Scheduler scaffolds. State remains local unless Object Storage backend is configured manually. | Move remote state readiness ahead of shared operations. |
| Observability | Health, readiness, infrastructure, analytics, fallback, governance, and diagnostics endpoints exist. OCI Logging/Monitoring/Notifications are represented when configured. | Add live metric/log emission only after readiness checks are stable. |
| Evaluation | Regression and advisory-quality suites cover retrieval, governance, migration, FinOps, release intelligence, runtime, and usability. | Keep every promotion tied to a quality gate. |
| Documentation | Internal beta docs are broad and mostly aligned, with accepted limitations documented. | Keep plan and status docs current as work advances. |

## Priority Order

1. **Remote Terraform state readiness**
   - Why first: shared OCI operations and rebuild confidence depend on state safety.
   - OCI-native target: OCI Object Storage Terraform backend.
   - Initial increment: add a non-mutating readiness checker that verifies backend template, namespace, bucket access, and local-state migration prerequisites without moving state automatically.

2. **OCI API Gateway promotion**
   - Why next: staging currently exposes the backend VM directly.
   - OCI-native target: OCI API Gateway in front of the backend, with Terraform-managed configuration.
   - Initial increment: validate default-off scaffold, document cutover inputs, add readiness checks for endpoint/OCID configuration.

3. **OCI GenAI shadow activation**
   - Why next: advisory quality may improve, but deterministic fallback must remain safe.
   - OCI-native target: OCI Generative AI chat and embeddings.
   - Initial increment: run deterministic-vs-GenAI synthesis parity and embedding diagnostics when approved model config exists; keep fallback required.

4. **Oracle AI Vector Search shadow mode**
   - Why next: Object Storage retrieval is stable, but semantic search needs DB-backed parity before active read promotion.
   - OCI-native target: Oracle Database with AI Vector Search.
   - Initial increment: validate schema/index readiness, dual-read against Object Storage, and compare citation/result parity.

5. **Semantic retrieval promotion**
   - Why after shadow mode: active retrieval should move only after measured parity and rollback proof.
   - OCI-native target: Oracle AI Vector Search active provider with Object Storage and local JSON fallback.
   - Initial increment: promote through configuration only, run retrieval regression, vector validation, golden/edge evals, and staging smoke.

6. **OCI Functions + Resource Scheduler activation**
   - Why after retrieval stability: scheduled refresh should not automate unstable index flows.
   - OCI-native target: OCI Functions invoked by OCI Resource Scheduler for release refresh, selective reindexing, and integrity checks.
   - Initial increment: build function image path, validate schedule OCIDs, and run a controlled refresh invocation.

7. **OCI DevOps delivery path**
   - Why later: operator scripts are adequate for beta; OCI DevOps becomes valuable when deployment inputs stabilize.
   - OCI-native target: OCI DevOps project and deploy pipeline metadata wired into runtime diagnostics.
   - Initial increment: define pipeline contract and validation checks without removing local/operator deployment.

8. **Corpus and release intelligence expansion**
   - Why continuous: retrieval and advisory quality depend on source coverage and freshness.
   - OCI-native target: Object Storage snapshots and Oracle AI Vector Search indexes built from curated official OCI sources.
   - Initial increment: expand official OCI corpus by workload gaps, then rerun retrieval and advisory-quality evaluations.

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
| TASK-007 | Done | Validate Oracle AI Vector Search schema/index prerequisites without active-provider promotion. | Local index validation passed for 44 chunks at 256 dimensions; vector validation skip-safe report confirms missing Oracle DB config without active-provider promotion. |
| TASK-008 | Done | Add Oracle AI Vector Search dual-read parity workflow against Object Storage retrieval. | `retrieval_parity_check.py` now supports `--oci-native-provider oracle_ai_vector_search`; skip-safe run used Object Storage baseline with 44 chunks and reported missing Oracle DB config. |
| TASK-009 | Blocked | Promote semantic retrieval through configuration only after parity approval. | Blocked until Oracle DB vector config exists and Oracle AI Vector Search parity passes without skip; promotion and rollback runbook documented. |
| TASK-010 | Done | Activate controlled OCI Functions knowledge-refresh invocation path. | Local Function handler smoke passed with `no_fetch`, `quick_gates`, `upload=false`, `promoted=false`, and reports written under `/tmp`. |
| TASK-011 | Blocked | Activate OCI Resource Scheduler for release refresh after function readiness. | Blocked until Function image is built/pushed to OCIR and packaged invocation passes; enablement and rollback path documented. |
| TASK-012 | Done | Define OCI DevOps delivery contract around existing operator artifact flow. | OCI DevOps artifact/stage/rollback contract documented; operator script remains fallback. |
| TASK-013 | Done | Wire OCI DevOps metadata into runtime readiness checks for active deployments. | Passed `tests/test_operational_hardening.py`, `tests/test_api.py`, and `py_compile`; diagnostics distinguish inactive, partial, and promotion-ready DevOps metadata. |
| TASK-014 | Next | Expand official OCI corpus for highest-value advisory gaps. | Retrieval regression and advisory evals do not regress. |
| TASK-015 | Not Started | Harden release-intelligence freshness and selective reindex reporting. | Release refresh report shows candidate, gate, and promotion state. |
| TASK-016 | Not Started | Cut a new internal beta baseline after all active gates pass. | Full validation matrix passes; docs updated; commit, push, and tag. |

## Phase Gates

| Phase | Status | Promotion gate | Rollback path |
|---|---|---|---|
| Remote Terraform state readiness | Not Started | Readiness checker passes without mutating state; runbook updated. | Continue local Terraform state. |
| API Gateway promotion | Not Started | Terraform validate, API Gateway endpoint smoke, backend direct path retained until cutover verified. | Disable `enable_api_gateway`; use direct VM backend endpoint. |
| OCI GenAI shadow activation | Not Started | Parity report shows no unsupported claims increase, no fallback-only result, acceptable latency, citation coverage preserved. | `SYNTHESIS_PROVIDER=deterministic`; deterministic fallback remains enabled. |
| OCI GenAI embeddings shadow activation | Not Started | Embedding dimension validation passes; retrieval regression does not degrade; fallback diagnostics clean. | `EMBEDDING_PROVIDER=local`; retain existing vector manifest. |
| Oracle AI Vector Search shadow mode | Not Started | Schema/index validation passes; dual-read parity acceptable across golden, edge, and retrieval regression cases. | Keep `RETRIEVAL_PROVIDER=oci_object_storage`. |
| Semantic retrieval active promotion | Not Started | Active-provider staging smoke, retrieval health, vector validation, eval suites, and rollback drill pass. | Restore `RETRIEVAL_PROVIDER=oci_object_storage` or `local_json`. |
| Scheduled refresh activation | Not Started | Function invocation, Resource Scheduler OCIDs, release refresh, and selective reindex checks pass. | Disable schedules; return to operator-triggered refresh. |
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
| Scheduler refresh corrupts snapshots/index | Retrieval regression | Start with controlled invocation; retain previous snapshots and rollback provider. |
| DevOps pipeline diverges from operator scripts | Deployment inconsistency | Define pipeline contract around existing scripts/artifacts before promotion. |
| Docs overstate runtime maturity | Stakeholder trust risk | Update limitations with every promotion and avoid production claims before validation. |

## Next Actionable Increment

Current task: `TASK-014`.

Expand official OCI corpus for highest-value advisory gaps:

1. Inspect current source registry and eval weak spots.
2. Add official OCI source entries only where advisory coverage is thin.
3. Rebuild local index without live fetch if needed.
4. Run retrieval regression and advisory evals before promotion.

## Operating Rules

- Inspect before implementing.
- Prefer the smallest promotion that produces measurable OCI-native progress.
- Keep local development and deterministic fallback working.
- Do not promote a provider without rollback proof.
- Do not make staging default changes without validation evidence.
- Commit and push validated increments continuously.
- Update this plan whenever reality changes.
