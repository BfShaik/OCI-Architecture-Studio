# OCI Architecture Studio — Internal Beta Readiness Summary

Date: 2026-05-16

Validated baseline: current `main` after TASK-055 and UI closeout v1.0.4

## Readiness Position

OCI Architecture Studio is ready for a controlled enterprise internal beta after the validation gates listed below pass on the target environment.

This milestone is an internal beta baseline, not a production HA certification. The platform is deployable and operable in OCI staging, has deterministic fallback behavior, exposes advisory traceability, and has regression coverage across retrieval, governance, migration, FinOps, release intelligence, runtime diagnostics, and executive usability.

## Platform Gap Assessment

| Area | Current State | Internal Beta Decision |
|---|---|---|
| Retrieval | `oracle_ai_vector_search` is active in staging with 60 chunks. `oci_object_storage` remains the immediate rollback provider and `local_json` remains the local fallback. | Accept for beta. Keep Object Storage snapshots aligned with the active Oracle vector index. |
| Advisory synthesis | OCI GenAI synthesis is active in staging through `ADVISORY_SYNTHESIS_PROVIDER=oci_genai`; deterministic synthesis remains the config-only rollback path. | Accept for beta. Continue monitoring quality, fallback, latency, and cost before production promotion. |
| Governance | Deterministic governance annotations, risk classification, security posture checks, prioritization, comparisons, and auditability trace exist. | Accept for beta as human-review metadata, not policy enforcement. |
| Migration and FinOps | `optimization_plan` adds phased migration, modernization options, FinOps levers, workload optimization, comparisons, and implementation readiness. | Accept for beta. It is heuristic advisory guidance and does not call live OCI billing APIs. |
| Release intelligence | Release ingestion, normalization, impact analysis, overlays, historical snapshot retention, release-aware response metadata, and VM-cron release-watch refresh with gated Object Storage upload exist. | Accept for beta. Full current-vs-historical answer comparison and full bi-temporal retrieval remain future work. |
| Runtime deployment | OCI VM staging and OCI API Gateway ingress are active, with direct VM rollback preserved. OKE profile examples exist. OCI DevOps metadata is scaffolded but not active in staging. | Accept for beta with documented readiness warnings. Keep direct VM rollback until production ingress hardening is complete. |
| IaC | Terraform covers compartment, VCN/subnet, gateway, route/security, Compute, Object Storage, Vault/key/secret, Logging, Monitoring alarm, Notifications, Events, optional API Gateway, IAM dynamic groups/policies, backend VM cron refresh support, and rebuild outputs. | Accept for beta. Move Terraform state to OCI Object Storage before team/shared operations. |
| Observability | Operational endpoints expose health, readiness, infrastructure, analytics, provider usage, fallback events, governance trends, recommendation trends, and runtime degradation counters. OCI Logging/Monitoring/Notifications/Event OCIDs are visible when configured. | Accept for beta. Custom metric export to OCI Monitoring is a later hardening task. |
| Evaluation | Golden, edge, advisory, orchestration, architecture realism, evaluation intelligence, governance, platform maturity, runtime readiness, executive experience, FinOps/migration, retrieval regression, vector skip-safe, and provider-parity tooling exist. | Accept for beta. Keep eval additions tied to real failures and platform gaps. |
| Executive usability | Executive summaries, decision briefs, implementation sequence, topology summaries, comparisons, explainability highlights, Markdown artifact, and migration/FinOps UI exist. | Accept for beta. Full diagram rendering and presentation generation remain future work. |

## Prioritized Remediation Completed In This Closeout

1. Added `infra/scripts/internal_beta_readiness_check.py` as a single high-signal internal beta gate for deployed environments.
2. Improved scheduler diagnostics so refresh readiness reports the backend OCI VM cron path directly.
3. Removed the unused serverless scheduler scaffold after choosing the VM cron runtime.
4. Added regression coverage for scheduler diagnostic visibility.
5. Added release-refresh lifecycle reporting so candidate creation, gate status, promotion, upload, rollback, and query-time refresh posture are visible in one report.
6. Synced the refreshed 47-chunk knowledge snapshot and release snapshot to OCI Object Storage staging.
7. Updated this readiness summary and related docs to keep internal beta claims precise.

