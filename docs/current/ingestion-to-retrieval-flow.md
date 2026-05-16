# Ingestion To Retrieval Flow

Last updated: 2026-05-16

This guide explains how OCI Architecture Studio turns approved OCI documentation sources into grounded advisory retrieval. It is written for operators and reviewers who need to understand the path without reading the ingestion code first.

## One-Line Flow

```text
Official OCI docs or fallback source text
  -> source registry
  -> fetched and normalized text
  -> chunks
  -> metadata enrichment
  -> embeddings
  -> knowledge/snapshots/oci-rag-index.json
  -> OCI Object Storage promoted snapshot
  -> Oracle AI Vector Search active retrieval
```

Refresh jobs follow the same basic shape, but they build candidate snapshots first and promote them only after quality gates pass.

## Source Registry

The approved architecture corpus starts in `knowledge/source_registry.json`. Each source record provides the stable source ID, title, official OCI documentation URL, source category, source group, and offline fallback text.

The fallback text is intentional. It keeps local development and CI deterministic when network access is unavailable, and it gives operators a safe way to run `--no-fetch` smoke tests without changing the retrieval contract.

## Fetch And Normalize

`knowledge/ingestion/ingest.py` reads the registry and tries to fetch each official OCI documentation page unless `--no-fetch` is set. Fetched HTML is parsed into text, noisy page chrome is removed, and source-group defaults are merged into each source before chunking.

Typical local build:

```bash
python3 knowledge/ingestion/ingest.py
```

Offline deterministic build:

```bash
python3 knowledge/ingestion/ingest.py --no-fetch
```

The release-aware path uses `knowledge/release_source_registry.json` and `knowledge/refresh/ingest_releases.py` to build `knowledge/snapshots/oci-release-snapshot.json`. Release refresh is separate from normal advisory ingestion so current release signals do not destabilize the architecture corpus.

## Chunk And Enrich

Normalized source text is split into reviewable chunks. Each chunk keeps enough lineage for traceability:

- source ID, title, source URL, and source type
- parent document and section context
- chunk hash and fetch status
- generated timestamp

The ingestion pipeline then enriches each chunk with advisory metadata used by retrieval and evaluation:

- OCI service and service domain
- service category and source category
- intent tags such as architecture, migration, cost, DR, security, and release awareness
- workload, domain, and architecture-pattern tags
- trust level, freshness score, and content hash

This metadata is not decorative. It is used for retrieval filters, reranking, citation cards, corpus health checks, release impact overlays, and Oracle AI Vector Search materialization.

## Embed

Each chunk receives an embedding before it can be used for retrieval. Staging currently uses OCI Generative AI `cohere.embed-v4.0` document embeddings at 1536 dimensions. Query retrieval uses the matching OCI GenAI query embedding path, and `/retrieval/health` refuses to serve if the configured provider/model/dimensions do not match the active index metadata.

Local deterministic embeddings remain useful for offline development and rollback validation. The previous 256-dimension local-hash Object Storage manifest and Oracle vector table are retained for config-only rollback.

## Snapshot

The generated knowledge index is written to:

```text
knowledge/snapshots/oci-rag-index.json
```

That JSON snapshot is the portable retrieval manifest. It contains index metadata, embedding metadata, schema version, vector-readiness flags, and the chunk records with text, embeddings, and enriched metadata.

Before promotion, operators validate the snapshot with corpus health, retrieval health, retrieval regression, and the relevant advisory eval subset. Refresh-policy runs write candidate snapshots under `knowledge/reports/runs/<run_id>/candidates` first; authoritative snapshots are updated only after gates pass.

## Object Storage Snapshot And Rollback

In staging, Object Storage keeps the promoted `oci-rag-index.json` and `oci-release-snapshot.json` snapshots that feed the active Oracle vector index and remain available for rollback. After a gated promotion, the validated snapshots are uploaded to the staging Object Storage bucket before Oracle AI Vector Search is rebuilt.

If Oracle vector active reads need to be rolled back, the backend can be switched to `oci_object_storage` and load the same promoted manifest. `local_json` remains the tested local rollback provider and uses the same snapshot format.

Refresh never runs on user queries. It is operator-triggered or scheduled through the OCI backend VM cron path, and it promotes only after candidate gates pass.

## Oracle AI Vector Search Active Sync

Oracle AI Vector Search is the active staging read path. The Oracle vector index is rebuilt from the same promoted `oci-rag-index.json` snapshot uploaded to Object Storage, so the active database-backed provider and immediate Object Storage rollback source stay aligned.

The sync tool is:

```bash
python3 infra/scripts/oracle_vector_index.py rebuild \
  --index-path knowledge/snapshots/oci-rag-index.json
```

The rebuild validates that chunks have embeddings, expected dimensions, and required service metadata before upserting them into the Autonomous Database table. The active staging table is `OCI_ARCHITECTURE_CHUNKS_V4`; the prior local-hash rollback table is `OCI_ARCHITECTURE_CHUNKS`. Each table stores chunk text, vector embeddings, metadata JSON, service/domain fields, source lineage, and citation-friendly fields.

A safe promotion keeps runtime env values unchanged unless a reviewed provider change is required, uploads the validated snapshot, rebuilds Oracle AI Vector Search from that exact snapshot, restarts the backend, then verifies `/retrieval/health` shows `oracle_ai_vector_search`, the expected chunk count, fallback inactive, and no primary store error.

## Operator Checklist

For a normal local ingestion check:

1. Build or rebuild the local snapshot with `knowledge/ingestion/ingest.py`.
2. Run corpus health against `knowledge/snapshots/oci-rag-index.json`.
3. Run retrieval regression before treating the snapshot as promotion-ready.
4. Promote and upload only through the refresh policy or a reviewed operator flow.
5. Rebuild Oracle AI Vector Search from the promoted snapshot, not from an unvalidated candidate.
6. Verify Object Storage remains ready as the config-only rollback provider.

## Safe Defaults

- Local development can use deterministic embeddings and `local_json`.
- Staging active retrieval uses `oracle_ai_vector_search` with OCI GenAI embeddings.
- Object Storage remains the immediate rollback provider.
- Refresh candidates are validated before promotion.
- Stable-doc refresh stays conservative until separately validated.
- Rollback uses the prior promoted local-hash snapshot/table or `local_json`.
