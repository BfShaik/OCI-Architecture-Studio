# Knowledge Refresh Policy

Last updated: 2026-05-15

## Purpose

OCI Architecture Studio should keep OCI guidance current without refreshing on every user query and without full reindexing unless the index contract changes.

The refresh policy separates fast-changing release knowledge from slower-moving OCI service documentation.

## Recommended Ingestion Cadence

| Source class | Cadence | Reason |
|---|---|---|
| OCI release notes | Every 6 hours in staging/prod; daily in local/dev when enabled | Release notes can affect service names, compatibility, security, migration, and architecture impact. |
| Fast-changing service pages | Daily | Security, limits, pricing, migration, and operational docs can change more often than reference architecture docs. |
| Stable OCI docs | Weekly, preferably Sunday 02:00 environment-local time | Reference docs are important but should not churn the index unnecessarily. |
| Full reindex | Manual only | Use when embedding model, chunking policy, metadata schema, or source registry changes. |

## Refresh Triggers

Scheduled:

- `release-watch`: scheduled release-note watcher.
- `stable-docs`: slower weekly refresh for stable source registry entries.

On change:

- new release-note item
- important release impact level such as `review`, `breaking`, or `security`
- service/domain impact that maps to indexed sources
- manual operator refresh after a known OCI announcement

Explicitly not supported:

- query-time refresh
- background refresh triggered by a user question

## Selective Reindex Rules

1. Ingest release notes into the separate release snapshot.
2. Compare new release items against the previous snapshot with a stable content key.
3. Classify new items by:
   - service
   - service domain
   - impact tags
   - impact level
4. Map the affected service/domain/impact to source IDs through `knowledge/refresh_policy.json`.
5. Refresh only those source IDs.
6. Merge refreshed chunks back into the existing index while retaining unaffected chunks.

Full reindex is reserved for:

- embedding provider/model change
- chunking size/overlap change
- metadata schema change
- source registry restructuring
- corrupted or missing index

## Eval-After-Refresh Workflow

After any selective refresh, run:

```bash
python knowledge/refresh/refresh_policy.py --mode release-watch
```

The policy runner performs:

1. release ingestion
2. selective knowledge ingestion
3. retrieval health check
4. retrieval regression check
5. golden evals
6. edge-case evals
7. advisory-quality evals
8. controlled orchestration evals

For quick local validation:

```bash
python knowledge/refresh/refresh_policy.py --mode release-watch --no-fetch --quick-gates
```

For weekly stable docs:

```bash
python knowledge/refresh/refresh_policy.py --mode stable-docs
```

## Rollback Approach

Before writing refreshed snapshots, the policy runner backs up:

- `knowledge/snapshots/oci-rag-index.json`
- `knowledge/snapshots/oci-release-snapshot.json`

If post-refresh gates fail and rollback is enabled, the previous snapshots are restored.

For OCI staging/prod, rollback remains config-safe:

- keep `local_json` as the validated rollback retrieval provider
- keep previous Object Storage manifest versions available
- upload the refreshed manifest only after eval/regression gates pass by passing `--oci-upload-bucket`
- restore the previous manifest object if a deployment smoke test fails

## Local/OCI Parity

The same policy runner is used locally, in CI, and in OCI environments.

Environment differences are config-only:

- local/dev can use `--no-fetch` and local embeddings
- staging/prod can fetch approved OCI sources and upload validated snapshots
- provider selection remains environment-driven

## Implementation Files

- `knowledge/refresh_policy.json`
- `knowledge/refresh/refresh_policy.py`
- `.github/workflows/knowledge-refresh.yml`
- `knowledge/ingestion/ingest.py`
- `knowledge/refresh/ingest_releases.py`
