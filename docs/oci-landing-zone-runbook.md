# OCI Architecture Studio — Landing Zone Runbook

Last updated: 2026-05-14

## Purpose

This runbook explains how to stand up the first OCI development/staging landing zone and deploy the validated OCI Architecture Studio application with minimal application changes.

## Landing Zone Structure

Recommended sandbox layout:

```text
Tenancy
  parent compartment
    oci-architecture-studio-dev
    oci-architecture-studio-test
    oci-architecture-studio-staging
```

Each environment gets:

- VCN
- public subnet for the first backend VM
- Object Storage bucket for frontend assets
- Object Storage bucket for knowledge/release snapshots
- Vault and encryption key
- placeholder app config secret
- Logging log group
- Notifications topic
- Monitoring alarm
- dynamic group for backend instances
- IAM policy for backend access to objects, secrets, keys, and metrics

## IAM Approach

The Terraform foundation creates:

- a dynamic group matching backend Compute instances in the environment compartment
- a starter IAM policy allowing that dynamic group to:
  - manage objects in the environment compartment
  - read secret bundles
  - use Vault keys
  - publish/use metrics

This is intentionally small. Tighten it in production by bucket, vault, and secret name.

## Secrets Strategy

Local development:

- `.env`
- no committed secrets

OCI development:

- OCI Vault stores app secrets
- Terraform creates a placeholder secret only
- real values should be updated through OCI Console, OCI CLI, or CI/CD

Future:

- backend reads secrets through instance principals
- CI/CD writes secret versions during deployment

## Remote State Strategy

Initial local validation can use local Terraform state.

Before shared team usage:

1. Create a dedicated Object Storage bucket for Terraform state.
2. Copy `infra/terraform/backend.object-storage.example.tf` into the environment directory as `backend.tf`.
3. Update bucket, namespace, key, and region.
4. Run:

```bash
terraform init -migrate-state
```

Do not commit real backend values if they expose tenant details.

## Local Dev Flow

```bash
app/backend/.venv/bin/python knowledge/ingestion/ingest.py --no-fetch
app/backend/.venv/bin/python knowledge/refresh/ingest_releases.py --no-fetch
cd app/backend
PYTHONPATH=src .venv/bin/uvicorn oci_arch_studio_backend.main:app --reload --port 8000
cd ../frontend
npm run dev
```

## OCI Deployment Flow

For exact command-by-command execution, see `docs/oci-deployment-execution.md`.

### 1. Configure Terraform

```bash
cd infra/terraform/envs/staging
cp terraform.tfvars.example terraform.tfvars
```

Edit:

- `tenancy_ocid`
- `parent_compartment_ocid`
- `region`
- `ssh_public_key`
- `backend_image_ocid`
- `alarm_email`

### 2. Provision Foundation

```bash
terraform init
terraform fmt -recursive
terraform validate
terraform plan
terraform apply
```

Capture outputs:

```bash
terraform output
```

### 3. Deploy Backend

For the first slice, keep deployment manual and simple:

1. SSH into backend public IP.
2. Clone the repo or upload an artifact.
3. Create `.env`.
4. Build local snapshots or sync snapshots from Object Storage.
5. Run FastAPI with `uvicorn` behind a systemd service.

Future improvement:

- build container image
- run on Compute with Docker or Container Instances
- use CI/CD to deploy the artifact

### 4. Upload Frontend

```bash
infra/scripts/upload_frontend_to_object_storage.sh <namespace> <frontend_bucket_name>
```

For a production frontend, put a CDN/load balancer/custom domain in front of Object Storage.

### 5. Validate Deployment

```bash
python3 infra/scripts/smoke_oci_deployment.py \
  --api-base-url http://<backend_public_ip>:8000 \
  --frontend-url https://<frontend-url>
```

Optional OCI SDK check:

```bash
python3 infra/scripts/smoke_oci_deployment.py \
  --api-base-url http://<backend_public_ip>:8000 \
  --check-oci-sdk
```

## Rollback Basics

Backend:

- keep the previous application artifact on the VM
- restart systemd service with previous artifact
- keep local JSON snapshots versioned or synced from Object Storage

Frontend:

- Object Storage upload can overwrite files
- keep previous `dist` artifact in CI or Object Storage
- re-upload previous artifact to roll back

Terraform:

- use version control for infrastructure changes
- review `terraform plan`
- avoid manual console drift

## Validation Checklist

- `terraform validate` passes
- backend `/health` returns `ok`
- `/architecture-review` returns citations
- frontend loads
- backend can read Object Storage snapshot path
- placeholder secret exists in Vault
- log group exists
- CPU alarm exists
- notification topic exists
- monitoring alarm is readable through the OCI SDK helper
- resource lifecycle Events rule exists and routes to Notifications

## Top Risks

| Risk | Mitigation |
|---|---|
| Public backend exposure on port 8000 | Accept only for dev; add Load Balancer/API Gateway and tighter NSGs before production. |
| Manual backend deployment drift | Move to container/artifact deployment after first dev slice. |
| Public frontend bucket | Use `NoPublicAccess` plus CDN/custom domain for test/prod. |
| Over-broad IAM starter policy | Tighten policy after first deployment using bucket/vault-specific access. |
| Local state in shared use | Move Terraform state to Object Storage before team collaboration. |

## Current Status

- Staging Terraform apply is complete.
- Backend/frontend staging deployment is working.
- Object Storage snapshot bucket contains the knowledge and release snapshots.
- OCI Object Storage retrieval has passed dual-provider parity against `local_json`.
- Staging now uses `RETRIEVAL_PROVIDER=oci_object_storage` through configuration.
- `local_json` remains the tested rollback provider.

## Next Implementation Steps

1. Prepare Oracle AI Vector Search schema and indexing prototype.
2. Dual-run Oracle AI Vector Search against the active Object Storage provider.
3. Add HTTPS ingress with Load Balancer or API Gateway.
4. Move Terraform state to OCI Object Storage before broader team usage.
5. Tighten IAM policies after access patterns stabilize.
