# OCI Architecture Studio — Deployment Execution

Last updated: 2026-05-14

## Rule

One codebase, multiple environments:

```text
local = development and testing
OCI staging = first cloud deployment
OCI demo/prod = promoted cloud environments later
```

Do not fork or duplicate application code for cloud deployment. Environment differences belong in Terraform variables, environment variables, OCI Vault, and deployment workflow inputs.

## Current Staging Defaults

The first staging deployment uses:

- parent compartment: `oci-architecture-studio`
- child environment compartment: `oci-architecture-studio-staging`
- region: `us-ashburn-1`
- backend shape: `VM.Standard.E5.Flex`
- backend image family: latest compatible Oracle Linux 9 platform image
- notification endpoint: `baba.shaik@oracle.com`
- SSH key path for local deployment: `~/.ssh/oci-architecture-studio-staging`

The real `terraform.tfvars`, saved Terraform plan, and SSH private key are local-only and must not be committed.

## Deployment Input Checklist

Required now:

| Input | Current staging value/source |
|---|---|
| Tenancy OCID | OCI config `DEFAULT` profile |
| Parent compartment OCID | `oci-architecture-studio` parent compartment |
| Region | `us-ashburn-1` |
| OCI CLI profile | `DEFAULT` |
| Auth method | local `config_file`; backend target `instance_principal` later |
| Admin/contact email | `baba.shaik@oracle.com` |
| SSH public key | generated from `~/.ssh/oci-architecture-studio-staging.pub` |
| Backend image OCID | latest compatible Oracle Linux 9 image for `us-ashburn-1` |
| Backend shape | `VM.Standard.E5.Flex` |
| Backend OCPUs/memory | `8 OCPUs`, `128 GB` |
| Frontend bucket access | `ObjectReadWithoutList` for the first staging slice |

Optional later:

- private subnet or existing VCN/subnet selection
- custom domain and TLS certificate
- Load Balancer or API Gateway
- remote Terraform state bucket
- OCI Generative AI endpoint/model settings
- Oracle AI Vector Search target

Never hardcode:

- OCI private keys
- user API keys
- application secrets
- generated `.env` files
- `terraform.tfvars`
- saved Terraform plans
- SSH private keys

## Exact Deployment Sequence

### 1. Validate Locally

```bash
app/backend/.venv/bin/python knowledge/ingestion/ingest.py --no-fetch
app/backend/.venv/bin/python knowledge/refresh/ingest_releases.py --no-fetch
cd app/backend && PYTHONPATH=src .venv/bin/pytest -q
cd ../..
app/backend/.venv/bin/python evals/run_golden.py --output-dir evals/reports/golden
app/backend/.venv/bin/python evals/run_golden.py --cases evals/edge-cases.jsonl --output-dir evals/reports/edge-cases
cd app/frontend && npm run build
```

### 2. Validate OCI Access

Install the small infrastructure helper dependency first:

```bash
python3 -m pip install -r infra/requirements.txt
```

```bash
python3 infra/scripts/check_oci_access.py --profile DEFAULT
```

Optional after Terraform creates resources:

```bash
python3 infra/scripts/check_oci_access.py \
  --profile DEFAULT \
  --compartment-id <compartment_ocid> \
  --bucket-name <snapshots_bucket_name> \
  --secret-id <app_config_secret_ocid> \
  --log-group-id <log_group_ocid> \
  --alarm-id <backend_cpu_alarm_ocid> \
  --event-rule-id <resource_lifecycle_event_rule_ocid>
```

### 3. Provision OCI Infrastructure

```bash
cd infra/terraform/envs/staging
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
tenancy_ocid             = "ocid1.tenancy..."
parent_compartment_ocid  = "ocid1.compartment..."
region                   = "us-ashburn-1"
ssh_public_key           = "ssh-rsa ..."
backend_image_ocid       = "ocid1.image..."
availability_domain      = ""
backend_shape            = "VM.Standard.E5.Flex"
backend_ocpus            = 8
backend_memory_gbs       = 128
frontend_bucket_access_type = "ObjectReadWithoutList"
alarm_email              = "baba.shaik@oracle.com"
```

For the current staging setup, the selected image is:

```text
Oracle-Linux-9.7-2026.04.30-3
```

Run:

```bash
terraform init
terraform fmt -recursive
terraform validate
python ../../../scripts/validate_deployment_config.py --tfvars terraform.tfvars --profile DEFAULT
terraform plan
terraform apply
terraform output
```

If a saved plan exists after validation:

```bash
terraform apply tfplan
```

Useful outputs for later validation:

- `backend_public_ip`
- `frontend_bucket_name`
- `snapshots_bucket_name`
- `app_config_secret_ocid`
- `log_group_ocid`
- `notification_topic_ocid`
- `backend_cpu_alarm_ocid`
- `resource_lifecycle_event_rule_ocid`

The resource lifecycle Events rule sends matching environment compartment events to the same Notifications topic as the monitoring alarm.

### 4. Deploy Backend

Use the backend public IP from Terraform output:

```bash
infra/scripts/deploy_backend_vm.sh <backend_public_ip> opc ~/.ssh/<key>
```

This script:

- syncs the same repo codebase to the VM
- creates a backend virtualenv
- installs backend requirements
- builds local knowledge/release snapshots on the VM
- creates a systemd service
- starts FastAPI on port `8000`

### 5. Upload Frontend

Get Object Storage namespace:

```bash
oci os ns get --profile DEFAULT
```

Upload frontend:

```bash
export OCI_CLI_PROFILE=DEFAULT
infra/scripts/upload_frontend_to_object_storage.sh \
  <namespace> \
  <frontend_bucket_name>
```

### 6. Upload Knowledge Snapshots

```bash
export OCI_CLI_PROFILE=DEFAULT
infra/scripts/sync_snapshots_to_object_storage.sh \
  <namespace> \
  <snapshots_bucket_name>
```

### 7. Validate Deployment

```bash
python3 infra/scripts/smoke_oci_deployment.py \
  --api-base-url http://<backend_public_ip>:8000
```

If frontend URL is available:

```bash
python3 infra/scripts/smoke_oci_deployment.py \
  --api-base-url http://<backend_public_ip>:8000 \
  --frontend-url <frontend_url>
```

## Environment Configuration

### Local

Use `.env` copied from `.env.example`.

### OCI Staging

Use:

- `terraform.tfvars` for infrastructure values
- `infra/deploy/staging.env.example` as the non-secret runtime config template
- `/etc/oci-architecture-studio.env` on the backend VM for runtime config
- OCI Vault for secrets
- OCI CLI/SDK standard config locally
- instance principals later for backend-to-OCI access

Do not hardcode secrets in code, Terraform, or deployment scripts.

## OCI Config Expectations

Local operator machine:

```text
~/.oci/config
~/.oci/<private_key>.pem
```

Expected profile:

```text
[DEFAULT]
user=...
fingerprint=...
tenancy=...
region=...
key_file=...
```

Staging deploys currently use local operator execution with OCI CLI/SDK
credentials and the staging SSH key. Future hosted deployment automation should
use OCI DevOps rather than GitHub Actions.

## Remote State Recommendation

Start local for first validation. Before team/shared use:

1. Create a dedicated Terraform state bucket.
2. Copy `infra/terraform/backend.object-storage.example.tf` to `infra/terraform/envs/staging/backend.tf`.
3. Fill bucket, namespace, key, and region.
4. Run:

```bash
terraform init -migrate-state
```

## Rollback

Backend:

- keep previous repo artifact on the VM
- redeploy previous commit with `deploy_backend_vm.sh`
- restart systemd service:

```bash
sudo systemctl restart oci-architecture-studio
```

Frontend:

- re-upload previous `dist` artifact to Object Storage

Infrastructure:

- review `terraform plan`
- revert Terraform commit
- re-apply only if needed

## CI And Deployment

Existing CI remains the quality gate:

- backend tests
- frontend build
- knowledge/release ingestion smoke
- golden evals
- edge evals

Staging deployment is currently local/operator-run through Terraform and the
scripts in `infra/scripts/`. OCI-native hosted deployment automation is future
work and should use OCI DevOps.

## First Slice Acceptance Criteria

- Terraform staging validates.
- Terraform staging applies with real OCIDs.
- Backend `/health` responds.
- `/architecture-review` returns citations.
- Frontend loads.
- Object Storage buckets exist.
- Vault placeholder secret exists.
- Log group exists.
- Monitoring alarm exists.
- Release-aware API smoke path returns citations.
- Smoke script passes.

## Next Production-Hardening Recommendations

1. Put backend behind Load Balancer or API Gateway.
2. Replace public port `8000` exposure with HTTPS.
3. Move backend OCI access to instance principals.
4. Add system logs and application logs to OCI Logging agent.
5. Add deployment artifact versioning.
6. Move Terraform state to Object Storage.
7. Add production embeddings and vector store adapter.
