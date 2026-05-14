# OCI Architecture Studio — Terraform Plan Review

Date: 2026-05-14

## Scope

This report covers the safe Terraform planning phase before the first OCI infrastructure apply.

No infrastructure was provisioned. `terraform apply` was not run.

## Environment

- Environment: `staging`
- Terraform root: `infra/terraform/envs/staging`
- Provider: Oracle OCI Terraform provider
- OCI profile expected locally: `DEFAULT`
- Region source: `terraform.tfvars`
- Variable source: `infra/terraform/envs/staging/terraform.tfvars`
- Saved plan: `infra/terraform/envs/staging/tfplan`
- State mode: local state for first sandbox planning
- Remote state: documented as an Object Storage backend template, not yet enabled

The real `terraform.tfvars`, saved `tfplan`, and SSH keys are intentionally ignored by git.

## Terraform Execution Workflow

Run from the repository root.

```bash
terraform fmt -check -recursive infra/terraform
terraform -chdir=infra/terraform/envs/staging init -input=false
terraform -chdir=infra/terraform/envs/staging validate
python3 infra/scripts/validate_deployment_config.py \
  --tfvars infra/terraform/envs/staging/terraform.tfvars \
  --profile DEFAULT
terraform -chdir=infra/terraform/envs/staging plan -out=tfplan
```

Review the saved plan:

```bash
terraform -chdir=infra/terraform/envs/staging show tfplan
terraform -chdir=infra/terraform/envs/staging show -json tfplan
```

Extract managed resources:

```bash
terraform -chdir=infra/terraform/envs/staging show -json tfplan \
  | jq -r '.resource_changes[] | select(.mode=="managed") | [(.change.actions|join("/")), .type, .name, .address] | @tsv'
```

Apply is intentionally separate and should be run only after the readiness criteria below are met.

## Planning Results

Validation result:

- `terraform fmt -check -recursive`: passed
- `terraform init -input=false`: passed
- `terraform validate`: passed
- deployment config validation: passed
- `terraform plan -out=tfplan`: passed

Plan summary:

```text
Plan: 19 to add, 0 to change, 0 to destroy
```

## Resources To Be Created

| Action | Resource type | Name |
|---|---|---|
| create | `oci_identity_compartment` | `project` |
| create | `oci_core_vcn` | `main` |
| create | `oci_core_internet_gateway` | `main` |
| create | `oci_core_route_table` | `public` |
| create | `oci_core_security_list` | `public` |
| create | `oci_core_subnet` | `public` |
| create | `oci_core_instance` | `backend` |
| create | `oci_objectstorage_bucket` | `frontend` |
| create | `oci_objectstorage_bucket` | `snapshots` |
| create | `oci_kms_vault` | `main` |
| create | `oci_kms_key` | `main` |
| create | `oci_vault_secret` | `app_config_placeholder` |
| create | `oci_logging_log_group` | `app` |
| create | `oci_ons_notification_topic` | `alerts` |
| create | `oci_ons_subscription` | `email` |
| create | `oci_events_rule` | `resource_lifecycle` |
| create | `oci_monitoring_alarm` | `backend_cpu` |
| create | `oci_identity_dynamic_group` | `backend_instances` |
| create | `oci_identity_policy` | `backend_access` |

## Major Dependencies

- The project compartment is created under the configured parent compartment.
- VCN, subnet, route table, security list, buckets, Vault, log group, notification topic, alarm, and Compute instance are created inside the project compartment.
- Dynamic group is created at tenancy scope and matches Compute instances in the project compartment.
- IAM policy is created under the parent compartment and grants the backend dynamic group starter access inside the project compartment.
- Monitoring alarm and Events rule send notifications through the ONS topic.
- Email subscription targets `baba.shaik@oracle.com`.

## Networking Summary

Planned network:

- VCN CIDR: `10.20.0.0/16`
- Public subnet CIDR: `10.20.10.0/24`
- Internet Gateway: enabled
- Public route: `0.0.0.0/0` through Internet Gateway
- Backend Compute: public IP enabled
- Public ingress:
  - TCP `22` from `0.0.0.0/0`
  - TCP `8000` from `0.0.0.0/0`
- Egress:
  - all protocols to `0.0.0.0/0`

This is simple and usable for a first sandbox deployment, but it is not production hardened.

## Security Observations

Positive:

- Secrets are not hardcoded into source control.
- Real `terraform.tfvars` is ignored.
- SSH private key is kept outside tracked files.
- Vault and KMS are included.
- Snapshot bucket is private.
- IAM uses a dynamic group for backend instance access.
- Notifications and lifecycle events are included.

Warnings:

- SSH is open to the internet.
- Backend API port `8000` is open to the internet.
- Backend gets a public IP.
- Frontend bucket uses `ObjectReadWithoutList`, which is expected for simple static hosting but should be reviewed before production.
- Placeholder Vault secret content must be replaced after apply.
- IAM policy grants `manage objects` in the project compartment. This is acceptable for an MVP backend but should be tightened by bucket or operation when usage stabilizes.
- Local Terraform state is acceptable for solo sandbox use but should move to OCI Object Storage before team/shared operations.

