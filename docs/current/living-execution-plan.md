# OCI Architecture Studio — Living Execution Plan

Last updated: 2026-05-16

## Purpose

This document is the active execution plan for moving OCI Architecture Studio from the `v1.0.1` internal beta baseline toward a stronger OCI-native enterprise beta. It is intentionally living: update it whenever a promotion gate passes, a gap is retired, or a new risk is discovered.

The plan favors OCI-native services, Terraform-managed infrastructure, deterministic fallback, local development compatibility, and small explainable increments. It does not introduce autonomous agents, hidden SaaS dependencies, external schedulers, external vector databases, GitHub Actions-based operational orchestration, or heavyweight workflow engines.

## Current Baseline

| Area | Current position | Baseline decision |
|---|---|---|
| Git baseline | `main` is the active branch. The latest closeout commits document and deploy section traceability plus review-history operator controls to staging. | Treat the latest pushed `main` commit and existing version tags as recovery points; do not move existing tags. |
| Retrieval | Staging uses `oracle_ai_vector_search` as the active provider with fallback enabled. Object Storage remains the immediate config-only rollback provider; `local_json` remains the deterministic local fallback. | Keep Oracle vector active only while health, smoke, regression, and rollback evidence stay current. |
| Synthesis | Deterministic synthesis is default. OCI GenAI synthesis exists behind configuration and fails closed to deterministic fallback. | Keep deterministic default until live GenAI parity passes. |
| Embeddings | Deterministic local embeddings are the stable path. OCI GenAI embeddings are configurable but not the default. | Activate in shadow/parity mode before promotion. |
| Runtime | OCI VM staging is active behind OCI API Gateway, with direct VM rollback preserved. OKE profile examples exist. Knowledge refresh scheduling runs as a conservative cron job on the OCI backend VM. OCI DevOps metadata is scaffolded but not active. | Keep Gateway active and run refresh scheduling from the VM cron path. |
| IaC | Terraform covers core OCI foundation resources, API Gateway, Autonomous Database vector infrastructure, backend VM cron refresh support, and deployment outputs. Staging Terraform state is configured for OCI Object Storage backend storage. | Keep the VM cron release-watch path active and stable-docs in safe mode until separately validated. |
| Observability | Health, readiness, infrastructure, analytics, fallback, governance, and diagnostics endpoints exist. OCI Logging/Monitoring/Notifications are represented when configured. | Add live metric/log emission only after readiness checks are stable. |
| Evaluation | Regression and advisory-quality suites cover retrieval, governance, migration, FinOps, release intelligence, runtime, and usability. | Keep every promotion tied to a quality gate. |
| Documentation | Internal beta docs are broad and mostly aligned, with accepted limitations documented. | Keep plan and status docs current as work advances. |

## Implemented Baseline Summary

The current working baseline includes:

- React/FastAPI advisory app deployed locally and in OCI staging.
- OCI API Gateway staging ingress with direct OCI VM rollback preserved.
- Active staging retrieval from Oracle AI Vector Search using the validated 60-chunk architecture corpus.
- OCI Object Storage retrieval as the immediate staging rollback path and local JSON retrieval as deterministic local fallback.
- Curated OCI corpus with 60 active staging knowledge chunks.
- Release-watch refresh on the OCI backend VM cron path with live fetch, quick gates, gated promotion, Object Storage upload, rollback support, and status visibility.
- Oracle AI Vector Search infrastructure, table/index, and active-read sync from the promoted snapshot.
- Deterministic synthesis as the default with OCI GenAI synthesis available behind configuration.
- Deterministic local embeddings as the default with OCI GenAI embeddings available behind configuration.
- Governance, risk, migration, FinOps, executive summary, topology, explainability, and auditability metadata in advisory responses.
- Knowledge Refresh Status UI panel showing VM cron state, gates, promotion/upload state, snapshot version, release-change count, affected-source count, and rollback posture.
- Regression and readiness gates for backend tests, frontend build/lint, retrieval health, retrieval regression, advisory evals, vector validation, Terraform validation, staging smoke, and operational readiness.

## Work In Progress / Not Yet Implemented

Keep these items in the active work queue until each has validation evidence and documentation updates:

