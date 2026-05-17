# Infra

Deployment and OCI runtime assets live here.

## Current State

- Staging runs the React/FastAPI app on an OCI Compute VM.
- OCI GenAI synthesis is active in staging through `ADVISORY_SYNTHESIS_PROVIDER=oci_genai`.
- Oracle AI Vector Search is the active retrieval provider.
- OCI GenAI embeddings use `cohere.embed-v4.0` at 1536 dimensions.
- Object Storage and local JSON remain rollback paths.
- GitHub Actions is validation-only; staging deploys use operator scripts.

## Useful Paths

- `infra/scripts/` - deploy, smoke, validation, GenAI, retrieval, and rollback helpers.
- `infra/deploy/` - non-secret deployment examples and schema.
- `infra/runtime-profiles/` - local, OCI VM, and OKE runtime examples.
- `infra/terraform/` - OCI foundation resources.

Operational orchestration stays inside OCI. Current staging scheduled knowledge
refresh runs as cron on the backend OCI Compute VM.
