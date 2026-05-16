# OCI Architecture Studio — Status Log

Last updated: 2026-05-16

## Latest OCI Architecture Accuracy Promotion

- `TASK-050` completed as an OCI architecture recommendation accuracy increment.
- Added five Architecture Center-style reference sources for secure enterprise landing zones, EKS-to-OKE migration, Data Guard / Full Stack Disaster Recovery, analytics data lake platforms, and enterprise observability.
- Added three architecture-realism regression cases covering secure landing zones, EKS-to-OKE migration, and database DR.
- Tightened retrieval/service selection so explicit OCI services in the prompt participate in final citation selection, with security-specific priority for IAM, VCN, Vault, Cloud Guard, Audit, Logging, and Monitoring.
- Corrected AWS ECR mapping to `Container Registry` and added secure landing-zone intent classification.
- Promoted the refreshed 60-source snapshot to staging Object Storage and rebuilt Oracle AI Vector Search from the same snapshot. Staging remains `RETRIEVAL_PROVIDER=oracle_ai_vector_search`, fallback enabled but inactive.
- Secret posture: `/etc/oci-architecture-studio.env` hash remained unchanged; no runtime env values were printed or changed.
- Current Gateway retrieval health: active provider `oracle_ai_vector_search`, 60 chunks, fallback inactive, no Oracle vector store error.
- Validation passed:
  - source registry JSON validation
  - corpus health with `--min-chunks 60`
  - local retrieval regression: 18/18
  - architecture-realism retrieval regression: 7/7
  - architecture-realism evals: 7/7
  - golden evals: 18/18
  - backend full suite: `131 passed`
  - frontend lint and production build
  - VM focused backend tests: 34 passed
  - direct VM and API Gateway smoke
  - live Gateway landing-zone prompt returned security intent with IAM, VCN, Vault, Cloud Guard, Audit, and Logging as the first six evidence labels
  - hash guardrails: env unchanged, release snapshot unchanged, knowledge snapshot updated

## Latest Explainability UI

- `TASK-047` completed as a frontend-only explainability increment.
- The architecture review UI now requests retrieval debug traces for submitted reviews.
- Added a dedicated Explainability panel covering:
  - retrieval influence
  - governance influence
  - release-awareness influence
  - confidence scoring
  - service selection rationale
  - rejected alternatives
  - mapped OCI services
  - domain signals
  - selected evidence labels
- Added typed frontend support for release impact and knowledge temporal context fields returned by the backend.
- No staging runtime environment variables, retrieval provider settings, wallet files, Terraform resources, or backend service process were changed.
- Promoted the built frontend bundle and matching frontend source files to the staging VM.
- Validation passed:
  - frontend lint
  - frontend production build
  - local browser smoke against the staging API
  - staging browser smoke through the direct VM URL
  - direct VM backend/frontend smoke
  - API Gateway backend smoke
  - Gateway retrieval health remains `oracle_ai_vector_search`, 47 chunks, fallback inactive

## Latest Advisory Response Layout Refinement

- `TASK-046` completed as a frontend-only advisory readability increment.
- Added a compact Decision Snapshot to the review result covering confidence, governance posture, next move, and risk watch.
- Refined the Executive Brief with recommendation priority cards, clearer decision titles, and Markdown export iconography.
- Added implementation exit criteria, comparison evidence chips, recommendation-confidence cards, and architecture tradeoff cards.
- Fixed the Retrieval Provider Status panel so promoted Oracle AI Vector Search shows `Active read path` instead of the old shadow-only wording.
- No staging runtime environment variables, retrieval provider settings, wallet files, Terraform resources, or backend service process were changed.
- Promoted the built frontend bundle and matching frontend source files to the staging VM.
- Validation passed:
  - frontend lint
  - frontend production build
  - local browser smoke against staging API with a representative architecture prompt
  - staging frontend smoke through the direct VM URL
  - direct VM backend/frontend smoke
  - API Gateway backend smoke
  - Gateway retrieval health remains `oracle_ai_vector_search`, 47 chunks, fallback inactive
  - `git diff --check`

## Latest Oracle Vector Active-Read Promotion

- `TASK-045` completed as the gated Oracle AI Vector Search active-read promotion.
- Fixed the remaining staging blockers before promotion:
  - added Terraform-managed Run Command IAM permissions for the backend dynamic group and verified a clean inline Run Command probe
  - added explicit subnet security-list ingress for Autonomous Database TCPS `1522` from `10.20.10.0/24`
  - replaced the stale VM runtime wallet after taking a timestamped backup
  - added Oracle vector runtime env flags to `/etc/oci-architecture-studio.env` with a timestamped backup and mode `600`; secret values were fetched from OCI Vault in-process and were not printed
- Added lazy Oracle DB connection pooling for the Oracle AI Vector Search provider. This removed per-query connection overhead and brought staging parity latency down to `77.32 ms` average Oracle vector latency.
- Promoted staging to `RETRIEVAL_PROVIDER=oracle_ai_vector_search` while keeping `RETRIEVAL_FALLBACK_ENABLED=true` and `EMBEDDING_PROVIDER=local`.
- Current Gateway/direct retrieval health: active provider `oracle_ai_vector_search`, 47 chunks, fallback enabled but inactive, no Oracle vector store error.
- Rollback proof passed:
  - switched staging back to `RETRIEVAL_PROVIDER=oci_object_storage`
  - verified 47 chunks and fallback inactive
  - switched staging forward again to `oracle_ai_vector_search`
  - verified 47 chunks, fallback inactive, and service active
- Validation passed:
  - backend full suite: `129 passed`
  - frontend lint and production build
  - local retrieval regression: 18/18
  - golden evals: 18/18
  - edge evals: 8/8
  - VM targeted backend tests: 33 passed
  - VM Oracle vector validation: 18 cases, `1.0` average top-chunk overlap
  - VM Oracle vector parity: 26/26
  - VM Oracle vector retrieval regression: 18/18
  - direct VM and API Gateway smoke
  - post-promotion operational readiness passed with known warnings limited to inactive OCI DevOps metadata and one infrastructure rebuildability gap
  - Terraform staging plan reports no changes

## Latest Curated OCI Corpus Expansion

- `TASK-043` completed as a candidate-only corpus expansion increment.
- Added eight high-value official OCI source entries:
  - OCI Network Firewall
  - OCI Vulnerability Scanning
  - OCI OS Management Hub
  - OCI Container Instances
  - OCI Queue
  - OCI Health Checks
  - OCI Database Management
  - OCI Generative AI
- Updated release-impact source hints so security, networking, observability, resilience, containers, database, and AI/ML release items can map to the new sources.
- Tuned the SaaS reasoning profile to keep Logging in SaaS observability retrieval after the corpus expansion.
- Offline candidate rebuild produced 55 chunks from 55 sources, 52 services, and 15 service domains.
- No authoritative snapshot promotion, Object Storage upload, Oracle vector reload, or staging retrieval-provider change was performed.
- Validation passed:
  - source registry JSON validation
  - `py_compile` for release intelligence and architecture reasoning code
  - corpus health with `--min-chunks 55`
  - retrieval regression: 18/18
  - golden evals: 18/18
  - advisory-quality evals: 5/5
  - edge evals: 8/8
  - targeted backend reasoning/retrieval tests: 16 passed
  - `git diff --check`

## Latest OCI GenAI Embeddings Shadow Activation

