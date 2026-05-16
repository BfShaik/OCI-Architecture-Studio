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
3. Normalize and classify new items by:
   - service
   - service domain
   - impact tags
   - impact level
   - change category such as security, HA/DR, observability, cost, migration, deprecation, enhancement, or compatibility risk
   - workload and architecture-domain relevance
4. Run deterministic impact analysis to identify affected services, source IDs, chunk IDs, targeted eval cases, refresh actions, and unresolved risks.
5. Map the affected service/domain/impact to source IDs through `knowledge/refresh_policy.json` plus built-in release-intelligence hints.
6. Refresh only those source IDs.
7. Apply release overlay metadata to impacted chunks when retagging is required.
8. Merge refreshed chunks back into the existing index while retaining unaffected chunks.

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
3. release impact analysis and targeted eval impact detection
4. selective candidate knowledge ingestion for affected source IDs
5. release overlay tagging for impacted chunks
6. retrieval health check against the candidate knowledge index
7. retrieval regression check against the candidate knowledge index
8. golden evals with `KNOWLEDGE_INDEX_PATH` and `RELEASE_SNAPSHOT_PATH` pointed at the candidate snapshots
9. edge-case evals
10. advisory-quality evals
11. controlled orchestration evals
12. promotion to authoritative snapshots only if all gates pass

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

It also preserves historical copies of the previously authoritative knowledge and release snapshots under:

```text
knowledge/snapshots/historical/
```

Those historical snapshots are retained for audit/context and future time-aware retrieval work. The current runtime remains current-first; it does not yet perform full bi-temporal retrieval.

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
- impacted eval case IDs
- release impact report
- historical snapshot paths when promotion occurs
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
- `knowledge/refresh/release_intelligence.py`
- `knowledge/ingestion/ingest.py`
- `knowledge/refresh/ingest_releases.py`
- `infra/scripts/release_impact_report.py`
- `infra/scripts/run_knowledge_refresh_vm.sh`
- `infra/scripts/install_knowledge_refresh_vm_cron.sh`
- `infra/terraform/modules/foundation/main.tf`
- `infra/functions/knowledge-refresh/`

## OCI-Native Schedule

Current staging recurring execution uses a conservative cron entry on the OCI backend VM. This keeps the refresh runtime inside OCI Compute, uses the same repository Python policy code, and avoids external schedulers while the OCI Function image startup issue is repaired.

GitHub Actions is no longer used for scheduled knowledge refresh. The only
remaining GitHub workflow is CI validation; refresh orchestration should be
run from OCI runtime infrastructure only.

VM cron safe-mode install:

```bash
infra/scripts/install_knowledge_refresh_vm_cron.sh <backend-host> opc ~/.ssh/oci-architecture-studio-staging
```

The installed cron file runs:

```bash
VM_REFRESH_MODE=release-watch \
VM_REFRESH_NO_FETCH=false \
VM_REFRESH_QUICK_GATES=true \
VM_REFRESH_CANDIDATE_ONLY=false \
VM_REFRESH_UPLOAD=true \
/opt/oci-architecture-studio/infra/scripts/run_knowledge_refresh_vm.sh
```

Release-watch upload/promotion is gate-controlled: failed candidates remain
under the run report directory and are not promoted or uploaded. Stable-docs
remains safe-mode until its live-refresh cadence is separately validated.
Reports are
written under `/var/lib/oci-architecture-studio/knowledge-refresh/reports` and
logs under `/var/log/oci-architecture-studio`.

OCI Functions plus Resource Scheduler remain the preferred later OCI-native
managed scheduling target, but they are currently deferred because deployed
Function invocation failed container initialization during dry run.

Deferred Terraform variables:


```hcl
enable_knowledge_refresh_scheduler = true
knowledge_refresh_function_image   = "iad.ocir.io/<namespace>/oci-architecture-studio/knowledge-refresh:<immutable-tag>"
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

The deferred function receives a JSON body:

```json
{"mode":"release-watch","upload":true}
```

or:

```json
{"mode":"stable-docs","upload":true}
```