| ID | Status | Item | Next validation |
|---|---|---|---|
| WIP-001 | Done | Added a beginner-friendly ingestion/retrieval flow doc section: HTML/docs source -> chunks -> metadata -> embeddings -> `oci-rag-index.json` -> OCI Object Storage promoted snapshot -> Oracle AI Vector Search active retrieval. | Passed `git diff --check`; no code validation required. |
| WIP-002 | Done | Added a read-only Retrieval Provider Status panel beside the refresh panel. | Passed frontend lint/build, backend retrieval health endpoint smoke, browser smoke, and `git diff --check`. |
| WIP-003 | Done | Expanded the curated OCI corpus beyond 47 sources with high-value official OCI docs. | Offline candidate rebuild produced 55 chunks from 55 sources; corpus health, retrieval regression, golden evals, advisory-quality evals, edge evals, and targeted backend tests passed. No Object Storage upload was performed. |
| WIP-004 | Done | Ran OCI GenAI embeddings in shadow mode and compared against local deterministic embeddings. | Live `cohere.embed-v4.0` shadow candidate built with the project staging compartment at 256 dimensions; corpus health, candidate validation, retrieval regression, golden/advisory/edge evals, Oracle local-index validation, embedding visibility, and rollback baseline checks passed. No Object Storage upload or active promotion was performed. |
| WIP-005 | Done | Promote Oracle AI Vector Search from shadow to active retrieval only after refreshed parity passes. | Completed through TASK-045 and TASK-050; active staging retrieval is `oracle_ai_vector_search` with 60 chunks and Object Storage fallback retained. |
| WIP-006 | Blocked | Run OCI GenAI synthesis live parity and decide whether to promote from deterministic default. | Waiting for approved `OCI_GENAI_COMPARTMENT_ID` and `OCI_GENAI_CHAT_MODEL_ID` runtime configuration. Skip-safe local/staging parity runs passed deterministic baselines and preserved the deterministic default. |
| WIP-007 | Ready | Add OCI Monitoring custom metrics for refresh latency, gate failures, candidate promotion count, rollback count, and retrieval regression failures. | Operational readiness, OCI metric visibility, safe local fallback. |
| WIP-008 | Future | Move deployment automation from operator scripts toward OCI DevOps while preserving the current script-based rollback path. | OCI DevOps pipeline smoke, artifact parity with operator scripts, staging rollback validation. |
| WIP-009 | Future | Add full current-vs-historical release comparison and richer bi-temporal retrieval. | Release-aware evals, temporal snapshot tests, advisory regression. |
| WIP-010 | Future | Improve the broader advisor UX shell after the near-term visibility and readability work lands, including navigation polish, review workflow affordances, and demo-readiness cleanup. | Frontend tests/build, UX smoke, browser smoke. |
| WIP-011 | Planned | Refine the main advisory response layout for stronger executive and architecture-review readability. Group executive summary, recommended-now items, recommended-later items, risks, evidence, and rollout guidance into clearer scan-friendly sections. | Frontend lint/build, browser smoke with representative architecture, migration, cost, and release-aware prompts. |
| WIP-012 | Planned | Improve explainability UI so users can see why services were selected, why alternatives were not selected, and how retrieval, governance, release-awareness, and confidence influenced the recommendation. | Frontend lint/build, backend response-contract check, browser smoke, advisory eval subset. |
| WIP-013 | Done | Improved release-context visibility in the UI, including release match counts, affected services, recommendation-affecting services, impact/change categories, snapshot timestamp, temporal boundary, and maturity notes. | Passed frontend lint/build, backend tests, local retrieval regression, local deployment smoke, staging direct/API Gateway smoke, retrieval health, env/snapshot hash guardrails, and browser smoke with a release-aware prompt. |
| WIP-014 | Done | Added lightweight architecture visualization for OCI service relationships, topology summaries, HA/DR posture, and migration phases without introducing a heavy diagram engine. | Passed frontend lint/build, focused topology/API tests, backend full suite, local retrieval regression, local deployment smoke, staging direct/API Gateway smoke, retrieval health, env/snapshot hash guardrails, and browser smoke with a representative topology prompt. |
| WIP-015 | Done | Add saved review history and prompt/session history with a storage and security design that fits the OCI-native runtime direction. | Completed through TASK-051 and TASK-053 with redacted persistence, policy metadata, export controls, delete controls, backend tests, frontend build, local smoke, and staging smoke. |
| WIP-016 | Done | Improve section-level citation presentation so recommendations and rationale can be traced more directly to retrieved sources. | Completed through TASK-052 with enriched section citation metadata, eval checks, frontend build, local smoke, and staging smoke. |

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
   - Why before vector sync: Object Storage remains the promoted snapshot and rollback source of truth.
   - OCI-native target: OCI Object Storage manifests for `oci-rag-index.json` and `oci-release-snapshot.json`.
   - Initial increment: promote only a validated candidate, upload snapshots, and validate staging reads the refreshed manifest.

