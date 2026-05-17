# Knowledge

Knowledge ingestion, embeddings, vector manifests, and release-awareness pipeline.

## Current State

The repository supports two modes:

- **Local development:** deterministic local embeddings and `knowledge/snapshots/oci-rag-index.json`.
- **Staging:** OCI GenAI embeddings with `cohere.embed-v4.0`, 1536 dimensions, Oracle AI Vector Search, and Object Storage rollback manifests.

The pipeline is implemented with:

- `source_registry.json` for the initial OCI source list
- `ingestion/ingest.py` for fetching, chunking, and embedding source text
- `snapshots/oci-rag-index.json` as the generated vector manifest
- `release_source_registry.json` for official OCI release sources
- `refresh/ingest_releases.py` for release snapshot ingestion and classification
- `refresh_policy.json` and `refresh/refresh_policy.py` for scheduled release watching, selective reindex, candidate-first eval gates, version lineage, and rollback-safe refresh
- `snapshots/oci-release-snapshot.json` as the generated release snapshot

Local hashing remains useful for offline development and rollback validation. Staging uses OCI GenAI embeddings.

## Run Ingestion

From the repository root:

```bash
python3 knowledge/ingestion/ingest.py
```

Offline fallback mode:

```bash
python3 knowledge/ingestion/ingest.py --no-fetch
```

## Run Release Ingestion

```bash
python3 knowledge/refresh/ingest_releases.py
```

Offline fallback mode:

```bash
python3 knowledge/refresh/ingest_releases.py --no-fetch
```

## Run Refresh Policy

```bash
python3 knowledge/refresh/refresh_policy.py --mode release-watch
```

Local smoke mode:

```bash
python3 knowledge/refresh/refresh_policy.py --mode release-watch --no-fetch --quick-gates
```

The policy runner does not run on user queries. It watches release sources on a schedule or by explicit operator action, maps important changes to affected source IDs, refreshes only those chunks as candidate snapshots, runs eval/regression gates against the candidates, and promotes them only after validation passes.

Rollback latest promoted refresh:

```bash
python3 knowledge/refresh/refresh_policy.py --rollback-latest
```

## Operator Flow

For a beginner-friendly explanation of how approved OCI docs become chunks, metadata, embeddings, Object Storage manifests, and Oracle AI Vector Search rows, see:

- `docs/current/ingestion-to-retrieval-flow.md`

## Subdirectories

- `ingestion/` - source loading and document normalization
- `classifiers/` - future classification helpers for release notes and source types
- `refresh/` - release-aware refresh and snapshot jobs
- `snapshots/` - local metadata snapshots, ignored by default except `.gitkeep`
