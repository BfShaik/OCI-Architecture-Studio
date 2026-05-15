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
- See `docs/oci-landing-zone-runbook.md` for the deployment and validation workflow.