4. **Oracle AI Vector Search refresh sync**
   - Why after Object Storage promotion: Oracle vector active index must be rebuilt from the same promoted snapshot.
   - OCI-native target: Oracle Database AI Vector Search active index.
   - Initial increment: rebuild the active index, validate counts and schema/index health, then run vector parity against Object Storage.

5. **OCI VM cron refresh runtime**
   - Why now: the backend VM is already inside OCI, has the repository and Python environment, and can run the same refresh policy without introducing an external scheduler.
   - OCI-native fit for current maturity: lightweight OCI Compute scheduling preserves local-dev parity while refresh quality gates mature.
   - Initial increment: install `/etc/cron.d/oci-architecture-studio-knowledge-refresh` with safe `no_fetch`, `quick_gates`, `candidate_only`, `upload=false` jobs.

6. **VM scheduled refresh dry run and activation**
   - Why staged: dry-run cron path proves logs, reports, and readiness before live upload/promotion.
   - OCI-native target: backend OCI VM cron release-watch first; stable-docs remains slower and conservative.
   - Initial increment: run safe `no_fetch`, `quick_gates`, `candidate_only`, `upload=false`, then activate gate-controlled release refresh.

7. **Return to Oracle vector promotion**
   - Status: complete through TASK-045 and TASK-050.
   - OCI-native target: Oracle AI Vector Search active provider with Object Storage and local JSON fallback.
   - Next related work: keep the active vector index aligned with promoted snapshots during future refreshes.

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
| TASK-036 | Done | Return To Oracle Vector Promotion. | Superseded by TASK-045 active Oracle AI Vector Search promotion and TASK-050 60-source architecture corpus promotion. Active staging retrieval is now `oracle_ai_vector_search` with Object Storage fallback retained. |
| TASK-037 | Done | Add read-only Knowledge Refresh Status panel plan. | Scope is UI visibility only: consume `/knowledge/refresh/status`, show VM cron run state, gate result, promotion/upload state, snapshot version, affected source count, and rollback posture. No query-time refresh or external scheduler is introduced. |
| TASK-038 | Done | Add typed frontend API support for refresh status. | Added TypeScript status models and API helper for `/knowledge/refresh/status`; existing architecture review API contract is unchanged. |
| TASK-039 | Done | Render Knowledge Refresh Status panel in the main UI. | Added read-only panel showing last run, pass/fail status, Object Storage upload, snapshot version, gate result, promotion status, release count, affected source count, and rollback state with a reload action. |
| TASK-040 | Done | Validate and document refresh status panel. | Frontend build passed, backend refresh status endpoint subset passed, `git diff --check` passed, browser smoke verified panel rendering and reload, and README/plan documentation were updated. |
| TASK-041 | Done | Document the ingestion-to-retrieval flow for operators and reviewers. | Added `docs/current/ingestion-to-retrieval-flow.md`, linked it from `knowledge/README.md`, and passed `git diff --check`. |
| TASK-042 | Done | Add Retrieval Provider Status UI panel. | Added typed frontend API support for `/retrieval/health`, rendered a read-only provider panel beside the refresh panel, and passed frontend lint/build, backend retrieval-health smoke, browser smoke, and `git diff --check`. |
| TASK-043 | Done | Expand curated official OCI corpus beyond 47 sources. | Added eight official OCI source entries for Network Firewall, Vulnerability Scanning, OS Management Hub, Container Instances, Queue, Health Checks, Database Management, and Generative AI; updated release-impact source hints; offline candidate rebuild produced 55 chunks from 55 sources; passed corpus health, 18/18 retrieval regression, 18/18 golden evals, 5/5 advisory-quality evals, 8/8 edge evals, targeted backend reasoning/retrieval tests, JSON validation, `py_compile`, and `git diff --check`. No Object Storage upload was performed. |
| TASK-044 | Done | Run OCI GenAI embeddings shadow activation. | Used `cohere.embed-v4.0` with the project staging compartment and 256 output dimensions; upgraded OCI SDK support for `outputDimensions`; built `/tmp/oci-rag-index-task044-genai.json`; passed corpus health, candidate validation, 18/18 retrieval regression, 18/18 golden evals, 5/5 advisory-quality evals, 8/8 edge evals, Oracle local-index validation, embedding visibility checks, backend embedding/retrieval tests, and deterministic rollback baseline retrieval regression. No Object Storage upload, authoritative snapshot promotion, or active provider change was performed. |
| TASK-045 | Done | Run Oracle AI Vector Search active-read promotion gate. | Fixed Run Command IAM, ADB TCPS `1522` security-list access, stale runtime wallet, and secret-safe runtime vector env configuration. Added Oracle DB connection pooling for active reads. Promoted staging to `RETRIEVAL_PROVIDER=oracle_ai_vector_search` with fallback enabled and local embeddings retained. Passed backend full suite, frontend lint/build, local regression/golden/edge evals, VM targeted tests, Oracle vector validation, 26/26 parity, 18/18 Oracle-vector regression, Gateway/direct smoke, operational readiness, Terraform no-change plan, and rollback drill back to Object Storage and forward to Oracle vector. |
| TASK-046 | Done | Refine the advisory response layout for executive and architecture-review readability. | Added Decision Snapshot, recommendation priority cards, implementation exit criteria, comparison evidence chips, recommendation-confidence cards, and tradeoff cards. Fixed the promoted Oracle vector status label. Frontend lint/build, local browser smoke with a representative architecture prompt, staging frontend smoke, direct VM smoke, API Gateway smoke, retrieval health, and `git diff --check` passed. |
| TASK-047 | Done | Add explainability UI for service selection, rejected alternatives, retrieval influence, governance influence, release-awareness influence, and confidence scoring. | Enabled retrieval debug traces for UI review requests; added Explainability panel with influence cards, service-selection rationale, rejected alternatives, mapped services, domain signals, and selected evidence labels. Frontend lint/build, local browser smoke, staging browser smoke, direct VM smoke, API Gateway smoke, and retrieval health passed. |
| TASK-048 | Done | Improve release-context visibility in the advisory UI. | Added Release Context summary cards and detail panels for release matches, affected services, recommendation-affecting services, impact/change categories, snapshot timing, temporal boundary, and release notes. Passed frontend lint/build, backend full suite, local retrieval regression, local deployment smoke, staging direct/API Gateway smoke, retrieval health, env/snapshot hash guardrails, and browser smoke with a release-aware prompt. |
| TASK-049 | Done | Add lightweight architecture visualization for service relationships, topology summaries, HA/DR posture, and migration phases. | Added Architecture Map summary cards, lane-based service map, relationship evidence board, implementation path, and operational notes using the existing `architecture_topology` contract. Passed frontend lint/build, focused topology/API tests, backend full suite, local retrieval regression, local deployment smoke, staging direct/API Gateway smoke, retrieval health, env/snapshot hash guardrails, and browser smoke with a representative topology prompt. |
| TASK-050 | Done | Improve OCI architecture service accuracy and promote the 60-source architecture corpus to active Oracle vector retrieval. | Added Architecture Center-style reference sources for secure landing zones, EKS-to-OKE migration, database DR, analytics data lake, and enterprise observability; added landing-zone, EKS-to-OKE, and database DR evals; corrected ECR to Container Registry mapping; protected explicit service evidence selection for security prompts. Passed corpus health, 18/18 retrieval regression, 7/7 architecture-realism retrieval/evals, 18/18 golden evals, backend full suite, frontend lint/build, VM focused tests, direct/API Gateway smoke, live landing-zone evidence check, and env/release/knowledge hash guardrails. Staging Oracle AI Vector Search is active with 60 chunks and fallback inactive. |
| TASK-051 | Done | Add saved review history and prompt/session history after storage and security design are agreed. | Added redacted file-backed review history with 50-record retention, mode `600` writes, list/detail/delete APIs, `review_id` response metadata, and a Saved Reviews UI for refresh, open, active-state, and delete. Persisted records exclude retrieval/synthesis debug traces and redact obvious secrets. Deployment/eval smoke paths opt out of persistence. Passed backend full suite, focused API tests, frontend lint/build, golden evals, local browser smoke, VM focused tests, direct/API Gateway smoke, Gateway history redaction/delete smoke, staging browser smoke, retrieval health, env hash guardrail, and `git diff --check`. |
| TASK-052 | Done | Improve section-level citation presentation for recommendation traceability. | Enriched section citation metadata with source URLs, relevance, trust level, source counts, and traceability notes; added eval checks for section citations; added UI section-to-source traceability cards, S-numbered recommendation evidence links, and S-number source badges. Passed backend full suite, focused response/API tests, frontend lint/build, retrieval regression, architecture-realism evals, golden evals, local browser smoke, and `git diff --check`. |
| TASK-053 | Done | Add operator controls for review history retention/export policy. | Added policy metadata, redacted export, delete-all API, left-rail policy/export/clear controls, and recursive response redaction for saved history. Passed py_compile, focused API tests, backend full suite, frontend lint/build, local API/browser smoke, staging focused API tests, direct/API Gateway smoke, Gateway policy/redaction/export smoke, staging browser smoke, retrieval health, env hash guardrail, and `git diff --check`. |
| TASK-054 | Blocked | Run OCI GenAI synthesis live parity without changing the deterministic default. | Parity checker now validates required-service coverage, missing required services, latency guardrails, fallback state, unsupported claims, hallucination findings, and promotion recommendation. Local and staging skip-safe runs passed deterministic baselines, but live OCI GenAI skipped because `OCI_GENAI_COMPARTMENT_ID` and `OCI_GENAI_CHAT_MODEL_ID` are not configured. |
| TASK-055 | Gated | Migrate embeddings from local hash to OCI GenAI semantic embeddings. | Operator approved `cohere.embed-v4.0` as the best visible candidate after `cohere.embed-english-v3.0` was not listed in the tenancy/region. Added the D1 mismatch guardrail only: retrieval now refuses configured embedder/index metadata mismatches and `/retrieval/health` exposes the verdict. No reindex, Object Storage upload, staging env flip, or provider promotion was performed because `TASK-054` remains blocked and v4 changes the target dimensions to 1536. |