- `TASK-044` completed as a shadow-only OCI GenAI embedding activation.
- Selected `cohere.embed-v4.0` as the embedding model and used the project staging compartment from Terraform output.
- Used 256 output dimensions to stay compatible with the current Oracle AI Vector Search shadow table/index dimension.
- Upgraded the OCI Python SDK pin to `2.174.0` and wired the embedding adapter to send `outputDimensions` when `OCI_GENAI_EMBEDDING_DIMENSIONS` is configured.
- Live embedding smoke passed with `cohere.embed-v4.0`, 256 dimensions, and non-empty vectors.
- Built `/tmp/oci-rag-index-task044-genai.json` with 55 chunks from 55 sources, `embedding_provider=oci_genai`, and fallback disabled.
- No authoritative snapshot promotion, Object Storage upload, Oracle vector table mutation, active embedding default change, or active retrieval-provider change was performed.
- Validation passed:
  - corpus health with `--min-chunks 55`
  - refresh candidate validation
  - retrieval regression: 18/18
  - golden evals: 18/18
  - advisory-quality evals: 5/5
  - edge evals: 8/8
  - Oracle vector local-index validation at 256 dimensions
  - embedding visibility activation readiness
  - backend embedding/retrieval/operational embedding tests: 6 passed
  - deterministic local rollback baseline retrieval regression
  - backend full test suite: 129 passed
  - frontend production build
  - frontend lint

## Latest Retrieval Provider Status Panel

- `TASK-042` completed as a read-only operational visibility increment.
- Added typed frontend API support for `/retrieval/health`.
- Added a Retrieval Provider Status panel beside the Knowledge Refresh Status panel.
- The panel surfaces active provider, chunk count, fallback state, Object Storage source posture, embedding model, service/domain coverage, and Oracle AI Vector Search shadow posture.
- No retrieval provider, refresh behavior, query-time refresh, or staging promotion setting changed.
- Validation passed:
  - frontend production build
  - frontend lint
  - backend `/retrieval/health` endpoint smoke
  - browser smoke for panel rendering and text overflow
  - `git diff --check`

## Latest Ingestion-To-Retrieval Operator Doc

- `TASK-041` completed as a docs-only operator/reviewer increment.
- Added `docs/current/ingestion-to-retrieval-flow.md` to explain the path from approved OCI docs or fallback text through source registry, fetch/normalize, chunks, metadata enrichment, embeddings, `knowledge/snapshots/oci-rag-index.json`, OCI Object Storage active retrieval, and Oracle AI Vector Search shadow sync.
- Linked the new guide from `knowledge/README.md`.
- No runtime behavior, retrieval provider, refresh policy, or staging configuration changed.
- Validation passed: `git diff --check`.

## Latest Knowledge Refresh Status Panel

- `TASK-037` through `TASK-040` completed as the first low-risk operational visibility increment after the internal beta baseline.
- Added a read-only frontend Knowledge Refresh Status panel backed by the existing `/knowledge/refresh/status` endpoint.
- The panel surfaces VM cron refresh state, last run time, gate result, promotion status, Object Storage upload status, snapshot version, changed release count, affected source count, and rollback posture.
- No query-time refresh, external scheduler, or new operational orchestration was introduced.
- Validation passed:
  - frontend production build
  - frontend lint
  - backend full test suite: `129 passed`
  - backend `/knowledge/refresh/status` endpoint subset
  - `git diff --check`
  - local browser smoke for panel render and reload
- Staging deployment passed after the panel was pushed:
  - current `main` deployed to the OCI backend VM
  - backend systemd service restarted successfully
  - OCI API Gateway smoke passed
  - direct VM rollback endpoint smoke passed
  - deployed frontend bundle contains the Knowledge Refresh Status panel
  - `/knowledge/refresh/status` returned the promoted release-watch state through both Gateway and direct VM paths

## Latest Knowledge Refresh Preflight

- `TASK-028` completed as a controlled knowledge refresh preflight before any further Oracle vector promotion work.
- Direct refresh policy preflight passed with `knowledge/refresh/refresh_policy.py --mode release-watch --no-fetch --quick-gates`.
- The preflight path reported `release-watch-no-change`, `promoted=false`, `oci_upload_performed=false`, and `authoritative_snapshots_updated=false`.
- A forced refresh against temporary snapshot copies exposed and then validated a selective-refresh fix: `refresh_policy.py` now passes embedding fallback and OCI GenAI embedding dimension settings through to `ingest.build_index`.
- The forced temp-snapshot run exercised quick gates without touching repo authoritative snapshots: retrieval health passed and retrieval regression passed 26 cases.
- Authoritative snapshot hashes remained unchanged:
  - `knowledge/snapshots/oci-rag-index.json`: `83ffb06e49c81c7829fe6cebe1d1c490e64bd70655005051ed8f7a69477d2459`
  - `knowledge/snapshots/oci-release-snapshot.json`: `cd77805429a66a2ed1289d4fae284c6762ef021ee01c7c52d357577f4b45ad32`
- Backend refresh/status regression passed: `tests/test_refresh_policy.py` and `tests/test_api.py`.
- Active retrieval remains `oci_object_storage`; Oracle AI Vector Search remains shadow-only until refresh candidate promotion and refreshed parity pass.

## Latest Refresh Candidate Quality Gate

- `TASK-029` completed as a controlled candidate-only refresh quality gate.
- Added `--candidate-only` support to `knowledge/refresh/refresh_policy.py` so changed candidates can be validated without promotion or Object Storage upload.
- Added `infra/scripts/validate_refresh_candidate.py` and wired it into post-refresh gates to validate chunk count, source metadata completeness, release snapshot integrity, and embedding dimensions.
- Controlled forced `release-watch` candidate run passed with `--no-fetch --quick-gates --force --candidate-only`.
- Candidate validation passed with 47 chunks, 5 releases, metadata schema `2026-05-oci-advisory-v2`, and no integrity errors.
- Candidate retrieval health passed and retrieval regression passed 26 cases.
- Advisory subset passed: 18/18 golden evals and 5/5 advisory-quality evals against the candidate snapshot.
- Authoritative snapshots remained unchanged and no OCI upload was performed.

## Latest Object Storage Refresh Promotion

- `TASK-030` completed as a controlled Object Storage refresh promotion.
- Promoted a validated `release-watch` candidate generated with `--no-fetch --quick-gates --force`; no query-time refresh was introduced.
- Promotion updated authoritative snapshots to:
  - `knowledge/snapshots/oci-rag-index.json`: `a451fc4db9493ff694073d8e59ed4b112691ea0f3a236b2fcd2274858b2198c0`
  - `knowledge/snapshots/oci-release-snapshot.json`: `b1bf53c9fde5ec599effedee0ee669b19b498b2029c1106112290801579c0327`
- Uploaded promoted snapshots to OCI Object Storage bucket `oci-architecture-studio-staging-knowledge-snapshots` in namespace `idsmrn7rvqb6`.
- Hardened `infra/scripts/sync_snapshots_to_object_storage.sh` so it validates promoted snapshots before upload and no longer rebuilds snapshots by default.
- Object Storage retrieval health passed with 47 chunks, 44 services, 14 service domains, and fallback inactive.
- Object Storage retrieval regression passed 26 cases.
- API Gateway smoke passed through `https://pkgmvyyi3itxklv6knh4xfm6ca.apigateway.us-ashburn-1.oci.customer-oci.com`.
- Operational readiness passed with known warnings limited to inactive OCI DevOps metadata and remaining infrastructure rebuildability gaps.
- Active retrieval remains `oci_object_storage`; Oracle AI Vector Search remains shadow-only until refreshed vector sync and parity pass.

## Latest Oracle Vector Refresh Sync

- `TASK-031` completed as an Oracle AI Vector Search shadow refresh sync.
- Copied the promoted authoritative snapshots to the staging backend VM and rebuilt the Oracle shadow index from `knowledge/snapshots/oci-rag-index.json`.
- Rebuild upserted 47 chunks into `OCI_ARCHITECTURE_CHUNKS`.
- Oracle vector health passed with valid schema, vector index `OCI_ARCH_CHUNKS_VEC_IDX`, 47 chunks, 44 services, 14 service domains, and no missing config.
- Vector validation passed 26 cases with average local latency `2.07 ms`, average Oracle vector latency `193.24 ms`, and average top-chunk overlap `0.977`.
- Temporary wallet and vector env material used for the rebuild were removed from the staging VM after validation.
- Active retrieval remains `oci_object_storage`; Oracle AI Vector Search remains shadow-only.

