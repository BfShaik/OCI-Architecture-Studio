# OCI Architecture Studio — Operational Runbook

Date: 2026-05-14

## Working URLs

Use the backend-hosted app URL for the current MVP staging baseline:

```text
http://193.122.149.102:8000/
```

Health endpoint:

```text
http://193.122.149.102:8000/health
```

Retrieval health endpoint:

```text
http://193.122.149.102:8000/retrieval/health
```

## Verify Deployment Health

Run:

```bash
python3 infra/scripts/verify_staging_baseline.py \
  --api-base-url http://193.122.149.102:8000 \
  --frontend-url http://193.122.149.102:8000/
```

Expected result:

```text
"passed": true
```

## Rerun Smoke Tests

Backend, frontend, and OCI SDK:

```bash
python3 infra/scripts/smoke_oci_deployment.py \
  --api-base-url http://193.122.149.102:8000 \
  --frontend-url http://193.122.149.102:8000/ \
  --check-oci-sdk
```

OCI resource visibility:

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

## Rerun Evals

```bash
app/backend/.venv/bin/python evals/run_golden.py --output-dir evals/reports/golden
app/backend/.venv/bin/python evals/run_golden.py --cases evals/edge-cases.jsonl --output-dir evals/reports/edge-cases
```

## Rerun Local Quality Gates

```bash
app/backend/.venv/bin/python knowledge/ingestion/ingest.py --no-fetch
app/backend/.venv/bin/python knowledge/refresh/ingest_releases.py --no-fetch
cd app/backend && PYTHONPATH=src .venv/bin/pytest -q
cd ../frontend && npm run build
```

Terraform validation:

```bash
terraform fmt -check -recursive infra/terraform
terraform -chdir=infra/terraform/envs/staging validate
```

## Inspect Backend Service

SSH to the VM:

```bash
ssh -i ~/.ssh/oci-architecture-studio-staging opc@193.122.149.102
```

Check service:

```bash
sudo systemctl status oci-architecture-studio --no-pager
```

Follow logs:

```bash
sudo journalctl -u oci-architecture-studio -f
```

Restart service:

```bash
sudo systemctl restart oci-architecture-studio
```

## Redeploy App

```bash
infra/scripts/deploy_backend_vm.sh \
  193.122.149.102 \
  opc \
  ~/.ssh/oci-architecture-studio-staging
```

Then rerun:

```bash
python3 infra/scripts/verify_staging_baseline.py \
  --api-base-url http://193.122.149.102:8000 \
  --frontend-url http://193.122.149.102:8000/
```

## Upload Snapshots

```bash
infra/scripts/sync_snapshots_to_object_storage.sh \
  idsmrn7rvqb6 \
  oci-architecture-studio-staging-knowledge-snapshots
```

## Local vs OCI Troubleshooting

If local tests fail:

- check Python virtualenv
- check generated snapshots
- check eval reports under `evals/reports`
- do not redeploy until local gates are green

If local tests pass but OCI fails:

- check systemd service logs
- check `/etc/oci-architecture-studio.env`
- check that `/opt/oci-architecture-studio/app/frontend/dist` exists
- check `/opt/oci-architecture-studio/knowledge/snapshots`
- rerun deployment script

If frontend loads but Review fails:

- use `http://193.122.149.102:8000/`, not the Object Storage HTTPS URL
- check browser console for mixed-content or network errors
- run the backend smoke test

If retrieval fails:

- check `/retrieval/health`
- confirm chunk count is at least 13
- rerun ingestion on the VM through the deploy script

## Rollback

App-only rollback:

1. Check out the previous known-good Git commit locally.
2. Run `infra/scripts/deploy_backend_vm.sh`.
3. Rerun baseline smoke tests.

Infrastructure rollback:

```bash
terraform -chdir=infra/terraform/envs/staging destroy
```

Use full destroy only for sandbox teardown. Capture logs and outputs first if debugging a failure.

## Current Operational Risks

- Public HTTP backend
- Public SSH
- local Terraform state
- placeholder Vault secret
- no app log shipping into OCI Logging yet
- no custom app metrics yet

The next hardening milestone is HTTPS ingress and restricted backend access.
