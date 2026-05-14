# Deployment Config

This directory stores non-secret deployment configuration examples.

Use one codebase across all environments:

- local values live in `.env`
- OCI staging values are rendered into `/etc/oci-architecture-studio.env`
- OCI secrets live in Vault or GitHub environment secrets
- Terraform values live in `infra/terraform/envs/<env>/terraform.tfvars`

Do not commit copied `.env`, `staging.env`, `terraform.tfvars`, private keys, or downloaded OCI config files.

## Deployment Inputs

Required now:

- `tenancy_ocid`
- `parent_compartment_ocid`
- `region`
- `oci_profile`
- `auth_method`
- `admin_email`
- `ssh_public_key`
- `backend_image_ocid`
- `backend_shape`
- `backend_ocpus`
- `backend_memory_gbs`
- `frontend_bucket_access_type`

Optional later:

- private subnet OCID or custom subnet CIDR
- custom domain and TLS certificate OCID
- Load Balancer or API Gateway OCID
- remote Terraform state bucket
- OCI Generative AI endpoint/model settings
- Oracle AI Vector Search connection settings

Never hardcode:

- OCI private keys
- user API keys
- application secrets
- generated `.env` files
- `terraform.tfvars`
- saved Terraform plan files
- SSH private keys

The deployment config contract is documented in `deployment-config.schema.json`.

Validate Terraform variables before planning:

```bash
python3 infra/scripts/validate_deployment_config.py \
  --tfvars infra/terraform/envs/staging/terraform.tfvars \
  --profile DEFAULT
```

## Staging Runtime Config

Start from:

```bash
cp infra/deploy/staging.env.example infra/deploy/staging.env
```

Then fill only non-secret environment-specific identifiers. Store secret material in OCI Vault and reference it by OCID.