## Latest VM Cron Refresh Pivot

- `TASK-034` completed as a VM cron refresh dry run.
- Added `infra/scripts/run_knowledge_refresh_vm.sh` as the backend VM refresh runner.
- Added `infra/scripts/install_knowledge_refresh_vm_cron.sh` to install `/etc/cron.d/oci-architecture-studio-knowledge-refresh` on the staging backend VM.
- Cron defaults are intentionally safe: `no_fetch=true`, `quick_gates=true`, `candidate_only=true`, and `upload=false`.
- The VM path runs inside OCI Compute and uses the same repository `knowledge/refresh/refresh_policy.py`, preserving deterministic fallback and avoiding any external scheduler.
- Installed the safe cron file on staging backend VM `193.122.149.102`.
- Synced the backend VM to current repo code after the first dry run found an older `refresh_policy.py` without `--candidate-only`.
- Manual release-watch VM run passed with `status=no_change`, `passed=true`, `promoted=false`, `authoritative_snapshots_updated=false`, and `oci_upload_performed=false`.
- Manual stable-docs VM run passed candidate validation, retrieval health, and 26-case retrieval regression with `promoted=false` and `oci_upload_performed=false`.
- The VM runner now publishes latest `knowledge-refresh-status.json` and `knowledge-refresh-report.json` back to the backend-visible `knowledge/reports` path while retaining full run reports under `/var/lib/oci-architecture-studio/knowledge-refresh/reports`.
- API Gateway `/knowledge/refresh/status` now reports the latest VM release-watch dry run.
- Gateway smoke, Object Storage retrieval health, operational readiness, and Terraform no-change plan passed after the pivot.

## Latest VM Cron Release Refresh Activation

- `TASK-035` completed for VM cron release-watch activation.
- Release-watch cron now runs from the OCI backend VM with live release fetch, quick gates, candidate promotion enabled, and Object Storage upload enabled.
- Stable-docs cron remains conservative: `no_fetch=true`, `quick_gates=true`, `candidate_only=true`, and `upload=false`.
- The first live release-watch candidate was correctly blocked by gates: two live release items lacked parseable dates and the candidate caused retrieval regression misses. No authoritative snapshots were updated and no Object Storage upload occurred.
- Hardened release ingestion so undated official release items get an explicit inferred date and `release_date_inferred=true`.
- Hardened release-watch reindex behavior so live release notes can be fetched while affected knowledge-source reindexing uses stable curated fallback content by default. This keeps release freshness from destabilizing advisory retrieval.
- Added `infra/scripts/upload_snapshots_to_object_storage.py` and wired the VM runner to upload both `oci-rag-index.json` and `oci-release-snapshot.json` after successful gated promotion.
- Updated VM cron install so the `opc` cron runner can read `/etc/oci-architecture-studio.env` for non-secret runtime configuration.
- Corrected manual activation passed:
  - 12 live release items ingested
  - 47 knowledge chunks preserved
  - candidate validation passed
  - retrieval health passed
  - 26-case retrieval regression passed
  - snapshots promoted locally on the VM
  - both Object Storage objects uploaded
  - refresh status endpoint reports `status=promoted`, `passed=true`, and `oci_upload_performed=true`
- Gateway smoke, Object Storage retrieval health, operational readiness, backend refresh/API tests, and Terraform no-change plan passed after activation.
- Oracle AI Vector Search shadow was rebuilt from the promoted snapshot: 47 chunks upserted, table/index health passed, and 26-case vector validation passed with 0.977 average top-chunk overlap.
- Active retrieval remains `oci_object_storage`; Oracle AI Vector Search remains shadow-only until `TASK-036`.

## Latest Operational Promotion

- `TASK-022` completed on staging: API Gateway runtime metadata was added to the running VM environment and the backend was redeployed from the current repository code without replacing the VM.
- API Gateway smoke passed through `https://pkgmvyyi3itxklv6knh4xfm6ca.apigateway.us-ashburn-1.oci.customer-oci.com`.
- Direct backend smoke passed through `http://193.122.149.102:8000`, preserving the rollback path.
- Operational readiness now reports `api_exposure=oci_api_gateway`, `api_gateway.active=true`, and `api_gateway.promotion_ready=true`.
- Remaining runtime readiness warning is limited to OCI DevOps metadata not being configured; operator-script deployment remains the active fallback path.

## Latest Vector Search Preflight

- `TASK-023` completed as a non-mutating Terraform preflight for Oracle Autonomous AI Database / Oracle AI Vector Search shadow infrastructure.
- Terraform validation passed for staging.
- A staging plan with `enable_autonomous_vector_database=true` proposed exactly 3 creates, 0 changes, and 0 destroys:
  - `oci_core_network_security_group.autonomous_vector_db[0]`
  - `oci_core_network_security_group_security_rule.backend_to_autonomous_vector_db[0]`
  - `oci_database_autonomous_database.vector_search[0]`
- The planned database shape used private endpoint access, mTLS, ECPU compute, 2 ECPUs, 1 TB storage, `26ai`, and `LICENSE_INCLUDED`.
- No apply was run in this task; the binary plan artifact was removed because Terraform plans can carry sensitive values.

## Latest Secret Handling Hardening

- `TASK-024` completed before database apply to avoid relying on a transient shell-supplied database password.
- Terraform now generates the Autonomous Database admin password when no local sensitive override is supplied.
- Terraform also creates an OCI Vault secret named `<project>-<environment>-vector-db-admin-password` so operations have an OCI-native retrieval point for the generated credential.
- Dev, test, and staging Terraform provider locks now include the `hashicorp/random` provider used only for local IaC password generation; runtime secret storage remains OCI Vault.
- Dev/test/staging `terraform init`, `terraform fmt`, and `terraform validate` passed.
- A staging preflight with `enable_autonomous_vector_database=true` now proposes 5 creates, 0 changes, and 0 destroys: generated password, Vault secret, vector DB NSG, TCPS ingress rule, and Autonomous Database.

## Latest Vector Search Infrastructure Apply

- `TASK-025` completed on staging.
- Terraform applied exactly 5 resources, 0 changes, and 0 destroys:
  - generated database admin password
  - OCI Vault secret for the generated admin password
  - vector database network security group
  - backend-to-database TCPS ingress rule
  - Oracle Autonomous Database for Oracle AI Vector Search shadow mode
- Autonomous Database OCID: `ocid1.autonomousdatabase.oc1.iad.anuwcljr2j5jslyacn2piq4ls4olitfupf4f2cfiqidc6xtqhtq5es7x4ytq`
- Private endpoint: `stagingvectordb.adb.us-ashburn-1.oraclecloud.com`
- Admin secret OCID: `ocid1.vaultsecret.oc1.iad.amaaaaaa2j5jslyanwaml5i3cu5xibjg6vtplqbqwd7cjsjbm2vucd4d4ihq`
- Post-apply `terraform plan -detailed-exitcode` returned no changes.
- Gateway smoke, operational readiness, and backend operational/API regression tests passed.
- Active retrieval remains `oci_object_storage`; Oracle AI Vector Search is infrastructure-ready but not promoted.

## Latest Vector Search Connectivity Validation

