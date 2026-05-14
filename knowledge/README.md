# Knowledge

This area will hold the RAG and release-awareness pipeline.

## Current State

The scaffold intentionally includes only placeholders. The first production step should be a small curated OCI source registry and a local retrieval adapter.

## Subdirectories

- `ingestion/` - source loading and document normalization
- `classifiers/` - future classification for release notes and source types
- `refresh/` - future scheduled refresh jobs
- `snapshots/` - local metadata snapshots, ignored by default except `.gitkeep`
