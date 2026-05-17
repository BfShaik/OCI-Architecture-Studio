# Current Status

Last updated: 2026-05-17

OCI Architecture Studio is live in staging as an internal-beta OCI architecture review assistant.

## Staging Runtime

| Area | Value |
| --- | --- |
| Synthesis | `oci_genai` |
| Chat model | `xai.grok-4.3` |
| Retrieval | `oracle_ai_vector_search` |
| Embeddings | `oci_genai` |
| Embedding model | `cohere.embed-v4.0` |
| Dimensions | `1536` |
| Vector table | `OCI_ARCHITECTURE_CHUNKS_V4` |
| Corpus | 60 curated OCI chunks |
| Guardrail | passing |

## Local Defaults

| Area | Value |
| --- | --- |
| Synthesis | `deterministic` |
| Retrieval | `local_json` |
| Embeddings | `local` |

Local defaults keep development usable without OCI credentials. Staging overrides them through the reviewed runtime/Vault path.

## Latest Validation

- `/health`: `200`
- `/retrieval/health`: `200`
- `/architecture-review`: `synthesis_provider=oci_genai`, fallback disabled
- Retrieval regression: `32/32`
- Golden evals: `18/18`
- Edge evals: `8/8`

## Rollback

Synthesis:

```text
ADVISORY_SYNTHESIS_PROVIDER=deterministic
```

Retrieval:

```text
RETRIEVAL_PROVIDER=oci_object_storage
```

Embedding:

```text
EMBEDDING_PROVIDER=local
OCI_VECTOR_OBJECT_NAME=oci-rag-index.local-hash.json
OCI_VECTOR_DIMENSIONS=256
```

Restart backend and verify `/retrieval/health` after any rollback.

## Known Gaps

- Restore or create `evals/team-real-prompts.jsonl`.
- Corpus is curated, not a full OCI documentation mirror.
- Release awareness is snapshot-based.
- Query embedding cache is not implemented yet.
- Production HA and HTTPS/domain hardening remain future work.

## Next Tasks

1. Run team-real prompt evals.
2. Monitor GenAI quality, cost, latency, and fallback behavior.
3. Monitor Oracle vector retrieval quality.
4. Add query embedding caching only if needed.
