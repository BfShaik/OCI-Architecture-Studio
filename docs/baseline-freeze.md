# OCI Architecture Studio — Working Baseline Freeze

Date: 2026-05-14

## Baseline Identity

Current-state note: this document freezes the original post-deploy baseline. Staging retrieval was later promoted from `local_json` to `oci_object_storage`; see `docs/retrieval-provider-promotion-report.md` for the active provider validation.

- Branch: `main`
- Baseline commit at verification start: `412c892`
- Baseline freeze artifacts: this document, the operational runbook, and the staging guardrail script on `main`
- Environment: `staging`
- Region: `us-ashburn-1`
- Primary working app URL: `http://193.122.149.102:8000/`
- Backend API base URL: `http://193.122.149.102:8000`
- OCI profile used for local validation: `DEFAULT`

The current working baseline keeps the project rule intact:

- one codebase
- multiple environments
- local equals dev/test
- OCI equals staging/demo/production
- no Kubernetes
- no microservices

## Deployed OCI Resources

Terraform apply result:

```text
Resources: 19 added, 0 changed, 0 destroyed
```

Created resources:

- `oci-architecture-studio-staging` compartment
- VCN
- Internet Gateway
- public route table
- public subnet
- public security list
- backend Compute VM
- frontend Object Storage bucket
- knowledge snapshots Object Storage bucket
- Vault
- KMS key
- placeholder app config secret
- Logging log group
- ONS notification topic
- email subscription
- Events lifecycle rule
- Monitoring CPU alarm
- backend dynamic group
- backend IAM policy

Important outputs:

- backend public IP: `193.122.149.102`
- frontend bucket: `oci-architecture-studio-staging-frontend-assets`
- snapshots bucket: `oci-architecture-studio-staging-knowledge-snapshots`
- Object Storage namespace: `idsmrn7rvqb6`

## Environment Configuration

Local:

- Python backend tests run from `app/backend/.venv`
- frontend build runs from `app/frontend`
- local retrieval provider: `local_json`
- local embedding provider: `local`
- local knowledge index: `knowledge/snapshots/oci-rag-index.json`
- local release snapshot: `knowledge/snapshots/oci-release-snapshot.json`

OCI staging at the original baseline freeze:

- backend systemd service: `oci-architecture-studio`
- backend deploy path: `/opt/oci-architecture-studio`
- Python runtime: Python 3.12
- backend env file: `/etc/oci-architecture-studio.env`
- hosted frontend path: `/opt/oci-architecture-studio/app/frontend/dist`
- OCI-hosted retrieval provider: `local_json`
- OCI-hosted knowledge index: `/opt/oci-architecture-studio/knowledge/snapshots/oci-rag-index.json`
- OCI-hosted release snapshot: `/opt/oci-architecture-studio/knowledge/snapshots/oci-release-snapshot.json`

## Verification Results

Post-deploy verification passed:

- backend health
- backend architecture review
- frontend reachability
- OCI SDK connectivity
- Object Storage access
- secret retrieval
- Logging log group visibility
- Monitoring alarm visibility
- Events rule visibility
- release ingestion
- retrieval health
- golden evals
- edge-case evals
- frontend build
- Terraform validation

Latest local validation:

```text
Knowledge ingestion: passed, 13 chunks
Release ingestion: passed, 3 release items
Backend tests: passed, 26/26
Golden evals: passed, 6/6
Edge-case evals: passed, 8/8
Frontend build: passed
Terraform fmt: passed
Terraform validate: passed
```

Latest live staging validation:

```text
Backend smoke: passed
Frontend smoke: passed
OCI SDK check: passed
Object Storage access: passed
Vault secret readable: passed
Logging log group readable: passed
Monitoring alarm readable: passed
Events rule readable: passed
Retrieval health: passed, 13 chunks
Baseline guardrail: passed
```

## Regression Guardrails

Guardrail commands:

```bash
python3 infra/scripts/verify_staging_baseline.py \
  --api-base-url http://193.122.149.102:8000 \
  --frontend-url http://193.122.149.102:8000/
```

```bash
python3 infra/scripts/check_oci_access.py \
  --profile DEFAULT \
  --compartment-id "$(terraform -chdir=infra/terraform/envs/staging output -raw compartment_ocid)" \
  --bucket-name "$(terraform -chdir=infra/terraform/envs/staging output -raw snapshots_bucket_name)" \
  --secret-id "$(terraform -chdir=infra/terraform/envs/staging output -raw app_config_secret_ocid)" \
  --log-group-id "$(terraform -chdir=infra/terraform/envs/staging output -raw log_group_ocid)" \
  --alarm-id "$(terraform -chdir=infra/terraform/envs/staging output -raw backend_cpu_alarm_ocid)" \
  --event-rule-id "$(terraform -chdir=infra/terraform/envs/staging output -raw resource_lifecycle_event_rule_ocid)"
```

```bash
app/backend/.venv/bin/python evals/run_golden.py --output-dir evals/reports/golden
app/backend/.venv/bin/python evals/run_golden.py --cases evals/edge-cases.jsonl --output-dir evals/reports/edge-cases
```

Guardrail coverage:

- config drift detection through Terraform validation and staging outputs
- environment parity through same-origin frontend/backend smoke checks
- failed deployment detection through backend, frontend, and retrieval health checks
- stale/missing secret visibility through OCI secret read checks
- retrieval regression detection through retrieval health and golden/edge evals
- eval failure reporting through markdown/JSON eval reports

## Known Limitations

- Backend is public HTTP on port `8000`.
- SSH is public on port `22`.
- HTTPS ingress is deferred.
- Terraform state is still local.
- VM size is large for staging: `VM.Standard.E5.Flex`, 8 OCPUs, 128 GB.
- Vault contains placeholder app config content.
- ONS email subscription may still require inbox confirmation.
- OCI-native vector retrieval is not yet the default.
- Release awareness is snapshot-based, not a live release intelligence workflow.
- App log shipping to OCI Logging is not yet implemented.

## Open Technical Debt

- Restrict ingress CIDRs for SSH and backend API.
- Add HTTPS through OCI Load Balancer or API Gateway.
- Move Terraform state to OCI Object Storage.
- Replace placeholder Vault secret with real app config.
- Add app log shipping and request correlation.
- Add custom retrieval and eval metrics.
- Add OCI-native vector retrieval adapter validation against Oracle AI Vector Search.
- Expand OCI documentation corpus.

## Stable Baseline Summary

What is working:

- local development workflow
- backend tests
- frontend build
- knowledge ingestion
- release ingestion
- golden evals
- edge-case evals
- OCI infrastructure apply
- backend VM deployment
- frontend served from backend VM
- architecture-review API
- retrieval citations
- Object Storage snapshot uploads
- OCI resource visibility checks

Intentionally deferred:

- HTTPS
- production auth/RBAC
- OCI-native vector search default
- live release watcher
- advanced LLM synthesis
- production observability dashboards

## Next Milestone Recommendation

The single highest-value next block is **HTTPS ingress and secure staging access**.

Reason:

- The app now works end to end.
- The current biggest demo and trust risk is public HTTP.
- HTTPS unblocks safer frontend/API separation, browser security, and future auth.
- It is a focused infrastructure hardening step that does not disturb RAG or eval behavior.

Recommended next milestone:

1. Add OCI Load Balancer or API Gateway in front of the backend.
2. Restrict backend port `8000` to the ingress layer.
3. Add TLS certificate handling.
4. Serve frontend and API through a stable HTTPS URL.
5. Rerun the full baseline guardrail suite.
