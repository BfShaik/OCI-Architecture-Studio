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

## Eval-Gated Promotion Workflow

After any selective refresh, run:

```bash
python knowledge/refresh/refresh_policy.py --mode release-watch
```

The policy runner performs:

1. release ingestion
2. candidate release snapshot creation under `knowledge/reports/runs/<run_id>/candidates`
3. selective candidate knowledge ingestion for affected source IDs
4. retrieval health check against the candidate knowledge index
5. retrieval regression check against the candidate knowledge index
6. golden evals with `KNOWLEDGE_INDEX_PATH` and `RELEASE_SNAPSHOT_PATH` pointed at the candidate snapshots
7. edge-case evals
8. advisory-quality evals
9. controlled orchestration evals
10. promotion to authoritative snapshots only if all gates pass

For quick local validation:

```bash
python knowledge/refresh/refresh_policy.py --mode release-watch --no-fetch --quick-gates
```

For weekly stable docs:

```bash
python knowledge/refresh/refresh_policy.py --mode stable-docs
```

## Rollback Approach

The policy is candidate-first. It does not overwrite authoritative snapshots until validation passes.

When validation passes, the policy runner promotes candidate snapshots to:

- `knowledge/snapshots/oci-rag-index.json`
- `knowledge/snapshots/oci-release-snapshot.json`

During promotion it stores rollback copies under the run directory:

```text
knowledge/reports/runs/<run_id>/rollback/
```

If post-refresh gates fail, the candidate is kept for inspection but authoritative snapshots are not changed.

Operator rollback:

```bash
python knowledge/refresh/refresh_policy.py --rollback-latest
```

Rollback restores the previous promoted snapshots from the latest run manifest and records an event in `knowledge/reports/knowledge-refresh-status.json`.

## Versioning And Lineage

Each refresh writes:

- `knowledge/reports/runs/<run_id>/manifest.json`
- `knowledge/reports/runs/<run_id>/knowledge-refresh-report.json`
- `knowledge/reports/knowledge-refresh-report.json`
- `knowledge/reports/knowledge-refresh-status.json`

The manifest tracks:

- ingestion run ID
- candidate and promoted snapshot paths
- knowledge snapshot version
- release snapshot version
- embedding provider and embedding version
- metadata schema version
- affected source IDs
- changed release IDs
- gate results
- rollback sources

The backend exposes the latest operational status at:

```text
GET /knowledge/refresh/status
```

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
- `infra/terraform/modules/foundation/main.tf`
- `infra/functions/knowledge-refresh/`

## OCI-Native Schedule

OCI recurring execution is implemented with OCI Resource Scheduler invoking an OCI Function. OCI Events remains in use for operational notifications and resource lifecycle visibility, but recurring cron-style execution is modeled as Resource Scheduler because OCI Events rules do not expose a cron schedule field in the Terraform provider.

Terraform variables:

```hcl
enable_knowledge_refresh_scheduler = true
knowledge_refresh_function_image   = "iad.ocir.io/<namespace>/oci-architecture-studio/knowledge-refresh:latest"
knowledge_refresh_release_cron     = "17 */6 * * *"
knowledge_refresh_stable_docs_cron = "23 2 * * 0"
```

Created resources when enabled:

- OCI Functions application
- OCI knowledge refresh function
- release-note Resource Scheduler schedule
- stable-docs Resource Scheduler schedule
- dynamic group for the schedules
- IAM policy allowing the schedules to invoke the function

The function receives a JSON body:

```json
{"mode":"release-watch","upload":true}
```

or:

```json
{"mode":"stable-docs","upload":true}
```
