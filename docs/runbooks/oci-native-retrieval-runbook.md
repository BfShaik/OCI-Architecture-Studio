# OCI-Native Retrieval Runbook

Date: 2026-05-16

## Purpose

This runbook controls the Sprint 2 migration from the validated local retrieval baseline to OCI-native retrieval services while preserving the advisory workflow.

Local development default remains:

```bash
EMBEDDING_PROVIDER=local
RETRIEVAL_PROVIDER=local_json
```

Current staging default:

```bash
EMBEDDING_PROVIDER=local
RETRIEVAL_PROVIDER=oracle_ai_vector_search
OCI_OBJECT_STORAGE_NAMESPACE=idsmrn7rvqb6
OCI_VECTOR_BUCKET=oci-architecture-studio-staging-knowledge-snapshots
OCI_VECTOR_OBJECT_NAME=oci-rag-index.json
```

Object Storage remains the immediate config rollback provider; `local_json` remains the local development fallback.

## Provider Modes

### Local Development

Use this for day-to-day development and CI:

```bash
python3 knowledge/ingestion/ingest.py --no-fetch
python3 infra/scripts/check_retrieval_health.py --provider local_json
python3 infra/scripts/retrieval_regression_check.py \
  --cases evals/golden-prompts.jsonl \
  --cases evals/edge-cases.jsonl \
  --output-dir evals/reports/retrieval
```

### OCI Object Storage Manifest

Use this for migration-safe managed storage parity:

```bash
python3 knowledge/ingestion/ingest.py \
  --embedding-provider oci_genai \
  --oci-region "$OCI_REGION" \
  --oci-profile "$OCI_PROFILE" \
  --oci-genai-compartment-id "$OCI_GENAI_COMPARTMENT_ID" \
  --oci-genai-embedding-model-id "$OCI_GENAI_EMBEDDING_MODEL_ID" \
  --oci-namespace "$OCI_OBJECT_STORAGE_NAMESPACE" \
  --oci-upload-bucket "$OCI_VECTOR_BUCKET" \
  --oci-upload-object "$OCI_VECTOR_OBJECT_NAME"
```

Then validate:

```bash
python3 infra/scripts/check_retrieval_health.py \
  --provider oci_object_storage \
  --embedding-provider oci_genai \
  --oci-region "$OCI_REGION" \
  --oci-profile "$OCI_PROFILE" \
  --oci-namespace "$OCI_OBJECT_STORAGE_NAMESPACE" \
  --oci-vector-bucket "$OCI_VECTOR_BUCKET" \
  --oci-vector-object-name "$OCI_VECTOR_OBJECT_NAME" \
  --oci-genai-compartment-id "$OCI_GENAI_COMPARTMENT_ID" \
  --oci-genai-embedding-model-id "$OCI_GENAI_EMBEDDING_MODEL_ID"
```

### Oracle AI Vector Search

Use this only after table/schema validation:

```bash
RETRIEVAL_PROVIDER=oracle_ai_vector_search
OCI_VECTOR_DB_DSN=...
OCI_VECTOR_DB_USER=...
OCI_VECTOR_DB_PASSWORD=...
OCI_VECTOR_WALLET_LOCATION=...
OCI_VECTOR_WALLET_PASSWORD=...
OCI_VECTOR_TABLE_NAME=OCI_ARCHITECTURE_CHUNKS
OCI_VECTOR_DIMENSIONS=256
OCI_VECTOR_DISTANCE_METRIC=COSINE
RETRIEVAL_FALLBACK_ENABLED=true
```

Current status: the provider code creates schema, upserts chunks, serves active reads, and reports health when Oracle DB settings and schema are valid. Staging uses `oracle_ai_vector_search` with the promoted 60-chunk corpus; Object Storage remains the immediate rollback provider.

Embedding migration note: the active staging table is still the 256-dimension local-hash index. For the approved `cohere.embed-v4.0` migration path, build a separate 1536-dimension Oracle vector table/index first, generate document embeddings with OCI GenAI `SEARCH_DOCUMENT`, use `SEARCH_QUERY` for runtime questions, and promote only after `/retrieval/health` shows matching provider, model, and dimensions with the guardrail passing.

Local operational checks:

```bash
app/backend/.venv/bin/python infra/scripts/oracle_vector_index.py validate-local-index
app/backend/.venv/bin/python infra/scripts/oracle_vector_index.py print-schema
app/backend/.venv/bin/python infra/scripts/vector_retrieval_validation.py --allow-skip
```

Dual-read parity against the active Object Storage baseline can be run before Oracle AI Vector Search is configured. It should skip cleanly rather than silently falling back:

```bash
app/backend/.venv/bin/python infra/scripts/retrieval_parity_check.py \
  --baseline-provider oci_object_storage \
  --oci-native-provider oracle_ai_vector_search \
  --allow-skip \
  --oci-region "$OCI_REGION" \
  --oci-profile "$OCI_PROFILE" \
  --oci-namespace "$OCI_OBJECT_STORAGE_NAMESPACE" \
  --oci-vector-bucket "$OCI_VECTOR_BUCKET" \
  --oci-vector-object-name "$OCI_VECTOR_OBJECT_NAME" \
  --output-dir evals/reports/retrieval-oracle-vector-parity
```

When Oracle DB settings exist, provide `OCI_VECTOR_DB_DSN`, `OCI_VECTOR_DB_USER`, and `OCI_VECTOR_DB_PASSWORD` through the matching CLI flags or environment wrapper and rerun the same parity gate. Do not promote `RETRIEVAL_PROVIDER=oracle_ai_vector_search` until parity passes without fallback.

## Oracle AI Vector Search Active Promotion