- `TASK-026` completed.
- Backend code and validation scripts now accept `OCI_VECTOR_WALLET_LOCATION` and `OCI_VECTOR_WALLET_PASSWORD` for Autonomous Database mTLS connections.
- The staging Autonomous Database reports `AVAILABLE`.
- Backend VM TCP connectivity to the private endpoint IP `10.20.10.68:1522` passed.
- Live mTLS connection from the backend VM succeeded as `ADMIN` against service `G4454520BBA5B2F_OCIARCHVEC_low.adb.oraclecloud.com`.
- The target vector table `OCI_ARCHITECTURE_CHUNKS` does not exist yet; next task is schema creation and shadow index loading.
- Active retrieval remains `oci_object_storage`; no production read path was promoted.

## Latest Vector Search Shadow Index Load

- `TASK-027` completed.
- Wallet-aware code was deployed to the staging backend VM.
- Oracle AI Vector Search schema health passed after creating the table and vector index.
- `oracle_vector_index.py rebuild` upserted 47 chunks into `OCI_ARCHITECTURE_CHUNKS`.
- Oracle vector health reports 47 chunks, 44 services, 14 service domains, valid schema, and no missing config.
- A live retrieval validation run passed across 18 cases with average local latency `2.18 ms`, average Oracle vector latency `215.51 ms`, and average top-chunk overlap `0.967`.
- Fixed Oracle vector result materialization so LOB-backed vector serialization is read before the database connection closes.
- Staging smoke, operational readiness, and Terraform no-change validation passed after the shadow load.
- Active retrieval remains `oci_object_storage`; Oracle AI Vector Search is loaded and validated in shadow mode only.

## Active Plan

- Living execution plan: `docs/current/living-execution-plan.md`
- Two-week plan archive: `docs/archive/two-week-plan.md`

## Plan Progress

The original two-week plan is complete and archived in `docs/archive/two-week-plan.md`. Current work is tracked in `docs/current/living-execution-plan.md`.

| Status | Count | Percent of total |
|---|---:|---:|
| Done | 11 | 100% |
| In Progress | 0 | 0% |
| Not Started | 0 | 0% |
| Blocked | 0 | 0% |
| Total | 11 | 100% |

Strict completion:
- 11 of 11 original two-week tasks completed
- 100% complete

Started or partially complete:
- 11 of 11 tasks touched
- 100% started

Remaining enterprise-beta work, including ingestion-flow documentation, Retrieval Provider Status UI, corpus expansion, OCI GenAI shadow activation, and Oracle AI Vector Search active promotion gates, is tracked separately in the living execution plan.

## Completed

- Created initial monorepo scaffold.
- Added FastAPI backend with:
  - `GET /health`
  - `POST /architecture-review`
  - typed request and response models
  - environment-based configuration
  - modular API, service, model, and config structure
- Added React + Vite frontend with:
  - chat-style architecture advisor UI
  - backend API integration
  - structured rendering for recommendations, assumptions, risks, sources, and next steps
  - demo prompt shortcuts
  - loading and error states
  - intent badges and citation metadata cards
- Added local RAG foundation:
  - OCI source registry
  - ingestion script
  - document fetching with offline fallback text
  - boilerplate cleanup
  - chunking
  - citation-ready chunk metadata
  - deterministic local embeddings
  - JSON vector index
  - cosine similarity retrieval
  - metadata-aware reranking over a wider retrieval candidate set
- Added release-awareness foundation:
  - OCI release source registry
  - release ingestion script
  - release classification by service, domain, impact tags, and impact level
  - separate release snapshot under `knowledge/snapshots/oci-release-snapshot.json`
  - freshness/staleness checks for retrieved sources and release-aware prompts
- Added intent-aware orchestration:
  - `product_overview`
  - `architecture`
  - `migration`
  - `dr`
  - `cost`
  - `observability`
  - `ai_ml`
  - `security`
  - `modernization`
  - `saas_platform`
  - `analytics`
  - `release_awareness`
  - `general`
- Added intent-specific prompt templates under `prompts/`.
- Added golden prompt regression suite under `evals/golden-prompts.md`.
- Added machine-readable golden eval dataset under `evals/golden-prompts.jsonl`.
- Added edge-case eval dataset under `evals/edge-cases.jsonl`.
- Added local golden eval runner under `evals/run_golden.py`.
- Added evaluation architecture design under `docs/architecture/evaluation-architecture.md`.
- Added CI workflow under `.github/workflows/ci.yml`.
- Added backend tests for:
  - API health and architecture review
  - retrieval
  - intent classification
  - golden prompt intent-aware orchestration
  - ingestion cleanup and metadata generation
  - release ingestion and classification
  - stale-source detection
- Verified early foundation validation:
  - backend tests pass
  - frontend build passes
  - golden prompts route to expected intents
  - golden eval runner passes its then-current golden cases
  - edge-case eval runner passes 8 of 8 cases
  - eval runner now checks retrieval support and stale or unverified guidance
- Added demo readiness closeout under `docs/current/demo-readiness.md`.
- Added OCI deployment architecture and Terraform scaffold under `docs/architecture/oci-deployment-architecture.md` and `infra/terraform/`.
- Added OCI landing-zone runbook and deployment smoke test under `docs/runbooks/oci-landing-zone-runbook.md` and `infra/scripts/`.
- Added first OCI deployment execution slice:
  - staging Terraform environment
  - Compute-backed FastAPI deployment script
  - Object Storage upload scripts for frontend assets and snapshots
  - OCI access validation helper
  - release-aware deployment smoke test
  - non-secret staging runtime config template
  - local operator staging deployment scripts
- Prepared first real OCI staging inputs:
  - root-level parent compartment `oci-architecture-studio`
  - ignored local staging `terraform.tfvars`
  - project-specific SSH key for the backend VM
  - latest compatible Oracle Linux 9 platform image in `us-ashburn-1`
  - `VM.Standard.E5.Flex` backend shape
  - `8 OCPUs` and `128 GB` backend sizing
  - `baba.shaik@oracle.com` notification endpoint
- Fixed Terraform environment propagation so the `staging` environment creates staging-named resources instead of module-default `dev` names.
- Added deployment input validation:
  - deployment config schema under `infra/deploy/`
  - Terraform variable preflight validator
  - CI template validation
  - local staging deployment preflight validation before Terraform plan
- Extended OCI connectivity validation to include Monitoring alarm visibility.
- Added a compartment-level OCI Events rule to notify the configured email about resource lifecycle events in the environment compartment.
- Validated Terraform configuration for `dev`, `test`, and `staging`.
- Validated local OCI access through the configured `DEFAULT` profile.
- Completed the pre-migration validation and stability review for OCI-native retrieval migration.
- Added `docs/reports/pre-migration-readiness-report.md` with validation results, retrieval quality assessment, scenario spot checks, operational readiness findings, migration risks, rollback guidance, and the go/no-go decision.
- Added the first OCI-native retrieval migration slice:
  - optional OCI Generative AI embedding adapter
  - optional OCI Object Storage vector-manifest retrieval adapter
  - retrieval provider factory driven by environment configuration
  - `/retrieval/health` diagnostics endpoint
  - retrieval latency and result-count diagnostics
  - ingestion support for OCI embedding generation and Object Storage vector manifest upload
  - retrieval health validation script
  - `docs/architecture/oci-native-retrieval-migration.md`
- Started Sprint 2 OCI-native retrieval migration while preserving the local default:
  - added metadata-aware retrieval boosts for intent, service domain, architecture pattern, trust, freshness, and release-aware prompts
  - added per-chunk `content_hash`, `chunk_word_count`, and `vector_ready` metadata during ingestion
  - initially added a guarded `oracle_ai_vector_search` retrieval provider boundary for Phase 2 schema validation
  - added vector DB environment settings without hardcoded secrets
  - added retrieval regression reporting under `infra/scripts/retrieval_regression_check.py`
  - added `docs/runbooks/oci-native-retrieval-runbook.md`
  - added retrieval regression checks to CI and staging deployment validation workflows
