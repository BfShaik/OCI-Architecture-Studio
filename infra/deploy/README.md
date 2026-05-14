# Deployment Config

This directory stores non-secret deployment configuration examples.

Use one codebase across all environments:

- local values live in `.env`
- OCI staging values are rendered into `/etc/oci-architecture-studio.env`
- OCI secrets live in Vault or GitHub environment secrets
- Terraform values live in `infra/terraform/envs/<env>/terraform.tfvars`

Do not commit copied `.env`, `staging.env`, `terraform.tfvars`, private keys, or downloaded OCI config files.

## Staging Runtime Config

Start from:

```bash
cp infra/deploy/staging.env.example infra/deploy/staging.env
```

Then fill only non-secret environment-specific identifiers. Store secret material in OCI Vault and reference it by OCID.