## Phase Gates

| Phase | Status | Promotion gate | Rollback path |
|---|---|---|---|
| Remote Terraform state readiness | Not Started | Readiness checker passes without mutating state; runbook updated. | Continue local Terraform state. |
| API Gateway promotion | Done | Terraform validate, API Gateway endpoint smoke, backend direct path retained until cutover verified. | Disable `enable_api_gateway`; use direct VM backend endpoint. |
| OCI GenAI shadow activation | Not Started | Parity report shows no unsupported claims increase, no fallback-only result, acceptable latency, citation coverage preserved. | `SYNTHESIS_PROVIDER=deterministic`; deterministic fallback remains enabled. |
| OCI GenAI embeddings shadow activation | Done | Embedding dimension validation passes; retrieval regression does not degrade; fallback diagnostics clean. | `EMBEDDING_PROVIDER=local`; retain existing vector manifest. |
| Oracle AI Vector Search active mode | Done | Schema/index validation passes; active-read parity acceptable across golden, edge, retrieval regression, smoke, and rollback cases. | Keep `RETRIEVAL_PROVIDER=oci_object_storage` as rollback. |
| Semantic retrieval active promotion | Done | Active-provider staging smoke, retrieval health, vector validation, eval suites, and rollback drill passed. | Restore `RETRIEVAL_PROVIDER=oci_object_storage` or `local_json`. |
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