- Completed the staging Terraform planning phase before first apply:
  - `terraform fmt -check -recursive` passed
  - `terraform init -input=false` passed
  - `terraform validate` passed
  - deployment config validation passed
  - fresh staging `terraform plan -out=tfplan` passed
  - plan remains 19 to add, 0 to change, 0 to destroy
  - added `docs/reports/terraform-plan-review.md`
- Completed the first OCI staging infrastructure apply:
  - Terraform apply completed with 19 added, 0 changed, 0 destroyed
  - backend VM created and deployed
  - frontend assets uploaded to Object Storage
  - knowledge and release snapshots uploaded to Object Storage
  - backend smoke test passed
  - frontend Object Storage smoke test passed
  - OCI resource visibility checks passed for bucket, secret, log group, alarm, and Events rule
  - initial retrieval health passed on the OCI-hosted backend with 13 local JSON chunks
  - added `docs/reports/oci-staging-deployment-report.md`
- Froze the current working staging baseline:
  - documented baseline commit, environment config, deployed OCI resources, verification results, known limitations, and technical debt in `docs/archive/baseline-freeze.md`
  - added `docs/runbooks/operational-runbook.md`
  - added `infra/scripts/verify_staging_baseline.py`
  - verified the live app through backend, frontend, retrieval, OCI resource, golden eval, and edge-case checks
- Renamed GitHub repository to `OCI-Architecture-Studio`.
- Promoted staging retrieval from `local_json` to `oci_object_storage` through configuration only:
  - updated `/etc/oci-architecture-studio.env` on the staging VM
  - preserved the same codebase, prompt templates, and retrieval interface
  - verified `/retrieval/health` reports `provider=oci_object_storage`
  - initially validated Object Storage manifest retrieval with 13 chunks and 10 service domains before the later 21-source corpus expansion
  - validated rollback to `local_json` and restored `oci_object_storage`
  - added `docs/reports/retrieval-provider-promotion-report.md`
- Added advisory intelligence quality foundation:
  - recommendation-to-citation evidence links
  - confidence scoring for retrieval, evidence, freshness, release-awareness, recommendations, and overall response quality
  - `not_enough_evidence`, `low_confidence`, `quality_warnings`, and `unsupported_claims` response fields
  - `/advisory/quality` operational metrics endpoint
  - advisory-quality eval suite under `evals/advisory-quality.jsonl`
  - CI advisory-quality eval gate
  - `docs/architecture/advisory-intelligence.md`
- Added GenAI advisory hardening foundation:
  - config-selected synthesis provider
  - OCI GenAI chat synthesis adapter
  - deterministic fail-closed fallback
  - synthesis provider, model, warnings, and fallback fields in the API response
  - synthesis fallback and latency observability in `/advisory/quality`
  - deterministic-vs-OCI GenAI parity checker under `infra/scripts/genai_synthesis_parity_check.py`
  - versioned local and staging config examples
  - `docs/architecture/genai-advisory-hardening.md`
- Added deterministic synthesis grounding improvements:
  - lightweight architecture pattern profiles for HA web apps, Kubernetes modernization, fintech DR, AI inference, analytics/data lake, and multi-region SaaS
  - deterministic synthesis now uses retrieved services, source chunk IDs, architecture patterns, workload/domain heuristics, and service-specific design moves
  - additive synthesis quality scoring for grounding, OCI specificity, workload alignment, migration accuracy, recommendation diversity, and citation coverage
  - expanded golden JSONL coverage for multi-region SaaS, AI inference optimization, observability modernization, secure fintech DR, Kubernetes modernization, and analytics platform scaling
- Added architecture intelligence workflow refinements:
  - concise decision reasoning metadata for major recommendations, including rationale, workload signal, tradeoffs, rejected alternatives, source chunk IDs, and confidence
  - lightweight architecture consistency validation for conflicting requirements, migration mapping coverage, HA/DR alignment, observability coverage, security coverage, and simple unsupported combination risks
  - expanded confidence scoring with service relevance, workload alignment, migration mapping certainty, and citation coverage sub-signals
  - release impact summary metadata in advisory responses
  - temporal knowledge context metadata for current snapshot plus future historical snapshot separation
  - release snapshot and temporal knowledge JSON schemas under `knowledge/metadata/`
  - expanded golden eval coverage for hybrid migration, regulated fintech, AI inference cost, enterprise observability, SaaS resiliency, and analytics DR scenarios
- Added OCI GenAI activation foundation:
  - OCI GenAI embedding path now supports deterministic fallback, missing-config diagnostics, generation-failure fallback, and optional dimension validation
  - retrieval health diagnostics expose embedding fallback state and activation errors
  - OCI GenAI synthesis now uses a dedicated retrieval-grounded prompt builder with intent, mapped OCI services, workload/domain profile, architecture pattern hints, retrieved chunks, and response structure
  - `synthesis_debug` request flag and `SYNTHESIS_DEBUG_ENABLED` config expose provider, model, selected chunks, prompt sections, estimated input tokens, token usage when available, and fallback reason
  - ingestion accepts source-level metadata overrides for service, category, workload, domain, intent, pattern, migration, HA/DR, cost, and release tags
  - ingestion supports OCI GenAI embedding fallback and optional embedding dimension validation
  - deterministic-vs-OCI GenAI comparison dataset added under `evals/genai-comparison.jsonl`
  - GenAI parity checker now reports synthesis quality signals, confidence, citations, reasoning counts, prompt sections, and fallback status
- Added supervised orchestration foundation:
  - config-selected orchestration mode through `ADVISORY_ORCHESTRATION_MODE`
  - one in-process supervisor
  - specialist routing for architecture, migration, HA/DR, cost, and release-awareness prompts
  - shared retrieval/evidence layer with no agent-specific stores
  - validation critic for evidence support, citation coverage, stale evidence, unsupported claims, and synthesis fallback
  - additive response fields for active agents, routing decision, agent trace, critic findings, and orchestration warnings
  - `/orchestration/health` endpoint for operational visibility
  - orchestration-quality eval suite under `evals/orchestration-quality.jsonl`
  - CI orchestration eval gate
  - `docs/architecture/supervised-orchestration.md`
- Added controlled multi-agent pilot:
  - default local orchestration mode is now `multi_agent_pilot`
  - deterministic specialist selection can include architecture, migration, HA/DR, cost, and release-awareness advisors
  - all specialists share the same retrieved evidence and cannot mutate retrieval, citations, confidence, or final response fields
  - one final synthesis step remains the single writer for the advisory response
  - additive response fields for `agent_contributions` and `aggregation_decision`
  - `/orchestration/health` now includes aggregation decision and active agent count
  - orchestration evals now validate multi-agent mode, specialist contribution counts, aggregation, critic findings, and rollback-safe metadata
  - `docs/architecture/controlled-multi-agent-pilot.md`
- Added retrieval precision and grounding foundation:
  - modular retrieval reranker using semantic similarity, intent match, service relevance, metadata overlap, architecture pattern match, workload/domain relevance, topic match, and migration mapping match
  - optional retrieval debug trace via request flag `retrieval_debug` or `RETRIEVAL_DEBUG_ENABLED`
  - source-service mapping expanded across Kubernetes, AWS networking, observability, security, AI/ML, and data engineering services
  - architecture-domain heuristics for ecommerce, fintech, SaaS, AI/ML inference, observability platforms, and analytics platforms
  - backend section citation metadata with chunk ID, source document, OCI service category, and service name
  - regression tests for reranking/debug traces, expanded mappings, domain heuristics, and section citations
