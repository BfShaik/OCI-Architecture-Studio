# OCI Architecture Studio — Retrieval Provider Promotion Report

Date: 2026-05-15

## Decision

Staging retrieval was promoted from `local_json` to `oci_object_storage` through configuration only.

Current active staging provider:

```text
RETRIEVAL_PROVIDER=oci_object_storage
```

Rollback provider:

```text
RETRIEVAL_PROVIDER=local_json
```

No application logic, prompt templates, retrieval interfaces, or frontend code were forked for the promotion.

## Promotion Result

The staging VM runtime environment now points retrieval at the OCI Object Storage vector manifest:

```text
EMBEDDING_PROVIDER=local
OCI_AUTH_MODE=instance_principal
OCI_REGION=us-ashburn-1
OCI_OBJECT_STORAGE_NAMESPACE=idsmrn7rvqb6
OCI_VECTOR_BUCKET=oci-architecture-studio-staging-knowledge-snapshots
OCI_VECTOR_OBJECT_NAME=oci-rag-index.json
```

Post-promotion `/retrieval/health` reported:

| Field | Value |
|---|---|
| provider | `oci_object_storage` |
| store provider | `oci_object_storage_vector_manifest` |
| chunk count | `13` |
| service domain count | `10` |
| last error | `null` |

## Validation Summary

Local validation after promotion:

| Check | Result |
|---|---:|
| Knowledge ingestion | Passed, `13` chunks |
| Release ingestion | Passed, `3` release items |
| Backend tests | Passed, `30` tests |
| Golden evals | Passed, `6/6` |
| Edge-case evals | Passed, `8/8` |
| Frontend build | Passed |
| Local retrieval regression | Passed, `14/14` |
| OCI Object Storage retrieval regression | Passed, `14/14` |
| Retrieval parity | Passed, `14/14` |
| Terraform fmt/validate | Passed for `dev`, `test`, and `staging` |

Staging validation after promotion:

| Check | Result |
|---|---:|
| Staging baseline guardrail | Passed with expected provider `oci_object_storage` |
| Backend health | Passed |
| Frontend reachability | Passed |
| OCI SDK connectivity | Passed |
| Object Storage visibility | Passed |
| Vault secret visibility | Passed |
| Logging visibility | Passed |
| Monitoring alarm visibility | Passed |
| Events rule visibility | Passed |

## Scenario Quality Checks

Live post-promotion scenarios passed for:

| Scenario | Intent | Result |
|---|---|---:|
| Highly available ecommerce platform on OCI | `architecture` | Passed |
| Migrate EKS + RDS to OCI | `migration` | Passed |
| Recommend OCI services for fintech DR | `dr` | Passed |
| Build a cost-optimized web app on OCI | `cost` | Passed |
| How does the latest OCI update affect this architecture? | `release_awareness` | Passed |

Observed quality:

- citations remained grounded
- source URLs were present
- retrieved metadata remained visible
- no stale citations surfaced in the scenario checks
- no unsupported OCI service claims were observed in the demo path

## Latency And Operations

Observed live retrieval latency averaged about `487 ms` during scenario checks.

This is acceptable for staging, but production hardening should add:

- per-request retrieval latency logging
- Object Storage read failure counters
- provider-specific warning counts
- comparison dashboards before Oracle AI Vector Search active reads

## Rollback Validation

Rollback was validated without code or prompt changes:

1. Set `RETRIEVAL_PROVIDER=local_json`.
2. Restarted the staging backend service.
3. Confirmed `/retrieval/health` reported `local_json` with `13` chunks.
4. Restored `RETRIEVAL_PROVIDER=oci_object_storage`.
5. Restarted the staging backend service.
6. Confirmed `/retrieval/health` reported `oci_object_storage` with `13` chunks.

Rollback remains instant and config-only.

## Remaining Risks

- The corpus is still intentionally small.
- Embeddings are still deterministic local hashing embeddings, not production semantic embeddings.
- Oracle AI Vector Search is not active yet.
- Object Storage manifest retrieval is reliable for staging, but it is not the final low-latency vector search architecture.
- Backend staging traffic is still served over public HTTP until HTTPS ingress is added.
- Release-awareness is point-in-time snapshot based, not a continuous watcher with impact analysis.

## Go / No-Go

Decision: **GO for Oracle AI Vector Search active-read implementation work**, with one boundary:

Oracle AI Vector Search must first run in dual-read parity against the now-active `oci_object_storage` provider. It should not become the staging active provider until schema, indexing, query behavior, citations, evals, and rollback are validated.

## Next Migration Boundary

Ready:

- config-selected retrieval interface
- Object Storage vector manifest
- provider health endpoint
- parity and regression scripts
- rollback to `local_json`

Still prototype:

- local hashing embeddings
- small seed corpus
- Object Storage manifest as the active vector read path
- point-in-time release snapshot without continuous impact analysis

Next highest-value block:

Implement Oracle AI Vector Search schema and indexing in shadow mode, then compare it against `oci_object_storage` for the golden, edge-case, retrieval-regression, and live scenario suites.
