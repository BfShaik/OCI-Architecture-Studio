# OCI Architecture Studio Terraform

Starter Terraform for the first OCI-native deployment architecture.

This scaffold is intentionally small:

- one project compartment
- one VCN and public subnet
- one Compute instance for the FastAPI backend
- Object Storage buckets for frontend assets and generated snapshots
- Vault and key for future secrets/encryption
- Logging log group
- Monitoring alarm
- Notifications topic
- Events rule for environment resource lifecycle notifications
- optional OCI API Gateway in front of the backend VM
- optional OCI Functions + Resource Scheduler knowledge refresh schedules
- runtime environment profile bootstrap for the backend VM
- operational diagnostics configuration for OCI Vault, Logging, OCI Audit posture, Monitoring, Notifications, and Events
- `governance_resource_summary` output for rebuild and audit review of IAM, Vault, logging, monitoring, notification, event, API Gateway, DevOps metadata, and scheduler resources
- `runtime_infrastructure_summary` output for operator review of VCN/subnet, API exposure mode, runtime compute, Object Storage, Vault/IAM, observability, scheduler, and delivery posture

It is not a production HA design yet. It is the Phase 1 OCI deployment foundation for the validated MVP.

## Structure

```text
terraform/
  envs/
    dev/
    staging/
    test/
      providers.tf
      variables.tf
      terraform.tfvars.example
      main.tf
      outputs.tf
      cloud-init.yaml.tftpl
  modules/
    foundation/
      main.tf
      variables.tf
      outputs.tf
```

## Usage

```bash
cd infra/terraform/envs/dev
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars with your tenancy/compartment/region values
terraform init
terraform fmt -recursive
terraform validate
terraform plan
terraform apply
```

## Notes

- Keep `terraform.tfvars` out of git.
- Keep saved plan files such as `tfplan` out of git.
- Commit `.terraform.lock.hcl` files when provider selections change.
- Store production secrets in OCI Vault, not Terraform variables.
- Use `deployment_profile`, `operational_diagnostics_enabled`, and `oci_connectivity_check_enabled` to control runtime diagnostics. Keep live OCI connectivity checks disabled until IAM policies and Vault access are verified.
- Use the generated Object Storage buckets for frontend assets, knowledge snapshots, release snapshots, and eval reports.
- Enable `enable_api_gateway` only when the backend VM exposure path is ready to move behind OCI API Gateway; it is default-off for staging stability.
- Provide optional `oci_devops_project_ocid` and `oci_devops_deploy_pipeline_ocid` when deployment is managed through OCI DevOps; current operator-script deployment remains supported.
- Enable `enable_knowledge_refresh_scheduler` only after the knowledge refresh function image is built and pushed to OCIR.
- When `enable_knowledge_refresh_scheduler` is enabled, Terraform passes the Function and Resource Scheduler OCIDs into cloud-init so runtime diagnostics can report the OCI-native refresh workflow accurately.
- Use `terraform output runtime_infrastructure_summary` during deployment reviews to distinguish active resources from default-off scaffolding.
- The backend instance is intentionally simple; move to Container Instances or a Load Balancer + instance pool only after the MVP deployment is stable.
- Use `backend.object-storage.example.tf` as the starting point for remote Terraform state once a shared state bucket exists.
- Before copying the backend template into an environment, run the read-only readiness check. It validates the local backend template and can optionally verify OCI Object Storage namespace and state-bucket access without migrating state:

```bash
python3 infra/scripts/check_terraform_remote_state_readiness.py \
  --env staging \
  --skip-oci
```

For live OCI validation, provide the expected namespace and state bucket:

```bash
python3 infra/scripts/check_terraform_remote_state_readiness.py \
  --env staging \
  --profile DEFAULT \
  --namespace <object-storage-namespace> \
  --bucket-name <terraform-state-bucket> \
  --region us-ashburn-1
```

This script is intentionally non-mutating. It does not create `backend.tf`, create buckets, run `terraform init -migrate-state`, or modify state files.

## Manual Object Storage Backend Migration

Run this only after the readiness check passes and the target state bucket exists.

1. Back up the current local state and lock metadata:

```bash
cd infra/terraform/envs/staging
mkdir -p ../../../.terraform-state-backups/staging
cp terraform.tfstate ../../../.terraform-state-backups/staging/terraform.tfstate.$(date +%Y%m%d%H%M%S)
cp .terraform.lock.hcl ../../../.terraform-state-backups/staging/.terraform.lock.hcl.$(date +%Y%m%d%H%M%S)
```

2. Copy the backend template into the environment directory:

```bash
cp ../../backend.object-storage.example.tf backend.tf
```

3. Edit `backend.tf` locally with the real bucket, namespace, key, and region. Do not commit `backend.tf` if it contains environment-specific values.
4. Review the pending local diff:

```bash
git status --short
terraform fmt
```

5. Run migration as an explicit operator action:

```bash
terraform init -migrate-state
```

6. Validate that the migrated backend can read state and produce a stable plan:

```bash
terraform validate
terraform plan
```

7. Keep the local backup until at least one successful apply/read cycle has completed from the remote backend.

Rollback before promotion:

1. Stop if `terraform init -migrate-state`, `terraform validate`, or `terraform plan` fails.
2. Remove the uncommitted environment `backend.tf`.
3. Restore the backed-up `terraform.tfstate` only if the local state file changed during the failed migration.
4. Re-run `terraform init` against the local backend and confirm `terraform plan` works.
5. Record the failure in the operational log before retrying.

## API Gateway Staging Cutover

OCI API Gateway is scaffolded but default-off. Promote it only after the backend VM health endpoint is stable and the operator accepts the ingress change.

Preflight:

```bash
terraform -chdir=infra/terraform/envs/staging validate
python3 infra/scripts/operational_readiness_check.py \
  --api-base-url http://<backend-public-ip>:8000 \
  --require-oci-profile
```

Cutover plan:

1. In the local, uncommitted staging `terraform.tfvars`, set:

```hcl
enable_api_gateway      = true
api_gateway_path_prefix = "/"
```

2. Review the planned Gateway, deployment, and cloud-init changes:

```bash
terraform -chdir=infra/terraform/envs/staging plan
```

3. Apply only after the plan shows the expected API Gateway resources and no unrelated destructive changes.
4. Capture the new outputs:

```bash
terraform -chdir=infra/terraform/envs/staging output -raw api_gateway_endpoint
terraform -chdir=infra/terraform/envs/staging output -raw api_gateway_ocid
terraform -chdir=infra/terraform/envs/staging output -raw api_gateway_deployment_ocid
```

5. Smoke test through the Gateway endpoint:

```bash
python3 infra/scripts/smoke_oci_deployment.py \
  --api-base-url "$(terraform -chdir=infra/terraform/envs/staging output -raw api_gateway_endpoint)" \
  --frontend-url http://<backend-public-ip>:8000/ \
  --check-oci-sdk
```

6. Confirm runtime diagnostics show:

- `api_gateway.active=true`
- `api_gateway.promotion_ready=true`
- `api_exposure=oci_api_gateway`

Rollback:

1. Set `enable_api_gateway = false` in local staging `terraform.tfvars`.
2. Run `terraform -chdir=infra/terraform/envs/staging plan` and verify only API Gateway resources are removed or disabled.
3. Apply the rollback only if the direct backend VM endpoint is healthy.
4. Re-run smoke and operational readiness against `http://<backend-public-ip>:8000`.
5. Keep direct VM exposure as the accepted staging path until Gateway smoke and diagnostics are clean.

## Autonomous AI Database Vector Search Scaffold

Oracle Autonomous AI Database is scaffolded as the OCI-native target for Oracle AI Vector Search shadow mode. It is default-off and should not be enabled until the operator has approved database cost, password/state handling, and a shadow-read parity plan.

The scaffold creates, only when explicitly enabled:

- an OCI Network Security Group for the database private endpoint
- an ingress rule allowing backend subnet TCPS access on port `1522`
- an Oracle Autonomous Database configured for private endpoint access, mTLS, ECPU compute, and `26ai` by default
- outputs for the database OCID and private endpoint

Do not enable this resource in committed environment files. Use a local, uncommitted `terraform.tfvars` override:

```hcl
enable_autonomous_vector_database   = true
autonomous_vector_db_name           = "OCIARCHVEC"
autonomous_vector_db_admin_password = "REPLACE_WITH_STRONG_PASSWORD"
autonomous_vector_db_compute_count  = 2
autonomous_vector_db_storage_tbs    = 1
autonomous_vector_db_version        = "26ai"
autonomous_vector_db_license_model  = "LICENSE_INCLUDED"
```

Security and state notes:

- `autonomous_vector_db_admin_password` is marked sensitive, but Terraform state can still contain sensitive values. Move state to the OCI Object Storage backend, restrict state access, and review the state plan before shared/team operation.
- The database is intended for shadow validation first. Keep `RETRIEVAL_PROVIDER=oci_object_storage` until Oracle AI Vector Search parity passes without skip.
- After apply, store runtime connection details in OCI Vault or the approved deployment secret path instead of plaintext shell files.

Preflight:

```bash
terraform fmt -check -recursive infra/terraform
terraform -chdir=infra/terraform/envs/staging validate
terraform -chdir=infra/terraform/envs/staging plan
```

Promotion gate:

1. Apply only after the plan shows the expected Autonomous Database and NSG resources.
2. Confirm `autonomous_vector_database_ocid` and `autonomous_vector_database_private_endpoint` outputs are populated.
3. Create/load the vector schema and index.
4. Run Oracle AI Vector Search parity against the active Object Storage baseline without `--allow-skip`.
5. Keep active retrieval on Object Storage until parity, staging smoke, retrieval regression, and rollback checks pass.

- See `docs/oci-landing-zone-runbook.md` for the deployment and validation workflow.