- Added knowledge refresh policy:
  - scheduled release-note watcher policy
  - release classification to affected service, domain, impact tags, and impact level
  - selective source-ID refresh instead of full reindex by default
  - candidate-first snapshot generation before authoritative promotion
  - post-refresh retrieval regression and eval gates against candidate snapshots
  - eval-gated promotion so refreshed knowledge is not authoritative until validation passes
  - ingestion run manifests with knowledge, release, embedding, and metadata version lineage
  - manifest-driven rollback automation through `--rollback-latest`
  - `/knowledge/refresh/status` endpoint for operational visibility
  - slower stable-doc cadence guidance
  - backend OCI VM cron support for recurring refresh
  - `docs/runbooks/knowledge-refresh-policy.md`
  - `docs/runbooks/continuous-intelligence-operations.md`
- Added corpus expansion foundation:
  - expanded the local source registry to 44 curated OCI sources/chunks
  - added source-group defaults for service families, reference architectures, and architecture-center sources
  - added context-preserving chunking profiles for service docs, migration guidance, resilience/security/observability guidance, and reference architectures
  - added chunk lineage metadata including parent document, section title/path, chunk type, previous/next chunk IDs, content hash, and word count
  - added automatic chunk metadata enrichment for OCI service references, workload/domain labels, migration relevance, HA/DR relevance, cost relevance, security/compliance tags, and architecture patterns
  - added corpus health validation for chunk count, metadata completeness, missing service tags, empty embeddings, duplicate IDs/content, orphaned chunks, and coverage gaps
  - improved final retrieval selection so intent-critical services and retrieval diversity survive the larger curated corpus
- Added Oracle AI Vector Search retrieval foundation:
  - implemented optional `oracle_ai_vector_search` provider with Oracle vector table schema SQL, vector index SQL, vector similarity search, vector upsert, and metadata-aware filters
  - added config-controlled local fallback through `RETRIEVAL_FALLBACK_ENABLED`
  - added provider diagnostics for missing DB configuration, schema validity, chunk count, service/domain counts, last query metadata filters, latency, and fallback state
  - added retrieval debug fields for provider, metadata filters, and retrieved chunk diversity
  - added `infra/scripts/oracle_vector_index.py` for schema printing, local-index validation, health checks, schema creation, vector index creation, and rebuild/upsert
  - added `infra/scripts/vector_retrieval_validation.py` for honest local-vs-Oracle retrieval comparison with skip-safe behavior when DB config is unavailable
  - added `evals/vector-retrieval-cases.jsonl` for local-vs-Oracle vector retrieval comparison scenarios
- Added release intelligence impact foundation:
  - deterministic release normalization and change-category classification for new features, enhancements, deprecations, pricing/cost, security, HA/DR, observability, migration, and compatibility risk
  - impact analysis that maps releases to affected services, source IDs, chunk IDs, targeted eval cases, refresh actions, and unresolved risks
  - release overlay metadata on affected chunks for release item IDs, change categories, validity markers, and current/historical knowledge flags
  - historical snapshot retention on promoted refresh runs under `knowledge/snapshots/historical/`
  - release-aware retrieval context terms for latest/current/release prompts while preserving current-first retrieval
  - impact reporting utility under `infra/scripts/release_impact_report.py`
- Added architecture reasoning engine foundation:
  - deterministic reasoning profiles for HA/DR, migration, SaaS, fintech, AI/ML inference, analytics/data, observability, and cost-optimized workloads
  - reasoning-profile retrieval hints and service priorities that bias retrieval through the existing provider/reranker path
  - expanded pattern library coverage for multi-region HA, active/passive DR, Kubernetes modernization, event-driven systems, serverless workloads, analytics pipelines, AI inference, and secure enterprise landing zones
  - explicit tradeoff analysis for cost/resilience, performance/complexity, managed/self-managed, latency/multi-region resilience, simplicity/scalability, and flexibility/operational overhead
  - per-recommendation confidence indicators with reasoning basis, supporting chunk IDs, known limitations, and assumptions
  - reasoning trace metadata for selected profile, triggered heuristics, pattern hints, retrieval terms, service priorities, risk emphasis, and synthesis provider
  - architecture realism eval suite under `evals/architecture-realism.jsonl`
- Added evaluation intelligence foundation:
  - deterministic multidimensional architecture scoring for OCI specificity, completeness, workload alignment, migration realism, HA/DR, cost, operations, security, observability, explainability, tradeoffs, and consistency
  - hallucination heuristics for invented OCI services, unsupported certainty, stale/unverified release claims, contradictions, and unsupported migration claims
  - benchmark checks for expected services, tradeoffs, risks, migration phases, observability guidance, and security guidance
  - response-quality analytics for recommendation repetition, generic filler, OCI service frequency, pattern coverage, citation coverage, retrieval influence, workload quality, and hallucination trends
  - configurable advisory quality gate under `infra/scripts/advisory_quality_gate.py`
  - provider comparison signals in the GenAI parity checker for architecture quality, hallucination deltas, tradeoff quality, and operational realism
  - evaluation-intelligence dataset under `evals/evaluation-intelligence.jsonl`
- Added enterprise governance advisory foundation:
  - additive `enterprise_governance` response object
  - executive advisory summary, governance annotations, security posture checks, risk classifications, recommendation priorities, architecture comparisons, enterprise review findings, and auditability trace
  - deterministic review signals for security, resilience, migration governance, FinOps, operational ownership, and implementation priority
  - enterprise-governance eval suite under `evals/enterprise-governance.jsonl`
- Added enterprise platform maturity foundation:
  - additive `architecture_topology` response object with service nodes, relationships, deployment topology, HA/DR topology, operational notes, and Mermaid flow text
  - `/operations/readiness` endpoint with startup, dependency, API Gateway, OCI DevOps, runtime safeguard, fallback, and release-refresh checks
  - runtime degradation event counters in operational analytics
  - enterprise-platform-maturity eval suite under `evals/enterprise-platform-maturity.jsonl`
- Added OCI runtime production-readiness foundation:
  - additive `/operations/infrastructure` endpoint for configuration-derived OCI topology, provider, workflow, rebuildability, and gap visibility
  - Terraform `runtime_infrastructure_summary` output for deployment review and rebuild documentation
  - operational readiness checker now validates infrastructure visibility in addition to health/readiness/analytics endpoints
  - runtime-production-readiness eval suite under `evals/runtime-production-readiness.jsonl`
- Added executive experience and visualization foundation:
  - additive `executive_experience` response object with executive summary, decision brief, implementation sequence, architecture visualization summary, comparison summary, explainability highlights, and Markdown review artifact
  - frontend review-board rendering for executive brief, implementation sequence, topology/dependency summaries, decision comparisons, explainability highlights, and Markdown export
  - operational analytics counters for executive summaries, visualization generation, review artifacts, architecture comparison usage, recommendation categories, and topology role usage
  - executive-experience eval suite under `evals/executive-experience.jsonl`
- Added FinOps and migration optimization foundation:
  - additive `optimization_plan` response object with phased migration plans, modernization options, FinOps levers, workload optimization signals, optimization comparisons, implementation readiness checks, and recommendation additions
  - deterministic planning for discovery, coexistence/pilot, migration waves, rollback considerations, dependency sequencing, managed-service adoption, selective refactoring, and data-platform modernization
  - FinOps guidance for rightsizing, autoscaling, environment sizing, Object Storage lifecycle, GPU/inference cost control, and DR cost tiering using OCI-native cost-governance framing
  - frontend rendering for migration and FinOps optimization summaries
  - operational analytics counters for migration, modernization, FinOps, and workload-optimization trends
  - FinOps/migration optimization eval suite under `evals/finops-migration-optimization.jsonl`
- Added internal beta completion foundation:
  - internal beta gap assessment and readiness summary under `docs/current/internal-beta-readiness-summary.md`
  - deployed-environment readiness gate under `infra/scripts/internal_beta_readiness_check.py`
  - scheduler diagnostics now report the backend OCI VM cron refresh runtime directly
  - Terraform cloud-init and runtime profile examples align to the VM cron refresh runtime