## Accepted Internal Beta Limitations

- OCI API Gateway is active for staging ingress, but the direct backend VM endpoint remains available as a rollback path.
- OCI DevOps is not configured for active staging deployment; local operator scripts remain the current deployment mechanism.
- Oracle AI Vector Search active reads are implemented and validated in staging; Object Storage remains the immediate rollback path.
- OCI GenAI synthesis and OCI GenAI embeddings are active in staging; deterministic synthesis, Object Storage retrieval, and local-hash embeddings remain rollback/development paths.
- The corpus is curated and intentionally small; it is not a complete OCI documentation mirror.
- Cost guidance is deterministic FinOps advisory logic. It does not inspect live tenancy spend or call OCI Cost Analysis APIs.
- Release awareness uses snapshots and deterministic impact logic. It does not yet provide full current-vs-historical answer comparison.
- Architecture visualization is lightweight topology metadata and UI summaries, not a full diagramming engine.

## Internal Beta Gate

Run this against a live environment:

```bash
PYTHONPATH=app/backend/src app/backend/.venv/bin/python infra/scripts/internal_beta_readiness_check.py \
  --api-base-url http://193.122.149.102:8000 \
  --require-oci-profile \
  --output-dir evals/reports/internal-beta-readiness
```

The gate validates:

- backend health
- retrieval health and chunk baseline
- operational health/readiness/infrastructure/analytics endpoints
- accepted staging readiness warnings
- governance/executive/topology metadata
- migration/FinOps optimization metadata
- release/temporal metadata
- citations and confidence visibility

## Full Validation Baseline

Run these before tagging a new internal beta baseline:

```bash
cd app/backend
PYTHONPATH=src .venv/bin/python -m pytest tests

cd ../frontend
npm run build

cd ../..
PYTHONPATH=app/backend/src app/backend/.venv/bin/python evals/run_golden.py --output-dir evals/reports/golden
PYTHONPATH=app/backend/src app/backend/.venv/bin/python evals/run_golden.py --cases evals/edge-cases.jsonl --output-dir evals/reports/edge-cases
PYTHONPATH=app/backend/src app/backend/.venv/bin/python evals/run_golden.py --cases evals/advisory-quality.jsonl --output-dir evals/reports/advisory-quality
PYTHONPATH=app/backend/src app/backend/.venv/bin/python evals/run_golden.py --cases evals/orchestration-quality.jsonl --output-dir evals/reports/orchestration-quality
PYTHONPATH=app/backend/src app/backend/.venv/bin/python evals/run_golden.py --cases evals/architecture-realism.jsonl --output-dir evals/reports/architecture-realism
PYTHONPATH=app/backend/src app/backend/.venv/bin/python evals/run_golden.py --cases evals/evaluation-intelligence.jsonl --output-dir evals/reports/evaluation-intelligence
PYTHONPATH=app/backend/src app/backend/.venv/bin/python evals/run_golden.py --cases evals/enterprise-governance.jsonl --output-dir evals/reports/enterprise-governance
PYTHONPATH=app/backend/src app/backend/.venv/bin/python evals/run_golden.py --cases evals/enterprise-platform-maturity.jsonl --output-dir evals/reports/enterprise-platform-maturity
PYTHONPATH=app/backend/src app/backend/.venv/bin/python evals/run_golden.py --cases evals/runtime-production-readiness.jsonl --output-dir evals/reports/runtime-production-readiness
PYTHONPATH=app/backend/src app/backend/.venv/bin/python evals/run_golden.py --cases evals/executive-experience.jsonl --output-dir evals/reports/executive-experience
PYTHONPATH=app/backend/src app/backend/.venv/bin/python evals/run_golden.py --cases evals/finops-migration-optimization.jsonl --output-dir evals/reports/finops-migration-optimization
PYTHONPATH=app/backend/src app/backend/.venv/bin/python infra/scripts/retrieval_regression_check.py --output-dir evals/reports/retrieval
PYTHONPATH=app/backend/src app/backend/.venv/bin/python infra/scripts/vector_retrieval_validation.py --allow-skip --output-dir evals/reports/vector-retrieval

terraform fmt -check -recursive infra/terraform
terraform -chdir=infra/terraform/envs/dev validate
terraform -chdir=infra/terraform/envs/test validate
terraform -chdir=infra/terraform/envs/staging validate
```

