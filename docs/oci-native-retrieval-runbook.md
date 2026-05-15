# OCI-Native Retrieval Runbook

Date: 2026-05-14

## Purpose

This runbook controls the Sprint 2 migration from the validated local retrieval baseline to OCI-native retrieval services while preserving the advisory workflow.

The default remains:

```bash
EMBEDDING_PROVIDER=local
RETRIEVAL_PROVIDER=local_json
```

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
OCI_VECTOR_TABLE_NAME=OCI_ARCHITECTURE_CHUNKS
```

Current status: the adapter is a guarded boundary. It reports health and missing configuration but intentionally does not serve reads yet.

## Migration Gates

Do not switch staging defaults until all are true:

- backend tests pass
- golden evals pass
- edge-case evals pass
- retrieval regression report passes
- `/retrieval/health` shows the expected provider and nonzero chunk count
- top retrieved chunks preserve source URLs and chunk IDs
- required services remain covered in retrieved evidence
- release-awareness prompts still produce freshness cautions

## Dual-Provider Parity Gate

Before staging uses `oci_object_storage` as the active retrieval provider, sync the latest local snapshots to the staging knowledge bucket:

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

Promotion requires:

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
- Vector Search selected accidentally: set `RETRIEVAL_PROVIDER=local_json` or `oci_object_storage` until the read adapter is enabled.
- Generic answers: inspect retrieval regression report for missing services or missing citations.
- Stale guidance: rerun release ingestion and check citation freshness fields.

## Next Operational Milestone

Run Object Storage manifest retrieval side by side with local JSON for the golden and edge suites, then approve the Oracle AI Vector Search table schema only after citation parity is visible.
