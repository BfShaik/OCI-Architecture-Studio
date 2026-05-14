# Knowledge

This area will hold the RAG and release-awareness pipeline.

## Current State

The first local RAG layer is implemented with:

- `source_registry.json` for the initial OCI source list
- `ingestion/ingest.py` for fetching, chunking, and embedding source text
- `snapshots/oci-rag-index.json` as the local generated vector index
- `release_source_registry.json` for official OCI release sources
- `refresh/ingest_releases.py` for release snapshot ingestion and classification
- `snapshots/oci-release-snapshot.json` as the generated release snapshot

The current embedding implementation is deterministic and local. It is useful for validating the retrieval workflow, but it should be replaced with a production embedding provider when the corpus grows.

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

## Subdirectories

- `ingestion/` - source loading and document normalization
- `classifiers/` - future classification helpers for release notes and source types
- `refresh/` - release-aware refresh and snapshot jobs
- `snapshots/` - local metadata snapshots, ignored by default except `.gitkeep`
