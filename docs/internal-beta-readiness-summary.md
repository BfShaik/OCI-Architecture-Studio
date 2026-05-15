# OCI Architecture Studio — Internal Beta Readiness Summary

Date: 2026-05-15

## Readiness Position

OCI Architecture Studio is ready for a controlled enterprise internal beta after the validation gates listed below pass on the target environment.

This milestone is an internal beta baseline, not a production HA certification. The platform is deployable and operable in OCI staging, has deterministic fallback behavior, exposes advisory traceability, and has regression coverage across retrieval, governance, migration, FinOps, release intelligence, runtime diagnostics, and executive usability.

## Platform Gap Assessment

| Area | Current State | Internal Beta Decision |
|---|---|---|
| Retrieval | `oci_object_storage` is active in staging with 44 chunks and `local_json` fallback. Oracle AI Vector Search provider and tooling exist but live DB-backed promotion is not complete. | Accept for beta. Keep Oracle AI Vector Search as the next retrieval promotion gate. |
| Advisory synthesis | Deterministic synthesis is default. OCI GenAI chat path exists with fail-closed deterministic fallback. | Accept for beta. Enable live OCI GenAI only after parity checks pass with approved model config. |
| Governance | Deterministic governance annotations, risk classification, security posture checks, prioritization, comparisons, and auditability trace exist. | Accept for beta as human-review metadata, not policy enforcement. |
| Migration and FinOps | `optimization_plan` adds phased migration, modernization options, FinOps levers, workload optimization, comparisons, and implementation readiness. | Accept for beta. It is heuristic advisory guidance and does not call live OCI billing APIs. |
| Release intelligence | Release ingestion, normalization, impact analysis, overlays, historical snapshot retention, and release-aware response metadata exist. | Accept for beta. Full live release reconciliation and full bi-temporal retrieval remain future work. |
| Runtime deployment | OCI VM staging is active. OKE and OCI Functions-compatible profiles exist. API Gateway and OCI DevOps metadata are scaffolded but not active in staging. | Accept for beta with documented readiness warnings. Promote API Gateway before production-style external exposure. |
| IaC | Terraform covers compartment, VCN/subnet, gateway, route/security, Compute, Object Storage, Vault/key/secret, Logging, Monitoring alarm, Notifications, Events, optional API Gateway, optional Functions/Scheduler, IAM dynamic groups/policies, and rebuild outputs. | Accept for beta. Move Terraform state to OCI Object Storage before team/shared operations. |
| Observability | Operational endpoints expose health, readiness, infrastructure, analytics, provider usage, fallback events, governance trends, recommendation trends, and runtime degradation counters. OCI Logging/Monitoring/Notifications/Event OCIDs are visible when configured. | Accept for beta. Custom metric export to OCI Monitoring is a later hardening task. |
| Evaluation | Golden, edge, advisory, orchestration, architecture realism, evaluation intelligence, governance, platform maturity, runtime readiness, executive experience, FinOps/migration, retrieval regression, vector skip-safe, and provider-parity tooling exist. | Accept for beta. Keep eval additions tied to real failures and platform gaps. |
| Executive usability | Executive summaries, decision briefs, implementation sequence, topology summaries, comparisons, explainability highlights, Markdown artifact, and migration/FinOps UI exist. | Accept for beta. Full diagram rendering and presentation generation remain future work. |

## Prioritized Remediation Completed In This Closeout

1. Added `infra/scripts/internal_beta_readiness_check.py` as a single high-signal internal beta gate for deployed environments.
2. Improved scheduler diagnostics so OCI Resource Scheduler/Functions readiness is based on configured Function and Schedule OCIDs, not only the process deployment profile.
3. Extended Terraform cloud-init and runtime profile examples to carry knowledge-refresh Function/Schedule OCIDs when the scheduler is enabled.
4. Added regression coverage for scheduler diagnostic visibility.
5. Updated this readiness summary and related docs to keep internal beta claims precise.

## Accepted Internal Beta Limitations

- The active staging API is still direct backend VM exposure unless OCI API Gateway is explicitly enabled.
- OCI DevOps is not configured for active staging deployment; local operator scripts remain the current deployment mechanism.
- Oracle AI Vector Search is implemented but not the active staging read path.
- OCI GenAI synthesis and OCI GenAI embeddings are implemented but not active by default.
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

PYTHONPATH=app/backend/src app/backend/.venv/bin/python infra/scripts/check_retrieval_health.py \
  --provider oci_object_storage \
  --oci-region us-ashburn-1 \
  --oci-profile DEFAULT \
  --oci-namespace idsmrn7rvqb6 \
  --oci-vector-bucket oci-architecture-studio-staging-knowledge-snapshots \
  --oci-vector-object-name oci-rag-index.json
```

## Milestone Tagging

After the full validation baseline passes and staging is refreshed, create a stable milestone tag:

```bash
git tag -a internal-beta-2026-05-15 -m "Internal beta baseline"
git push origin internal-beta-2026-05-15
```

Use a new date-suffixed tag for future internal beta baselines rather than moving an existing tag.
