# OCI Architecture Studio — OCI Staging Deployment Report

Date: 2026-05-14

## Summary

The first OCI staging infrastructure slice was applied successfully.

Current-state note: this report records the initial infrastructure apply. The retrieval provider was later promoted from `local_json` to `oci_object_storage`; see `docs/retrieval-provider-promotion-report.md` for the active retrieval state.

Result:

```text
Apply complete! Resources: 19 added, 0 changed, 0 destroyed.
```

After infrastructure provisioning, the same repository codebase was deployed to the backend VM, frontend assets were uploaded to Object Storage, knowledge snapshots were uploaded to Object Storage, and smoke tests passed.

## Environment

- Environment: `staging`
- Region: `us-ashburn-1`
- OCI profile used locally: `DEFAULT`
- Backend host: `193.122.149.102`
- Frontend bucket: `oci-architecture-studio-staging-frontend-assets`
- Snapshot bucket: `oci-architecture-studio-staging-knowledge-snapshots`
- Notification email: `baba.shaik@oracle.com`

## Terraform Apply Workflow

Commands run:

```bash
terraform fmt -check -recursive infra/terraform
terraform -chdir=infra/terraform/envs/staging init -input=false
terraform -chdir=infra/terraform/envs/staging validate
terraform -chdir=infra/terraform/envs/staging apply -auto-approve tfplan
```

The apply used the previously reviewed saved plan:

```text
infra/terraform/envs/staging/tfplan
```

## Resources Created

- Project compartment
- VCN
- Internet Gateway
- Public route table
- Public subnet
- Public security list
- Backend Compute VM
- Frontend Object Storage bucket
- Knowledge snapshots Object Storage bucket
- Vault
- KMS key
- Placeholder app config secret
- Logging log group
- ONS notification topic
- Email subscription
- Events lifecycle rule
- Monitoring CPU alarm
- Backend dynamic group
- Backend IAM policy

## Post-Apply Outputs

Important outputs:

- Backend public IP: `193.122.149.102`
- Frontend bucket: `oci-architecture-studio-staging-frontend-assets`
- Snapshot bucket: `oci-architecture-studio-staging-knowledge-snapshots`
- App config secret: created
- Log group: created
- Monitoring alarm: created
- Events lifecycle rule: created
- Notification topic: created

## Deployment Steps Completed

Backend deployment:

```bash
infra/scripts/deploy_backend_vm.sh \
  "$(terraform -chdir=infra/terraform/envs/staging output -raw backend_public_ip)" \
  opc \
  ~/.ssh/oci-architecture-studio-staging
```

Frontend upload:

```bash
VITE_API_BASE_URL="http://193.122.149.102:8000" \
infra/scripts/upload_frontend_to_object_storage.sh \
  idsmrn7rvqb6 \
  oci-architecture-studio-staging-frontend-assets
```

Snapshot upload:

```bash
infra/scripts/sync_snapshots_to_object_storage.sh \
  idsmrn7rvqb6 \
  oci-architecture-studio-staging-knowledge-snapshots
```

## Validation Results

OCI resource visibility:

- Object Storage namespace: passed
- Bucket list: passed
- Snapshot bucket found: passed
- Vault secret readable: passed
- Log group readable: passed
- Monitoring alarm readable: passed
- Events rule readable: passed

Backend smoke:

- `/health`: passed
- `/architecture-review`: passed
- architecture citations: 6
- release-aware citations: 6
- OCI SDK tenancy check: passed

Retrieval health:

- provider: `local_json`
- embedding model: `local-hashing-v1-256`
- chunk count: 13
- index path: `/opt/oci-architecture-studio/knowledge/snapshots/oci-rag-index.json`

Frontend:

- Object Storage `index.html`: uploaded
- frontend assets: uploaded
- smoke test: passed

Snapshot objects:

- `oci-rag-index.json`
- `oci-release-snapshot.json`

## Issues Found And Fixed

### Backend SSH Sync

Issue:

- `ssh` used the staging SSH key, but `rsync` did not.

Fix:

- Updated `infra/scripts/deploy_backend_vm.sh` so `rsync` uses the same SSH key.

### Backend Python Version

Issue:

- Oracle Linux default `python3` was 3.9, but the backend requires Python 3.12-compatible runtime behavior.

Fix:

- Updated deployment to install/use `python3.12`.
- Updated deployment to recreate the backend virtual environment with Python 3.12.

### OS Firewall

Issue:

- OCI security list allowed port `8000`, but host firewalld also needed the port opened.

Fix:

- Updated backend deployment script to open `8000/tcp` when firewalld is running.

### Frontend Upload

Issue:

- Bulk upload intermittently failed for `index.html` while asset uploads succeeded.

Fix:

- Updated frontend upload script to upload files individually.
- Rebuilt frontend with `VITE_API_BASE_URL=http://193.122.149.102:8000`.

### Local TLS Verification

Issue:

- Smoke test hit local certificate verification failure when reading Object Storage HTTPS URL.

Fix:

- Updated smoke test script to use certifi-backed TLS context.

## Remaining Warnings

- Backend API is public on `http://193.122.149.102:8000`.
- SSH is public on port `22`.
- Backend is HTTP-only; add HTTPS ingress before broader demo or production use.
- VM shape is intentionally large for MVP staging: `VM.Standard.E5.Flex`, 8 OCPUs, 128 GB.
- Terraform state is local. Move state to OCI Object Storage before shared/team operation.
- ONS email subscription may require confirmation in the target inbox before notifications fully deliver.
- Vault contains only a placeholder app config secret; replace it through OCI Console or CI.

## Rollback Notes

For a full sandbox rollback:

```bash
terraform -chdir=infra/terraform/envs/staging destroy
```

Before destroying, capture any logs, outputs, and object contents needed for debugging.

For app-only rollback:

- redeploy a previous Git commit with `infra/scripts/deploy_backend_vm.sh`
- re-upload the previous frontend build
- keep Terraform infrastructure intact

## Next Hardening Steps

1. Restrict SSH ingress to trusted CIDRs.
2. Put the backend behind HTTPS through Load Balancer or API Gateway.
3. Move Terraform state to OCI Object Storage.
4. Replace the placeholder Vault secret.
5. Add app log shipping into OCI Logging.
6. Add custom health/retrieval metrics.
7. Confirm ONS email subscription.
8. Add CI secrets for:
   - `OCI_STAGING_API_BASE_URL`
   - `OCI_STAGING_FRONTEND_URL`
   - `OCI_STAGING_BACKEND_HOST`
   - `OCI_STAGING_FRONTEND_BUCKET`
   - `OCI_STAGING_SNAPSHOTS_BUCKET`
