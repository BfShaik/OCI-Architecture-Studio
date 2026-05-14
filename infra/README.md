# Infra

Deployment and CI/CD assets live here.

## Current State

- GitHub Actions CI exists under `.github/workflows/ci.yml`.
- OCI deployment architecture is documented in `docs/oci-deployment-architecture.md`.
- OCI landing-zone deployment workflow is documented in `docs/oci-landing-zone-runbook.md`.
- Command-by-command deployment execution is documented in `docs/oci-deployment-execution.md`.
- Starter Terraform lives under `infra/terraform/`.
- Non-secret deployment config examples live under `infra/deploy/`.
- Deployment smoke checks live under `infra/scripts/`.
- OCI helper script dependencies live in `infra/requirements.txt`.
- Manual staging deployment workflow lives in `.github/workflows/deploy-oci-staging.yml`.

## Deployment Direction

Phase 1 keeps the MVP simple:

- React frontend assets in Object Storage
- FastAPI backend on a small Compute VM
- generated knowledge/release snapshots in Object Storage
- secrets in OCI Vault
- logs in OCI Logging
- alarms in OCI Monitoring
- alerts in OCI Notifications

Phase 2 replaces local embeddings/vector index with OCI-native embeddings and vector search.
