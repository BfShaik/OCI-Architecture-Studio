# Operational Runbook

## Current Staging Runtime

| Area | Value |
| --- | --- |
| App URL | `http://193.122.149.102:8000/` |
| Synthesis | `ADVISORY_SYNTHESIS_PROVIDER=oci_genai` |
| Retrieval | `RETRIEVAL_PROVIDER=oracle_ai_vector_search` |
| Embeddings | `EMBEDDING_PROVIDER=oci_genai` |
| Embedding model | `cohere.embed-v4.0` |
| Vector table | `OCI_ARCHITECTURE_CHUNKS_V4` |

## Health Checks

```bash
curl -fsS http://193.122.149.102:8000/health
curl -fsS http://193.122.149.102:8000/retrieval/health
curl -fsS http://193.122.149.102:8000/operations/health
curl -fsS http://193.122.149.102:8000/operations/readiness
```

Smoke test:

```bash
python3 infra/scripts/smoke_oci_deployment.py \
  --api-base-url http://193.122.149.102:8000 \
  --frontend-url http://193.122.149.102:8000/
```

## Deploy To Staging

Use the existing operator script:

```bash
infra/scripts/deploy_backend_vm.sh 193.122.149.102 opc ~/.ssh/oci-architecture-studio-staging
```

Then run the smoke test above.

## Verify GenAI Is Active

Call `/architecture-review` and confirm:

```text
synthesis_provider=oci_genai
synthesis_fallback_used=false
```

## Synthesis Rollback

Set through the reviewed runtime/Vault path:

```text
ADVISORY_SYNTHESIS_PROVIDER=deterministic
```

Restart backend, then run smoke test.

## Retrieval Rollback

First rollback option:

```text
RETRIEVAL_PROVIDER=oci_object_storage
```

Emergency local option:

```text
RETRIEVAL_PROVIDER=local_json
```

Restart backend, then verify `/retrieval/health`.

## Embedding Rollback

```text
EMBEDDING_PROVIDER=local
OCI_VECTOR_OBJECT_NAME=oci-rag-index.local-hash.json
OCI_VECTOR_TABLE_NAME=OCI_ARCHITECTURE_CHUNKS
OCI_VECTOR_INDEX_NAME=OCI_ARCH_CHUNKS_VEC_IDX
OCI_VECTOR_DIMENSIONS=256
```

Restart backend and verify:

```text
embedding_provider=local
index_dimensions=256
embedding_index_guardrail.ok=true
```

## Common Problems

### GenAI request falls back

Check:

- IAM policy for Generative AI
- `OCI_GENAI_COMPARTMENT_ID`
- `OCI_GENAI_CHAT_MODEL_ID`
- region
- model availability
- service logs

### Retrieval health fails

Check:

- `RETRIEVAL_PROVIDER`
- Oracle vector DB env values
- wallet path
- security list for DB port
- `/retrieval/health` guardrail message

### Frontend looks stale

Check the deployed bundle:

```bash
curl -fsS http://193.122.149.102:8000/ | rg -o 'index-[A-Za-z0-9_-]+\\.(js|css)'
```

Redeploy if the bundle does not match the latest build.

## References

- Current status: [../current/status.md](../current/status.md)
- Active plan: [../current/living-execution-plan.md](../current/living-execution-plan.md)
- Retrieval runbook: [oci-native-retrieval-runbook.md](oci-native-retrieval-runbook.md)
