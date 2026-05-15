# OCI Architecture Studio — Operational Runbook

Date: 2026-05-15

## Working URLs

Use the backend-hosted app URL for the current staging baseline:

```text
http://193.122.149.102:8000/
```

Health endpoint:

```text
http://193.122.149.102:8000/health
```

Retrieval health endpoint:

```text
http://193.122.149.102:8000/retrieval/health
```

Advisory quality endpoint:

```text
http://193.122.149.102:8000/advisory/quality
```

Orchestration health endpoint:

```text
http://193.122.149.102:8000/orchestration/health
```

Knowledge refresh status endpoint:

```text
http://193.122.149.102:8000/knowledge/refresh/status
```

Operational diagnostics endpoints:

```text
http://193.122.149.102:8000/operations/profile
http://193.122.149.102:8000/operations/health
http://193.122.149.102:8000/operations/analytics
```

## Operational Diagnostics

Use the operational endpoints before promoting runtime changes. They summarize deployment profile, retrieval/vector health, release-refresh freshness, synthesis provider readiness, OCI Vault configuration-secret posture, OCI observability configuration, fallback events, hallucination findings, governance policy triggers, governance risk trends, confidence distribution, and provider usage.

Runtime profiles are configured with:

```bash
DEPLOYMENT_PROFILE=local_dev|oci_vm|oke|oci_functions
```

Profile examples live under `infra/runtime-profiles/`. Local development remains offline-safe. OCI VM and OKE profiles should use OCI IAM runtime identity and OCI Vault-backed sensitive configuration. OCI Functions-compatible execution is intended for scheduled refresh jobs invoked by OCI Resource Scheduler.

Run a lightweight endpoint gate:

```bash
app/backend/.venv/bin/python infra/scripts/operational_readiness_check.py \
  --api-base-url http://localhost:8000
```

For staging, add `--require-oci-profile` once the deployed runtime is expected to report an OCI profile instead of `local_dev`.

Live OCI SDK connectivity checks are controlled by `OCI_CONNECTIVITY_CHECK_ENABLED`. Keep this disabled until IAM policies, dynamic groups, and Vault access are verified.

## Verify Deployment Health

Run:

```bash
python3 infra/scripts/verify_staging_baseline.py \
  --api-base-url http://193.122.149.102:8000 \
  --frontend-url http://193.122.149.102:8000/ \
  --expected-retrieval-provider oci_object_storage \
  --expected-chunks 21
```

Expected result:

```text
"passed": true
```

## Rerun Smoke Tests

Backend, frontend, and OCI SDK:

```bash
python3 infra/scripts/smoke_oci_deployment.py \
  --api-base-url http://193.122.149.102:8000 \
  --frontend-url http://193.122.149.102:8000/ \
  --check-oci-sdk
```

OCI resource visibility:

```bash
python3 infra/scripts/check_oci_access.py \
  --profile DEFAULT \
  --compartment-id "$(terraform -chdir=infra/terraform/envs/staging output -raw compartment_ocid)" \
  --bucket-name "$(terraform -chdir=infra/terraform/envs/staging output -raw snapshots_bucket_name)" \
  --secret-id "$(terraform -chdir=infra/terraform/envs/staging output -raw app_config_secret_ocid)" \
  --log-group-id "$(terraform -chdir=infra/terraform/envs/staging output -raw log_group_ocid)" \
  --alarm-id "$(terraform -chdir=infra/terraform/envs/staging output -raw backend_cpu_alarm_ocid)" \
  --event-rule-id "$(terraform -chdir=infra/terraform/envs/staging output -raw resource_lifecycle_event_rule_ocid)"
```

## Rerun Evals

```bash
app/backend/.venv/bin/python evals/run_golden.py --output-dir evals/reports/golden
app/backend/.venv/bin/python evals/run_golden.py --cases evals/edge-cases.jsonl --output-dir evals/reports/edge-cases
app/backend/.venv/bin/python evals/run_golden.py --cases evals/advisory-quality.jsonl --output-dir evals/reports/advisory-quality
app/backend/.venv/bin/python evals/run_golden.py --cases evals/orchestration-quality.jsonl --output-dir evals/reports/orchestration-quality
app/backend/.venv/bin/python evals/run_golden.py --cases evals/enterprise-governance.jsonl --output-dir evals/reports/enterprise-governance
```

## Run Knowledge Refresh Policy

Release notes and fast-changing OCI sources are refreshed on a schedule or on explicit operator action. They are not refreshed on user queries.

Release watcher:

```bash
app/backend/.venv/bin/python knowledge/refresh/refresh_policy.py --mode release-watch
```

Local/offline smoke:

```bash
app/backend/.venv/bin/python knowledge/refresh/refresh_policy.py --mode release-watch --no-fetch --quick-gates
```

Stable docs cadence:

```bash
app/backend/.venv/bin/python knowledge/refresh/refresh_policy.py --mode stable-docs
```

If post-refresh gates fail, do not promote the candidate. Inspect the run folder and keep the authoritative snapshots unchanged.

Current behavior is candidate-first:

- candidates are written under `knowledge/reports/runs/<run_id>/candidates`
- gates run against candidate paths
- authoritative snapshots are promoted only after gates pass
- run lineage is written to `knowledge/reports/runs/<run_id>/manifest.json`
- latest operational state is written to `knowledge/reports/knowledge-refresh-status.json`

Rollback latest promoted refresh:

```bash
app/backend/.venv/bin/python knowledge/refresh/refresh_policy.py --rollback-latest
```

## Rerun Retrieval Parity