- Added OCI-native operational hardening foundation:
  - runtime deployment profiles for local development, OCI VM, and OKE
  - additive `/operations/profile`, `/operations/health`, `/operations/readiness`, `/operations/infrastructure`, and `/operations/analytics` endpoints
  - operational metrics for provider usage, synthesis usage, fallback events, hallucination findings, governance policy triggers, governance risk trends, workload-category usage, confidence distribution, and response latency
  - OCI Vault configuration-secret readiness checks with local environment compatibility
  - OCI Logging, Audit posture, Monitoring, Notifications, and Events configuration visibility
  - optional OCI API Gateway Terraform scaffold and OCI DevOps readiness metadata; API Gateway remains disabled by default and is not active in staging unless explicitly enabled
  - cloud-init environment bootstrap for OCI VM deployments using OCI resource OCIDs generated by Terraform
  - operational readiness checker under `infra/scripts/operational_readiness_check.py`

## Latest Validation

Last validation run: 2026-05-15

- Terraform formatting: passed
- Terraform validation:
  - `infra/terraform/envs/dev`: passed
  - `infra/terraform/envs/test`: passed
  - `infra/terraform/envs/staging`: passed
- Terraform staging plan: passed, 19 to add, 0 to change, 0 to destroy
- Terraform staging plan target: `oci-architecture-studio-staging`
- Terraform staging compute image: `Oracle-Linux-9.7-2026.04.30-3`
- Terraform staging compute shape: `VM.Standard.E5.Flex`
- Terraform staging compute size: `8 OCPUs`, `128 GB`
- Deployment config validation: passed
- GitHub CI workflow YAML parsing: passed
- Infrastructure Python script compile checks: passed
- Knowledge ingestion smoke: passed, 47 chunks generated locally from 47 registry sources
- Release ingestion smoke: passed, 5 release items generated in offline fallback mode
- Release impact report: passed with deterministic classification, impacted source/chunk mapping, targeted eval impact detection, refresh action reporting, and unresolved-risk reporting
- Knowledge refresh policy smoke: passed in offline `release-watch` quick-gate mode
- Continuous intelligence hardening: candidate-first promotion, version lineage, rollback automation, and refresh status endpoint implemented
- Terraform validation: passed after backend VM cron refresh support; staging plan currently should not be applied until existing backend replacement drift is resolved
- OCI-native refresh scheduler: backend OCI VM cron is the active staging path
- Backend tests: passed, 126 tests
- Frontend build: passed
- Golden evals: passed, 18 of 18
- Edge-case evals: passed, 8 of 8
- Advisory-quality evals: passed, 5 of 5
- Controlled orchestration evals: passed, 5 of 5
- Architecture-realism evals: passed, 4 of 4
- Evaluation-intelligence evals: passed, 9 of 9
- Enterprise-governance evals: passed, 5 of 5
- Enterprise-platform-maturity evals: passed, 4 of 4
- Runtime-production-readiness evals: passed, 3 of 3
- Executive-experience evals: passed, 3 of 3
- FinOps-migration-optimization evals: passed, 4 of 4
- Advisory quality gate: passed against the evaluation-intelligence report with MVP thresholds
- Internal beta readiness gate: passed locally and against OCI staging for governance, executive, topology, migration/FinOps, release, retrieval, and operational diagnostics checks
- Operational hardening tests: passed in targeted API/diagnostics suite
- Operational readiness check: passed locally against `/health`, `/retrieval/health`, `/operations/health`, `/operations/readiness`, `/operations/infrastructure`, and `/operations/analytics`; API Gateway and OCI DevOps are expected readiness warnings until configured
- Runtime readiness endpoint: passed locally in targeted API tests
- Retrieval health check: passed for `local_json`, 47 chunks
- Retrieval health check with `EMBEDDING_PROVIDER=oci_genai` and missing OCI GenAI env vars: passed through deterministic embedding fallback
- Retrieval regression check: passed for `local_json`, 18 of 18 configured cases
- Oracle AI Vector Search fallback health: passed locally with fallback active when Oracle DB settings are absent
- Oracle vector local-index validation: passed for 47 chunks at 256 dimensions
- Oracle vector retrieval validation: generated a skip-safe report because Oracle DB settings were not provided
- GenAI comparison eval: skipped live OCI GenAI path because required OCI GenAI env vars were not present; deterministic side of 4 comparison cases passed and report was generated
- GenAI parity readiness check: passed in skip-safe mode when OCI GenAI env vars are not provided
- Python compile checks: passed for backend, infra scripts, ingestion, and refresh code
- Diff whitespace check: passed
- Local API smoke: passed for `/health`, `/architecture-review`, and `/orchestration/health`, including `multi_agent_pilot` with 3 specialist contributions
- OCI local access check: passed, Object Storage namespace `idsmrn7rvqb6`
- Local deployment smoke test: passed, including architecture and release-aware citation paths
- Pre-migration readiness review: passed with a go decision for incremental OCI-native retrieval migration behind configuration
- OCI staging apply: passed, 19 resources added
- OCI staging backend smoke: passed, including architecture and release-aware citations
- OCI staging frontend smoke: passed
- OCI staging baseline guardrail: passed against `http://193.122.149.102:8000/`
- OCI staging deployment smoke: passed for backend, frontend, and OCI SDK tenancy access
- OCI staging resource visibility smoke: passed for Object Storage bucket, Vault secret, Logging log group, Monitoring alarm, and Events rule
- Post-migration readiness review: passed with a go decision for continued Sprint 2 development
- Dual-provider retrieval parity validation: passed, 26 of 26 cases, comparing `local_json` with `oci_object_storage`
- OCI Object Storage snapshot sync: passed for `oci-rag-index.json` and `oci-release-snapshot.json`
- Staging retrieval provider promotion: passed, active provider is now `oci_object_storage`
- Staging redeploy from the latest audited working tree: passed
- Staging endpoint parity: passed for `/health`, `/architecture-review`, `/retrieval/health`, `/advisory/quality`, `/orchestration/health`, and `/knowledge/refresh/status`
- Staging retrieval snapshot: passed with `oci_object_storage`, 47 chunks, 44 services, and 14 service domains after Object Storage snapshot sync
- Staging enterprise governance smoke: passed, including `enterprise_governance` response metadata and governance analytics counters
- Post-promotion baseline guardrail: passed with expected provider `oci_object_storage`
- Post-promotion deployment smoke: passed for backend, frontend, and OCI SDK tenancy access
- Post-promotion OCI resource visibility smoke: passed for Object Storage bucket, Vault secret, Logging log group, Monitoring alarm, and Events rule
- Post-promotion live scenario checks: passed for architecture, migration, HA/DR, cost, and release-awareness
- Rollback validation: passed, `local_json` was restored and then `oci_object_storage` was restored without code or prompt changes; the restore runbook now preserves or restores SELinux context on `/etc/oci-architecture-studio.env`
- OCI Object Storage-provider eval parity: passed for golden evals, edge evals, and retrieval regression against the staging snapshot bucket
- OCI API Gateway staging apply: passed for gateway and deployment; Gateway endpoint `https://pkgmvyyi3itxklv6knh4xfm6ca.apigateway.us-ashburn-1.oci.customer-oci.com/` smoke and operational readiness passed, direct backend VM rollback path remains healthy, and post-apply Terraform plan reports no changes
- Presentation-friendly architecture diagrams: added in `docs/architecture/architecture-diagrams.md`
- Documentation refresh: README, PRD, roadmap, vision, sprint docs, runbooks, demo readiness, architecture docs, promotion report, GenAI hardening notes, and supervised orchestration notes now reflect the current promoted staging state
- Release Context advisory UI: added an executive-grade release visibility panel with release match counts, affected services, recommendation-affecting services, impact/change categories, snapshot timing, temporal boundary, and release maturity notes. Validation passed frontend lint/build, backend full suite, 18/18 retrieval regression, local deployment smoke, staging direct/API Gateway smoke, Oracle vector retrieval health, env/snapshot hash guardrails, and browser smoke with a release-aware prompt.
- Architecture Map advisory UI: added a lightweight visualization panel with topology/deployment/HA-DR summaries, lane-based OCI service map, service relationship evidence, implementation path, and operational notes. Validation passed frontend lint/build, focused topology/API tests, backend full suite, 18/18 retrieval regression, local deployment smoke, staging direct/API Gateway smoke, Oracle vector retrieval health, env/snapshot hash guardrails, and browser smoke with a representative topology prompt.

