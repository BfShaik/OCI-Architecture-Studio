# OCI Architecture Studio — Retrieval Parity Validation Report

Date: 2026-05-15

Validated baseline: `d3292d6`

Current-state note: this report records the Object Storage parity gate. Staging retrieval was later promoted to active `oracle_ai_vector_search` with Object Storage as rollback; see `docs/current/status.md` and `docs/current/living-execution-plan.md` for the current active provider.

## Goal

Validate the OCI-native retrieval provider against the stable `local_json` baseline before promoting OCI-native retrieval into the active staging read path.

This validation compares:

- `local_json`
- `oci_object_storage`

The Oracle AI Vector Search adapter remains guarded and is not part of this active-provider promotion decision.

## Provider Health

| Provider | Status | Chunk Count | Embedding Model | Notes |
|---|---:|---:|---|---|
| `local_json` | Passed | 13 | `local-hashing-v1-256` | Stable local baseline |
| `oci_object_storage` | Passed | 13 | `local-hashing-v1-256` | Reads `oci-rag-index.json` from staging knowledge snapshot bucket |

OCI Object Storage manifest:

- namespace: `idsmrn7rvqb6`
- bucket: `oci-architecture-studio-staging-knowledge-snapshots`
- object: `oci-rag-index.json`

## Initial Findings And Fixes

The first parity run failed, which was useful:

- The Object Storage manifest was older than the local index for DR evidence.
- The Object Storage adapter was re-reading the manifest during each `exists` check, causing avoidable latency.

Fixes completed:

- Synced the latest validated `oci-rag-index.json` and `oci-release-snapshot.json` to the staging knowledge snapshot bucket.
- Updated `OciObjectStorageVectorStore.exists` to use cached chunks after the manifest is loaded.
- Reran parity validation successfully.

## Final Parity Results

| Check | Result |
|---|---:|
| Total parity cases | 14 |
| Passed | 14 |
| Failed | 0 |
| Average top chunk overlap | 1.0 |
| Average local latency | 1.61 ms |
| Average OCI-native latency | 0.93 ms |
| Citation URL regressions | 0 |
| Stale citation regressions | 0 |
| Required service evidence regressions | 0 |
| Intent mismatches | 0 |

## Scenario Parity

| Scenario | Intent | Parity Result | Evidence Quality |
|---|---|---:|---|
| Highly available ecommerce | `architecture` | Passed | Same top chunks, same services, citation URLs present |
| EKS + RDS migration | `migration` | Passed | Same OKE/database migration evidence |
| Fintech DR | `dr` | Passed | Same DR, database, networking, and security evidence |
| Cost-optimized web app | `cost` | Passed | Same Cost Management, Object Storage, Compute, CDN evidence |
| Latest OCI update impact | `release_awareness` | Passed | Same release-aware retrieval behavior and citation grounding |

## Eval And Regression Parity

| Suite | `local_json` | `oci_object_storage` |
|---|---:|---:|
| Golden evals | 6 passed, 0 failed | 6 passed, 0 failed |
| Edge-case evals | 8 passed, 0 failed | 8 passed, 0 failed |
| Retrieval regression | 14 passed, 0 failed | 14 passed, 0 failed |
| Backend tests | 30 passed | Not provider-specific |
| Frontend build | Passed | Not provider-specific |

## Staging Smoke And OCI Checks

Post-promotion staging now reports `oci_object_storage` as the active provider. See `docs/reports/retrieval-provider-promotion-report.md` for the completed promotion validation.

Staging checks passed:

- backend health
- frontend reachability
- architecture-review smoke
- release-aware citation smoke
- OCI SDK tenancy access
- Object Storage bucket visibility
- Vault secret readability
- Logging log group visibility
- Monitoring alarm visibility
- Events rule visibility

## Observability Added

The new parity gate reports:

- active provider per side
- embedding model
- store health
- chunk counts
- services and service domains
- top chunk overlap
- citation counts
- citation URL gaps
- stale citation regressions
- metadata completeness
- latency comparison
- mismatch diagnostics

Health visibility remains available through:

```bash
curl http://193.122.149.102:8000/retrieval/health
```

## Config-Based Provider Switching

Promotion remains config-only:

```bash
RETRIEVAL_PROVIDER=oci_object_storage
EMBEDDING_PROVIDER=local
OCI_OBJECT_STORAGE_NAMESPACE=idsmrn7rvqb6
OCI_VECTOR_BUCKET=oci-architecture-studio-staging-knowledge-snapshots
OCI_VECTOR_OBJECT_NAME=oci-rag-index.json
```

Rollback remains config-only:

```bash
RETRIEVAL_PROVIDER=local_json
EMBEDDING_PROVIDER=local
KNOWLEDGE_INDEX_PATH=knowledge/snapshots/oci-rag-index.json
```

No code fork is required.

## Promotion Criteria

Promotion criteria for `oci_object_storage` as active staging provider:

- parity report passes all cases
- golden evals pass for both providers
- edge-case evals pass for both providers
- retrieval regression passes for both providers
- no required-service evidence regressions
- no citation URL regressions
- no stale citation regressions
- metadata completeness is not weaker than local baseline
- staging snapshot bucket contains the latest generated index
- rollback to `local_json` has been validated
- post-promotion `/retrieval/health` reports `provider=oci_object_storage`

## Go / No-Go Recommendation

Decision: **Completed. `oci_object_storage` is active in staging after controlled config-only promotion.**

Boundary:

- This is not a go decision for Oracle AI Vector Search active reads.
- Oracle AI Vector Search remains guarded until table schema, indexing, and live vector query parity are validated.

## Exact Commands

Sync latest snapshots:

```bash
OCI_CLI_PROFILE=DEFAULT infra/scripts/sync_snapshots_to_object_storage.sh \
  idsmrn7rvqb6 \
  oci-architecture-studio-staging-knowledge-snapshots
```

Run parity:

```bash
app/backend/.venv/bin/python infra/scripts/retrieval_parity_check.py \
  --oci-region us-ashburn-1 \
  --oci-profile DEFAULT \
  --oci-namespace idsmrn7rvqb6 \
  --oci-vector-bucket oci-architecture-studio-staging-knowledge-snapshots \
  --oci-vector-object-name oci-rag-index.json \
  --output-dir evals/reports/retrieval-parity
```

Run OCI provider evals:

```bash
OCI_REGION=us-ashburn-1 \
OCI_PROFILE=DEFAULT \
OCI_OBJECT_STORAGE_NAMESPACE=idsmrn7rvqb6 \
OCI_VECTOR_BUCKET=oci-architecture-studio-staging-knowledge-snapshots \
OCI_VECTOR_OBJECT_NAME=oci-rag-index.json \
RETRIEVAL_PROVIDER=oci_object_storage \
EMBEDDING_PROVIDER=local \
app/backend/.venv/bin/python evals/run_golden.py --output-dir evals/reports/golden-oci-object-storage
```

## Next Step

Prepare Oracle AI Vector Search schema and indexing in shadow mode, then immediately rerun:

- `/retrieval/health`
- staging baseline guardrail
- deployment smoke
- golden evals
- edge-case evals
- retrieval regression