Current decision: **promoted in staging**. Oracle AI Vector Search active reads passed non-skipped parity, retrieval regression, staging smoke, and rollback validation. Use this section for future re-promotions, rebuilds, and rollback drills.

Prerequisites for a future re-promotion:

- Oracle DB DSN, user, and password are available through OCI Vault or approved runtime configuration.
- `infra/scripts/oracle_vector_index.py validate-local-index` passes.
- Oracle schema and vector index are created or verified.
- `infra/scripts/retrieval_parity_check.py --baseline-provider oci_object_storage --oci-native-provider oracle_ai_vector_search` passes without fallback.
- Golden, edge, retrieval regression, vector validation, and staging smoke checks pass.

Configuration-only promotion:

```text
RETRIEVAL_PROVIDER=oracle_ai_vector_search
RETRIEVAL_FALLBACK_ENABLED=true
OCI_VECTOR_DB_DSN=<vault/runtime value>
OCI_VECTOR_DB_USER=<vault/runtime value>
OCI_VECTOR_DB_PASSWORD=<vault/runtime value>
OCI_VECTOR_WALLET_LOCATION=<runtime wallet directory>
OCI_VECTOR_WALLET_PASSWORD=<vault/runtime value>
OCI_VECTOR_TABLE_NAME=OCI_ARCHITECTURE_CHUNKS
OCI_VECTOR_INDEX_NAME=OCI_ARCH_CHUNKS_VEC_IDX
OCI_VECTOR_DIMENSIONS=256
OCI_VECTOR_DISTANCE_METRIC=COSINE
```

Post-promotion checks:

```bash
app/backend/.venv/bin/python infra/scripts/check_retrieval_health.py \
  --provider oracle_ai_vector_search \
  --oci-vector-db-dsn "$OCI_VECTOR_DB_DSN" \
  --oci-vector-db-user "$OCI_VECTOR_DB_USER" \
  --oci-vector-db-password "$OCI_VECTOR_DB_PASSWORD" \
  --oci-vector-wallet-location "$OCI_VECTOR_WALLET_LOCATION" \
  --oci-vector-wallet-password "$OCI_VECTOR_WALLET_PASSWORD"

app/backend/.venv/bin/python infra/scripts/retrieval_regression_check.py \
  --provider oracle_ai_vector_search \
  --output-dir evals/reports/retrieval-oracle-active

app/backend/.venv/bin/python infra/scripts/vector_retrieval_validation.py \
  --output-dir evals/reports/vector-retrieval
```

Rollback:

```text
RETRIEVAL_PROVIDER=oci_object_storage
```

Emergency local rollback:

```text
RETRIEVAL_PROVIDER=local_json
```

After rollback, rerun `/retrieval/health`, retrieval regression, and staging smoke. Record whether fallback was active, what failed, and which provider is now authoritative.

## Migration Gates

Do not switch or re-promote a staging provider until all are true:

- backend tests pass
- golden evals pass
- edge-case evals pass
- retrieval regression report passes
- `/retrieval/health` shows the expected provider and nonzero chunk count
- top retrieved chunks preserve source URLs and chunk IDs
- required services remain covered in retrieved evidence
- release-awareness prompts still produce freshness cautions

## Dual-Provider Parity Gate

Before staging uses a new provider as the active retrieval provider, sync the latest local snapshots to the staging knowledge bucket:

```bash
OCI_CLI_PROFILE=DEFAULT infra/scripts/sync_snapshots_to_object_storage.sh \
  idsmrn7rvqb6 \
  oci-architecture-studio-staging-knowledge-snapshots
```

Then compare local and OCI-native retrieval:

```bash
app/backend/.venv/bin/python infra/scripts/retrieval_parity_check.py \
  --oci-region us-ashburn-1 \
  --oci-profile DEFAULT \
  --oci-namespace idsmrn7rvqb6 \
  --oci-vector-bucket oci-architecture-studio-staging-knowledge-snapshots \
  --oci-vector-object-name oci-rag-index.json \
  --output-dir evals/reports/retrieval-parity
```

Provider promotion requires:

- `14/14` parity cases passing
- average top chunk overlap at or above `0.8`
- no citation URL regressions
- no stale citation regressions
- no required service evidence regressions
- golden and edge evals passing for both providers
- rollback to `local_json` remaining config-only

## Rollback

Rollback is configuration-only:

```bash
EMBEDDING_PROVIDER=local
RETRIEVAL_PROVIDER=local_json
KNOWLEDGE_INDEX_PATH=knowledge/snapshots/oci-rag-index.json
```

Then rerun:

```bash
python3 knowledge/ingestion/ingest.py --no-fetch
python3 infra/scripts/check_retrieval_health.py --provider local_json
python3 infra/scripts/retrieval_regression_check.py --output-dir evals/reports/retrieval
cd app/backend && PYTHONPATH=src .venv/bin/pytest -q
```

## Troubleshooting

- Missing or zero chunks: rerun ingestion and check `KNOWLEDGE_INDEX_PATH` or Object Storage bucket/object inputs.
- OCI embedding failure: verify `OCI_GENAI_COMPARTMENT_ID`, `OCI_GENAI_EMBEDDING_MODEL_ID`, region, auth mode, and policy access.
- Object Storage retrieval failure: verify namespace, bucket, object name, instance principal or OCI profile permissions.
- Vector Search selected accidentally: set `RETRIEVAL_PROVIDER=local_json` or `oci_object_storage`, or keep `RETRIEVAL_FALLBACK_ENABLED=true` while Oracle DB config is incomplete.
- Generic answers: inspect retrieval regression report for missing services or missing citations.
- Stale guidance: rerun release ingestion and check citation freshness fields.

## Next Operational Milestone

Keep Object Storage rollback snapshots aligned with the active Oracle AI Vector Search index, then run OCI GenAI synthesis parity without changing retrieval provider settings.