## Pending

- Replace deterministic local hash embeddings with a production embedding provider when model/provider decisions are finalized.
- Run OCI Generative AI embedding ingestion against the approved staging compartment and upload the vector manifest to Object Storage.
- Keep Oracle AI Vector Search active-read health current with periodic smoke, regression, parity, and rollback validation.
- Expand OCI source coverage for:
  - Budgets-specific documentation
  - Data Guard-specific documentation
  - deeper workload architecture sources
- Improve HTML ingestion quality to remove more documentation boilerplate.
- Add richer source metadata:
  - source version/date
  - per-service owners
  - source freshness policy
- Extend release-awareness workflow:
  - explicit current-vs-historical recommendation comparison
  - stronger release source parsing for point-in-time snapshots
  - richer release-to-source mapping coverage as the corpus expands
- Continue hardening advisory synthesis:
  - provide `OCI_GENAI_COMPARTMENT_ID` and `OCI_GENAI_CHAT_MODEL_ID` for live OCI GenAI parity validation
  - enable OCI GenAI synthesis in staging only after deterministic-vs-OCI GenAI parity passes without fallback
  - strengthen unsupported-claim suppression beyond current requested-service warnings
- Continue hardening controlled orchestration:
  - keep agent routing deterministic and observable
  - add policy-gate behavior only after enough critic or specialist disagreement failures appear in evals or staging telemetry
  - avoid autonomous planning loops until the supervised flow has stable quality data
- Add frontend improvements:
  - prompt history
- Move Terraform state to OCI Object Storage before shared/team usage.
- Put the backend behind HTTPS through OCI API Gateway or Load Balancer before production use. Optional API Gateway Terraform scaffolding exists but is disabled by default in staging.

## In Progress

- Ingestion cleanup:
  - common script/style/footer/help boilerplate cleanup exists
  - more Oracle documentation boilerplate cleanup is still needed
- Source metadata:
  - current index includes source URL, service, service domain, service category, workload/domain tags, topic, migration mappings, HA/DR and cost tags, intent tags, fetched timestamp, freshness score, trust level, architecture patterns, chunk index, and fetch status
  - still needs source version/date and richer ownership metadata
- Source registry expansion:
  - expanded to 44 local registry sources/chunks covering core networking, containers, database, storage, observability, security, cost, data/analytics, AI/ML, DevOps, and selected reference architecture topics
  - still needs Budgets-specific, Data Guard-specific, and deeper workload architecture sources
- Release-awareness and continuous intelligence:
  - release-aware intent, prompt template, release registry, release ingestion, and release snapshot reader exist
  - scheduled refresh automation and candidate-first promotion now exist
  - refresh status and rollback manifests now exist
  - deterministic impact analysis, release overlay tagging, impacted eval reporting, and historical snapshot retention now exist
  - full bi-temporal retrieval and automatic current-vs-historical answer comparison remain future work
- OCI deployment execution:
  - Terraform, scripts, config templates, workflow, and docs exist
  - staging values, plan files, and secrets are ignored by git
  - initial staging cloud apply/deploy is complete and baseline-frozen
- OCI-native retrieval migration:
  - Phase 1 configuration hooks, metadata enrichment, Object Storage manifest path, health checks, and regression checks exist
  - Object Storage manifest retrieval is the active staging provider
  - `local_json` remains the validated rollback provider
  - Oracle AI Vector Search provider code, schema/upsert/search tooling, fallback safety, Autonomous Database infrastructure, table/index, and shadow validation exist
- Oracle AI Vector Search is the active staging read path after refreshed active-provider parity, smoke, regression, operational readiness, and rollback checks passed
  - post-migration readiness report is captured in `docs/reports/post-migration-readiness-report.md`
  - dual-provider parity report is captured in `docs/reports/retrieval-parity-validation-report.md`
  - promotion report is captured in `docs/reports/retrieval-provider-promotion-report.md`
- Controlled orchestration:
  - active as an additive backend response layer by default in local config through `multi_agent_pilot`
  - rollback modes are `ADVISORY_ORCHESTRATION_MODE=supervised` and `ADVISORY_ORCHESTRATION_MODE=single_pass`
  - specialist agents are deterministic role boundaries, not autonomous workers
  - validation critic currently reports findings and warnings; it does not block responses yet
  - final response synthesis remains single-writer through the configured synthesis provider
- Synthesis quality:
  - deterministic synthesis uses reusable architecture pattern profiles and retrieved evidence
  - deterministic reasoning profiles influence retrieval hints, synthesis guidance, tradeoff analysis, and recommendation confidence metadata
  - synthesis quality signals are available in the backend response
  - OCI GenAI remains optional and must pass parity validation before staging activation
- Retrieval quality:
  - reranking and domain heuristics are implemented and covered by tests
  - optional debug traces expose provider, detected intent, mapped OCI services, metadata filters, candidate chunks, score adjustments, retrieved chunk diversity, and selected final chunks
  - final chunk selection now protects intent-critical architecture services before generic diversity fill
  - section citation metadata is available in the backend response
  - full section-level citation rendering in the frontend remains future work

## Current Known Limitations

- The local RAG index is a curated 47-chunk corpus, not a complete OCI documentation corpus.
- Embeddings are deterministic local hash embeddings, useful for workflow validation but not production semantic retrieval.
- Reranking improves ordering and traceability but still depends on the curated corpus and local hash embeddings.
- Oracle AI Vector Search code, tooling, live DB connection, table/index, and active staging reads are implemented and promoted with Object Storage as the immediate rollback provider.
- Release awareness has scheduled VM-cron snapshot refresh, deterministic impact analysis, candidate validation, historical snapshot retention, Object Storage upload, and status visibility; it does not yet perform full current-vs-historical answer comparison or full bi-temporal retrieval.
- OCI GenAI synthesis adapter exists, but deterministic synthesis remains the rollback-safe default unless enabled by environment configuration.
- Deterministic architecture patterns improve fallback usefulness but are still heuristic and bounded by the retrieved corpus.
- Deterministic reasoning profiles improve explainability and tradeoff structure, but they are heuristic and do not replace expert OCI solution review.
- FinOps and migration optimization metadata is deterministic and advisory. It recommends OCI-native cost-governance practices such as Budgets/Cost Analysis review cadence, but it does not call live billing APIs or calculate tenancy spend.
- Evaluation intelligence uses deterministic heuristics and configurable thresholds. It is useful for regression control, hallucination risk detection, and provider comparison, but it is not an objective architecture correctness oracle or LLM-as-judge system.
- Controlled multi-agent orchestration is currently an in-process control layer; it does not yet perform autonomous planning, tool use, or multi-step agent memory.
- Operational diagnostics are additive and lightweight. They do not replace OCI Monitoring alarms, OCI Logging ingestion, or a production incident-management process.
- Generated vector snapshots are local and gitignored.
- Staging uses OCI API Gateway for the promoted ingress path and keeps direct backend port `8000` as a rollback path; production HA and hardened HTTPS/custom-domain ingress remain future work.
