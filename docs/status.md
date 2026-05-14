# OCI Architecture Studio — Status Log

Last updated: 2026-05-14

## Active Plan

- Two-week plan: `docs/two-week-plan.md`

## Plan Progress

Current two-week task count:

| Status | Count | Percent of total |
|---|---:|---:|
| Done | 10 | 91% |
| In Progress | 1 | 9% |
| Not Started | 0 | 0% |
| Blocked | 0 | 0% |
| Total | 11 | 100% |

Strict completion:
- 10 of 11 tasks completed
- 91% complete

Started or partially complete:
- 11 of 11 tasks touched
- 100% started

Weighted progress estimate:
- Done tasks count as 100%
- In-progress tasks count as 50%
- Current weighted progress: 95%

This progress is based on `docs/two-week-plan.md`.

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
  - `security`
  - `release_awareness`
  - `general`
- Added intent-specific prompt templates under `prompts/`.
- Added golden prompt regression suite under `evals/golden-prompts.md`.
- Added machine-readable golden eval dataset under `evals/golden-prompts.jsonl`.
- Added edge-case eval dataset under `evals/edge-cases.jsonl`.
- Added local golden eval runner under `evals/run_golden.py`.
- Added evaluation architecture design under `docs/evaluation-architecture.md`.
- Added CI workflow under `.github/workflows/ci.yml`.
- Added backend tests for:
  - API health and architecture review
  - retrieval
  - intent classification
  - golden prompt intent-aware orchestration
  - ingestion cleanup and metadata generation
  - release ingestion and classification
  - stale-source detection
- Verified current validation:
  - backend tests pass
  - frontend build passes
  - golden prompts route to expected intents
  - golden eval runner passes 6 of 6 cases
  - edge-case eval runner passes 8 of 8 cases
  - eval runner now checks retrieval support and stale or unverified guidance
- Added demo readiness closeout under `docs/demo-readiness.md`.
- Added OCI deployment architecture and Terraform scaffold under `docs/oci-deployment-architecture.md` and `infra/terraform/`.
- Added OCI landing-zone runbook and deployment smoke test under `docs/oci-landing-zone-runbook.md` and `infra/scripts/`.
- Added first OCI deployment execution slice:
  - staging Terraform environment
  - Compute-backed FastAPI deployment script
  - Object Storage upload scripts for frontend assets and snapshots
  - OCI access validation helper
  - release-aware deployment smoke test
  - non-secret staging runtime config template
  - manual GitHub Actions staging deployment workflow
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
  - staging deployment workflow validation before Terraform plan
- Extended OCI connectivity validation to include Monitoring alarm visibility.
- Added a compartment-level OCI Events rule to notify the configured email about resource lifecycle events in the environment compartment.
- Validated Terraform configuration for `dev`, `test`, and `staging`.
- Validated local OCI access through the configured `DEFAULT` profile.
- Completed the pre-migration validation and stability review for OCI-native retrieval migration.
- Added `docs/pre-migration-readiness-report.md` with validation results, retrieval quality assessment, scenario spot checks, operational readiness findings, migration risks, rollback guidance, and the go/no-go decision.
- Added the first OCI-native retrieval migration slice:
  - optional OCI Generative AI embedding adapter
  - optional OCI Object Storage vector-manifest retrieval adapter
  - retrieval provider factory driven by environment configuration
  - `/retrieval/health` diagnostics endpoint
  - retrieval latency and result-count diagnostics
  - ingestion support for OCI embedding generation and Object Storage vector manifest upload
  - retrieval health validation script
  - `docs/oci-native-retrieval-migration.md`
- Completed the staging Terraform planning phase before first apply:
  - `terraform fmt -check -recursive` passed
  - `terraform init -input=false` passed
  - `terraform validate` passed
  - deployment config validation passed
  - fresh staging `terraform plan -out=tfplan` passed
  - plan remains 19 to add, 0 to change, 0 to destroy
  - added `docs/terraform-plan-review.md`