## Object Storage Review

Planned buckets:

- `oci-architecture-studio-staging-frontend-assets`
  - access: `ObjectReadWithoutList`
  - use: frontend static assets
- `oci-architecture-studio-staging-knowledge-snapshots`
  - access: `NoPublicAccess`
  - use: knowledge and release snapshots

This matches the MVP deployment model.

## Logging And Monitoring Review

Planned resources:

- application log group
- CPU alarm for backend Compute
- ONS topic
- email subscription
- Events rule for compartment-level resource lifecycle notifications

This is reasonable for the first deployment slice. App log shipping and custom app metrics are still future hardening items.

## Operational Footprint

Main cost-bearing resources:

- one `VM.Standard.E5.Flex` backend instance
- 8 OCPUs
- 128 GB memory
- Object Storage buckets
- Vault and KMS key
- Logging, Monitoring, Notifications, and Events

Cost warning:

- The backend VM size is intentionally large for staging. It should be accepted before apply or reduced for a lower-cost MVP deployment.

## Local / Cloud Parity

Confirmed design:

- one codebase
- multiple environments
- local remains dev/test
- OCI staging uses the same backend, frontend, ingestion, retrieval, prompts, and eval assets
- environment differences are config-driven
- no separate cloud-only application version is introduced

## Plan Review Checklist

- [x] Terraform formatting passed
- [x] Terraform initialized successfully
- [x] Terraform validation passed
- [x] Deployment config validation passed
- [x] Plan generated successfully
- [x] Plan creates only expected resources
- [x] Plan has 0 destroys
- [x] Plan has 0 unexpected changes
- [x] Project compartment name follows environment naming
- [x] Buckets follow environment naming
- [x] Notifications use configured admin email
- [x] Vault, KMS, Logging, Monitoring, and Events exist
- [x] One codebase / multiple environments discipline is preserved
- [ ] Public SSH exposure accepted or restricted
- [ ] Public backend API exposure accepted or restricted
- [ ] VM cost accepted or shape reduced
- [ ] Email subscription confirmation process understood
- [ ] Remote state decision made before shared/team usage

## Apply Readiness Criteria

Required before running `terraform apply`:

1. All required variables are populated in the ignored staging `terraform.tfvars`.
2. OCI profile can read tenancy, parent compartment, Object Storage namespace, and backend image.
3. Saved plan has been reviewed.
4. Plan still shows no destroys.
5. Public SSH and API exposure are explicitly accepted for sandbox staging, or ingress CIDRs are restricted.
6. Backend VM cost is explicitly accepted.
7. Rollback guidance is understood:
   - keep the saved plan
   - inspect outputs after apply
   - use Terraform-managed destroy only if the whole sandbox needs rollback
8. Post-apply smoke test commands are ready.
9. Notification email owner is ready to confirm the ONS subscription.

## Post-Apply Smoke-Test Plan

After apply, capture outputs:

```bash
terraform -chdir=infra/terraform/envs/staging output
```

Validate OCI resource visibility:

```bash
python3 infra/scripts/check_oci_access.py \
  --profile DEFAULT \
  --compartment-id "<compartment_ocid>" \
  --bucket-name "oci-architecture-studio-staging-knowledge-snapshots" \
  --secret-id "<app_config_secret_ocid>" \
  --log-group-id "<log_group_ocid>" \
  --alarm-id "<backend_cpu_alarm_ocid>" \
  --event-rule-id "<resource_lifecycle_event_rule_ocid>"
```

Validate backend API after app deployment:

```bash
python3 infra/scripts/smoke_oci_deployment.py \
  --api-base-url "http://<backend_public_ip>:8000" \
  --check-oci-sdk
```

Validate retrieval health after app deployment:

```bash
curl "http://<backend_public_ip>:8000/retrieval/health"
```

Validate frontend after static upload:

```bash
python3 infra/scripts/smoke_oci_deployment.py \
  --api-base-url "http://<backend_public_ip>:8000" \
  --frontend-url "<frontend_url>" \
  --check-oci-sdk
```

Checks that must pass:

- backend `/health`
- backend `/architecture-review`
- backend `/retrieval/health`
- frontend availability
- Object Storage access
- Vault secret visibility
- Logging log group visibility
- Monitoring alarm visibility
- Events rule visibility
- OCI SDK connectivity
- notification email confirmation

## Go / No-Go Recommendation

Recommendation: **Go for first sandbox `terraform apply` only after accepting two explicit risks.**

Risks to accept or fix before apply:

1. Public ingress is open for SSH and backend API.
2. Backend VM size is large for MVP staging.

If those are acceptable for a short-lived sandbox deployment, the plan is ready to apply.

If this environment will be long-lived, shared, or externally demoed, restrict ingress and consider HTTPS ingress before apply.

## Exact Next Step

After explicit approval:

```bash
terraform -chdir=infra/terraform/envs/staging apply tfplan
```

Do not regenerate the plan after approval unless variables or Terraform code change. If anything changes, rerun the full planning workflow before apply.