```bash
app/backend/.venv/bin/python infra/scripts/retrieval_parity_check.py \
  --oci-region us-ashburn-1 \
  --oci-profile DEFAULT \
  --oci-namespace idsmrn7rvqb6 \
  --oci-vector-bucket oci-architecture-studio-staging-knowledge-snapshots \
  --oci-vector-object-name oci-rag-index.json \
  --output-dir evals/reports/retrieval-parity
```

## Rerun Local Quality Gates

```bash
app/backend/.venv/bin/python knowledge/ingestion/ingest.py --no-fetch
app/backend/.venv/bin/python knowledge/refresh/ingest_releases.py --no-fetch
cd app/backend && PYTHONPATH=src .venv/bin/pytest -q
cd ../frontend && npm run build
```

Terraform validation:

```bash
terraform fmt -check -recursive infra/terraform
terraform -chdir=infra/terraform/envs/staging validate
```

## Inspect Backend Service

SSH to the VM:

```bash
ssh -i ~/.ssh/oci-architecture-studio-staging opc@193.122.149.102
```

Check service:

```bash
sudo systemctl status oci-architecture-studio --no-pager
```

Follow logs:

```bash
sudo journalctl -u oci-architecture-studio -f
```

Restart service:

```bash
sudo systemctl restart oci-architecture-studio
```

## Redeploy App

```bash
infra/scripts/deploy_backend_vm.sh \
  193.122.149.102 \
  opc \
  ~/.ssh/oci-architecture-studio-staging
```

Then rerun:

```bash
python3 infra/scripts/verify_staging_baseline.py \
  --api-base-url http://193.122.149.102:8000 \
  --frontend-url http://193.122.149.102:8000/
```

## Upload Snapshots

```bash
infra/scripts/sync_snapshots_to_object_storage.sh \
  idsmrn7rvqb6 \
  oci-architecture-studio-staging-knowledge-snapshots
```

## Local vs OCI Troubleshooting

If local tests fail:

- check Python virtualenv
- check generated snapshots
- check eval reports under `evals/reports`
- do not redeploy until local gates are green

If local tests pass but OCI fails:

- check systemd service logs
- check `/etc/oci-architecture-studio.env`
- check that `/opt/oci-architecture-studio/app/frontend/dist` exists
- check `/opt/oci-architecture-studio/knowledge/snapshots`
- rerun deployment script

If frontend loads but Review fails:

- use `http://193.122.149.102:8000/`, not the Object Storage HTTPS URL
- check browser console for mixed-content or network errors
- run the backend smoke test

If retrieval fails:

- check `/retrieval/health`
- confirm chunk count is at least 21 for the current staging baseline
- rerun ingestion on the VM through the deploy script

If advisory confidence drops:

- check `/advisory/quality`
- inspect `quality_warnings` and `evidence_links` in the API response
- add source chunks when useful recommendations lack evidence
- add a regression eval for any repeated failure pattern

If controlled orchestration behaves unexpectedly:

- check `/orchestration/health`
- confirm `ADVISORY_ORCHESTRATION_MODE=multi_agent_pilot` for normal pilot behavior
- confirm `active_agents` includes `supervisor`, `validation_critic`, and `final_synthesizer`
- inspect `agent_contributions`, `aggregation_decision`, `critic_findings`, `orchestration_warnings`, and `agent_trace` in the API response
- roll back to `ADVISORY_ORCHESTRATION_MODE=supervised` if multi-agent contribution metadata causes response quality issues
- roll back with `ADVISORY_ORCHESTRATION_MODE=single_pass` if agent metadata causes response or UI issues

If GenAI synthesis needs rollback:

- set `ADVISORY_SYNTHESIS_PROVIDER=deterministic`
- restart `oci-architecture-studio`
- rerun `/advisory/quality` and baseline smoke tests
- inspect `synthesis_warnings` and `synthesis_fallback_used` in API responses

Before enabling OCI GenAI synthesis, run:

```bash
app/backend/.venv/bin/python infra/scripts/genai_synthesis_parity_check.py \
  --cases evals/golden-prompts.jsonl \
  --cases evals/edge-cases.jsonl \
  --output-dir evals/reports/genai-parity
```

The parity gate must pass without GenAI fallback before staging is switched from deterministic synthesis.

If `oci_object_storage` promotion fails:

- set `RETRIEVAL_PROVIDER=local_json`
- restart `oci-architecture-studio`
- rerun baseline smoke tests
- inspect `/retrieval/health`
- restore `RETRIEVAL_PROVIDER=oci_object_storage` only after the Object Storage manifest path is healthy again

When restoring `/etc/oci-architecture-studio.env`, preserve systemd-readable permissions and SELinux context:

```bash
sudo install -o root -g root -m 0644 /tmp/oci-architecture-studio.env /etc/oci-architecture-studio.env
sudo restorecon /etc/oci-architecture-studio.env
sudo systemctl reset-failed oci-architecture-studio
sudo systemctl restart oci-architecture-studio
```

Avoid `sudo mv` from `/tmp` into `/etc` because it can carry a `user_tmp_t` SELinux label and cause systemd `Failed to load environment files: Permission denied`.

## Rollback

App-only rollback:

1. Check out the previous known-good Git commit locally.
2. Run `infra/scripts/deploy_backend_vm.sh`.
3. Rerun baseline smoke tests.

Infrastructure rollback:

```bash
terraform -chdir=infra/terraform/envs/staging destroy
```

Use full destroy only for sandbox teardown. Capture logs and outputs first if debugging a failure.

## Current Operational Risks

- Public HTTP backend
- Public SSH
- local Terraform state
- placeholder Vault secret
- no app log shipping into OCI Logging yet
- no custom app metrics yet
- active staging retrieval uses `oci_object_storage`; `local_json` remains the rollback provider

The next hardening milestone is HTTPS ingress and restricted backend access.