- Completed the first OCI staging infrastructure apply:
  - Terraform apply completed with 19 added, 0 changed, 0 destroyed
  - backend VM created and deployed
  - frontend assets uploaded to Object Storage
  - knowledge and release snapshots uploaded to Object Storage
  - backend smoke test passed
  - frontend Object Storage smoke test passed
  - OCI resource visibility checks passed for bucket, secret, log group, alarm, and Events rule
  - retrieval health passed on the OCI-hosted backend with 13 local JSON chunks
  - added `docs/oci-staging-deployment-report.md`
- Renamed GitHub repository to `OCI-Architecture-Studio`.
- Pushed current implementation to GitHub.

## Latest Validation

Last validation run: 2026-05-14

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
- GitHub workflow YAML parsing: passed
- Infrastructure Python script compile checks: passed
- Knowledge ingestion smoke: passed, 13 chunks generated
- Release ingestion smoke: passed, 3 release items generated
- Backend tests: passed, 26 tests
- Frontend build: passed
- Golden evals: passed, 6 of 6
- Edge-case evals: passed, 8 of 8
- Retrieval health check: passed for `local_json`, 13 chunks
- OCI local access check: passed, Object Storage namespace `idsmrn7rvqb6`
- Local deployment smoke test: passed, including architecture and release-aware citation paths
- Pre-migration readiness review: passed with a go decision for incremental OCI-native retrieval migration behind configuration
- OCI staging apply: passed, 19 resources added
- OCI staging backend smoke: passed, including architecture and release-aware citations
- OCI staging frontend smoke: passed
- OCI staging resource visibility smoke: passed

## Pending

- Replace deterministic local hash embeddings with a production embedding provider when model/provider decisions are finalized.
- Add a production vector store adapter while keeping the current JSON vector store for local development.
- Add an OCI-native retrieval adapter behind configuration and dual-run it against the current local JSON vector store before changing defaults.
- Implement the Oracle AI Vector Search adapter after Object Storage manifest parity is validated.
- Expand OCI source coverage for:
  - dedicated WAF
  - dedicated Vault
  - dedicated Cloud Guard
  - dedicated Logging
  - dedicated Monitoring
  - Budgets-specific documentation
- Improve HTML ingestion quality to remove more documentation boilerplate.
- Add richer source metadata:
  - source version/date
  - per-service owners
  - source freshness policy
- Implement real release-awareness workflow:
  - architecture impact analysis
  - explicit current-vs-historical recommendation comparison
- Add stronger response generation:
  - actual prompt execution with an LLM
  - citation-aware answer synthesis
  - unsupported-claim checks
  - structured confidence or evidence notes
- Add frontend improvements:
  - prompt history
- Move Terraform state to OCI Object Storage before shared/team usage.
- Put the backend behind HTTPS through API Gateway or Load Balancer before production use.

## In Progress

- Ingestion cleanup:
  - common script/style/footer/help boilerplate cleanup exists
  - more Oracle documentation boilerplate cleanup is still needed
- Source metadata:
  - current index includes source URL, service, service domain, intent tags, fetched timestamp, freshness score, trust level, architecture patterns, chunk index, and fetch status
  - still needs source version/date and richer ownership metadata
- Source registry expansion:
  - added OKE, database migration, Full Stack Disaster Recovery, Cost Management, Security Services, Object Storage, and CDN / edge services
  - still needs dedicated WAF, Vault, Cloud Guard, Logging, Monitoring, and Budgets-specific sources
- Release-awareness scaffold:
  - release-aware intent, prompt template, release registry, release ingestion, and release snapshot reader exist
  - impact comparison is not implemented yet
- OCI deployment execution:
  - Terraform, scripts, config templates, workflow, and docs exist
  - staging values and plan are prepared locally and ignored by git
  - actual cloud apply/deploy is the next operator step and requires explicit approval

## Current Known Limitations

- The local RAG index is small and not a complete OCI documentation corpus.
- Embeddings are deterministic local hash embeddings, useful for workflow validation but not production semantic retrieval.
- Release awareness has a local release snapshot foundation, but it is not yet a full live release intelligence workflow.
- The backend returns intent-profiled recommendations, but full LLM-based synthesis is not implemented yet.
- Generated vector snapshots are local and gitignored.
- The first OCI deployment exposes the backend directly on port `8000`; this is acceptable for staging validation but should be replaced with HTTPS ingress before demo/prod.