For staging, also run:

```bash
PYTHONPATH=app/backend/src app/backend/.venv/bin/python infra/scripts/smoke_oci_deployment.py \
  --api-base-url http://193.122.149.102:8000 \
  --frontend-url http://193.122.149.102:8000/ \
  --check-oci-sdk

PYTHONPATH=app/backend/src app/backend/.venv/bin/python infra/scripts/operational_readiness_check.py \
  --api-base-url http://193.122.149.102:8000 \
  --require-oci-profile

curl -sS https://pkgmvyyi3itxklv6knh4xfm6ca.apigateway.us-ashburn-1.oci.customer-oci.com/retrieval/health
```

## Milestone Tagging

After the full validation baseline passes and staging is refreshed, create a stable milestone tag:

```bash
git tag -a v1.0.1 -m "OCI Architecture Studio v1.0.1 internal beta baseline"
git tag -a internal-beta-2026-05-15-r2 -m "Internal beta baseline refresh"
git push origin v1.0.1 internal-beta-2026-05-15-r2
```

Use a new version tag for code baselines and a date/revision-suffixed internal beta tag when a same-day beta baseline already exists. Do not move existing baseline tags.

## Latest Current-State Validation

The current `main`/staging posture on 2026-05-16 includes:

- Active staging retrieval: `oracle_ai_vector_search`, 60 chunks, fallback inactive, no store error.
- Backend full suite: 132 passed.
- TASK-052 section traceability: local/staging backend, frontend, retrieval, eval, direct/API Gateway, and browser smokes passed.
- TASK-053 review-history operator controls: focused API tests, backend full suite, frontend lint/build, local smoke, staging focused tests, direct/API Gateway smoke, Gateway redaction/export smoke, staging browser smoke, retrieval health, and env hash guardrail passed.
- Runtime env hash remained unchanged during the latest UI/API promotions.

## Latest Baseline Validation

The `v1.0.1` validation on 2026-05-15 passed:

- Backend tests: 126 passed.
- Frontend build: passed.
- Golden evals: 18 of 18 passed.
- Edge-case evals: 8 of 8 passed.
- Advisory-quality evals: 5 of 5 passed.
- Orchestration-quality evals: 5 of 5 passed.
- Architecture-realism evals: 4 of 4 passed.
- Evaluation-intelligence evals: 9 of 9 passed.
- Enterprise-governance evals: 5 of 5 passed.
- Enterprise-platform-maturity evals: 4 of 4 passed.
- Runtime-production-readiness evals: 3 of 3 passed.
- Executive-experience evals: 3 of 3 passed.
- FinOps-migration-optimization evals: 4 of 4 passed.
- Local retrieval regression: 18 of 18 passed against the latest architecture-accuracy corpus.
- Object Storage retrieval parity: passed against the refreshed staging snapshot before Oracle vector promotion.
- Oracle AI Vector Search active-read promotion: passed parity, retrieval regression, staging smoke, rollback drill, and later 60-chunk architecture corpus validation.
- OCI GenAI synthesis parity and go-live validation passed for staging; public `/architecture-review` returns `synthesis_provider=oci_genai` with fallback disabled.
- Terraform validation: dev, test, and staging validated after backend-disabled init.
- Deployment config validation: passed for staging tfvars.
- Terraform remote-state readiness: passed in non-mutating `--skip-oci` mode with expected warnings that remote state is not yet enabled.
- Release-watch refresh validation: passed with live fetch, quick gates, gated promotion, and Object Storage upload from the backend OCI VM cron path.
- Staging Object Storage snapshot sync: uploaded `oci-rag-index.json` and `oci-release-snapshot.json`.
- Staging retrieval health: passed with `oracle_ai_vector_search`, 60 chunks, fallback inactive, and no store error.
- Staging smoke: passed through OCI API Gateway for backend and frontend.
- Staging operational readiness: passed with expected OCI DevOps warning.
- Staging internal beta readiness: passed with expected OCI DevOps warning.