Current task: `TASK-054` is blocked on approved OCI GenAI synthesis runtime configuration. `TASK-055` has its D1 guardrail prepared, but the embedding migration remains gated until `TASK-054` is live-validated and the 1536-dimension `cohere.embed-v4.0` scope change is explicitly promoted through the reindex/config sequence.

Next logical increment after review-history operator controls:

1. Add approved `OCI_GENAI_COMPARTMENT_ID` and `OCI_GENAI_CHAT_MODEL_ID` through the reviewed runtime secret/config path.
2. Run OCI GenAI synthesis parity in shadow/evaluation mode without changing `ADVISORY_SYNTHESIS_PROVIDER`.
3. Compare deterministic and OCI GenAI outputs for unsupported claims, citation coverage, required-service coverage, quality warnings, and latency/fallback behavior.
4. Keep active retrieval on `oracle_ai_vector_search`; do not change vector DB, wallet, or runtime secret settings.
5. Promote OCI GenAI synthesis only after parity passes and deterministic rollback remains proven.

## Operating Rules

- Inspect before implementing.
- Prefer the smallest promotion that produces measurable OCI-native progress.
- Keep local development and deterministic fallback working.
- Do not promote a provider without rollback proof.
- Do not make staging default changes without validation evidence.
- Commit and push validated increments continuously.
- Update this plan whenever reality changes.
