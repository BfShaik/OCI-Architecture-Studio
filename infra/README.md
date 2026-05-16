# Infra

Deployment and CI/CD assets live here.

## Current State

- GitHub Actions CI exists under `.github/workflows/ci.yml` for validation only.
- OCI deployment architecture is documented in `docs/oci-deployment-architecture.md`.
- OCI landing-zone deployment workflow is documented in `docs/oci-landing-zone-runbook.md`.
- Command-by-command deployment execution is documented in `docs/oci-deployment-execution.md`.
- Starter Terraform lives under `infra/terraform/`.
- Non-secret deployment config examples live under `infra/deploy/`.
- Deployment smoke checks live under `infra/scripts/`.
- OCI helper script dependencies live in `infra/requirements.txt`.
- Deployment config examples and schema live under `infra/deploy/`.

## Deployment Direction

Phase 1 keeps the MVP simple:

- React frontend assets in Object Storage
- FastAPI backend on a small Compute VM
- generated knowledge/release snapshots in Object Storage
- secrets in OCI Vault
- logs in OCI Logging
- alarms in OCI Monitoring
- alerts in OCI Notifications
- resource lifecycle notifications through OCI Events

Phase 2 replaces local embeddings/vector index with OCI-native embeddings and vector search.

Operational orchestration stays OCI-native. Current staging scheduled knowledge
refresh runs as cron on the backend OCI Compute VM because the packaged OCI
Function image failed before handler execution. OCI Resource Scheduler invoking
OCI Functions remains the preferred managed retry path after packaged invocation
validation passes. Staging deploys should use the local operator scripts or
future OCI DevOps, not GitHub Actions.
