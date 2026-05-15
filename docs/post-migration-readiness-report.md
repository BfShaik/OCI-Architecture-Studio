# OCI Architecture Studio — Post-Migration Readiness Report

Date: 2026-05-15

Current validated baseline: `d3292d6`

Staging URL: `http://193.122.149.102:8000/`

## Overall Health

Status: **GO for continued Sprint 2 development**

The platform is stable after the Sprint 2 retrieval migration slice. Local validation, evals, retrieval regression, frontend build, Terraform validation, OCI staging smoke tests, and OCI resource visibility checks passed.

Important caveat: the active staging retrieval provider is still `local_json`. OCI-native retrieval hooks, Object Storage snapshot integration, OCI embedding configuration, and the guarded Oracle AI Vector Search boundary exist, but Oracle AI Vector Search is not yet the active staging read path. Treat the current state as migration-ready and parity-ready, not a completed production Vector Search cutover.

## Full Regression Summary

| Area | Result | Notes |
|---|---:|---|
| Knowledge ingestion | Passed | `13` chunks generated from `13` sources |
| Release ingestion | Passed | `3` release items generated |
| Backend tests | Passed | `30 passed in 1.47s` |
| Golden evals | Passed | `6 passed, 0 failed` |
| Edge-case evals | Passed | `8 passed, 0 failed` |
| Retrieval health | Passed | `local_json`, `13` chunks, no warnings |
| Retrieval regression | Passed | `14 passed, 0 failed` |
| Frontend build | Passed | Vite build completed in `4.96s` |
| Python compile checks | Passed | backend, infra scripts, ingestion, refresh |
| Terraform fmt | Passed | recursive formatting check |
| Terraform validate | Passed | `dev`, `test`, and `staging` |
| Staging baseline guardrail | Passed | backend, retrieval, architecture review, frontend |
| Staging deployment smoke | Passed | backend, frontend, OCI SDK tenancy access |
| OCI resource visibility | Passed | Object Storage, Vault secret, Logging, Monitoring alarm, Events rule |

Flaky behavior warning: none observed in this run. This was a single-pass validation; no retry loop was used.

Regression observations:

- The advisory workflow remained stable after metadata-aware ranking changes.
- Evals and retrieval regression stayed green.
- Staging retrieval metrics showed no missing-index warnings.
- No stale citations surfaced in the scenario spot checks.

## Retrieval Quality Assessment

The retrieval layer is currently:

- **Grounded:** responses return citation objects with chunk IDs and source URLs.
- **Citation-aware:** all spot-check citations had a source URL or URL.
- **Metadata-aware:** local regression validates service/domain coverage, and ranking uses intent, service domain, architecture pattern, trust, freshness, and release hints.
- **Freshness-aware:** stale citation flags were checked; none surfaced in the main scenarios.
- **Release-aware:** release-awareness intent routes correctly and returns release-context caution through the existing release snapshot path.

### Intent Spot Checks

| Scenario | Intent | Citation Count | Evidence Summary | Stale Citations |
|---|---|---:|---|---:|
| Highly available ecommerce | `architecture` | 6 | Architecture Center, Load Balancer, Database Services, Object Storage, CDN, Compute | 0 |
| EKS + RDS migration | `migration` | 6 | OKE, Database Migration, Database Services, Cost Management, Load Balancer | 0 |
| Fintech DR | `dr` | 6 | Full Stack Disaster Recovery, Database Services, VCN, Security Services, Well-Architected | 0 |
| Cost-optimized web app | `cost` | 6 | Cost Management, Object Storage, Compute, CDN, Well-Architected | 0 |
| Latest OCI update impact | `release_awareness` | 6 | Architecture Center, Security Services, Object Storage, Database Services, Well-Architected | 0 |

Quality observations:

- Architecture answers are supported by ingress, storage, compute, and data-tier citations.
- Migration answers include OKE and database migration evidence.
- DR answers are grounded in DR, database, networking, and security evidence.
- Cost answers retrieve Cost Management plus compute/storage optimization evidence.
- Release-awareness answers correctly avoid claiming current release truth without explicit release context.

## OCI-Native Platform Validation

| Component | Status | Notes |
|---|---|---|
| OCI SDK connectivity | Passed | Local SDK authenticated and read tenancy successfully |
| Object Storage integration | Passed | Snapshot bucket visible with `oci-rag-index.json` and `oci-release-snapshot.json` |
| Vault secret access | Passed | Secret bundle readable |
| Logging visibility | Passed | Staging log group readable |
| Monitoring visibility | Passed | Backend CPU alarm readable |
| Events / Notifications | Passed | Resource lifecycle rule readable |
| OCI embedding generation | Not live-validated in this run | Adapter and config exist; requires OCI GenAI model/compartment inputs for live embedding generation |
| Vector indexing | Partially validated | Object Storage vector manifest exists; Oracle AI Vector Search table/index read path remains guarded |
| Vector search behavior | Partially validated | Local JSON search and Object Storage-compatible manifest contract validated; Oracle AI Vector Search is not active |
| Metadata persistence | Passed locally | Chunk metadata includes service, domain, intent tags, freshness, trust, architecture patterns, content hash, and vector readiness |

## Environment Consistency

The one-codebase, multiple-environments rule is preserved.

- Local and staging use the same backend/frontend codebase.
- Config remains environment-driven through `.env`, Terraform variables, and deployment scripts.
- No environment-specific application fork was introduced.
- Evals still execute against the same prompt and retrieval contracts.
- Rollback remains configuration-first: set `EMBEDDING_PROVIDER=local` and `RETRIEVAL_PROVIDER=local_json`.

Observed difference:

- Staging is intentionally still using `local_json` for the active read path. That is safe for baseline stability, but it means the production Vector Search read path has not yet been proven as the active provider.

## Observability Assessment

Validated:

- `/health`
- `/retrieval/health`
- retrieval request count
- missing-index count
- retrieval latency
- result count
- active provider
- embedding model
- last intent
- warnings
- OCI Logging log group visibility
- OCI Monitoring alarm visibility
- Events rule visibility

Gaps:

- No dashboard yet for retrieval latency and no-result trend.
- No persistent metric export for embedding generation latency.
- No vector index freshness/age alarm.
- No eval trend dashboard.
- No automated alert for stale snapshot age.
- No production trace correlation across frontend, backend, retrieval, and ingestion.

## Production-Readiness Review

### Scalability Risks

- Local JSON retrieval is fine for the current small corpus but will not scale to a full OCI documentation corpus.
- Object Storage manifest retrieval is migration-safe but not the final low-latency vector engine.
- Oracle AI Vector Search read behavior still needs schema validation and active-provider parity testing.

Mitigation:

- Continue dual-run retrieval parity before any cutover.
- Add corpus size and retrieval latency thresholds to CI/staging smoke tests.

### Operational Risks

- Backend is still directly exposed on port `8000`.
- HTTPS ingress is not yet implemented.
- Terraform state should move to OCI Object Storage before broader team operations.

Mitigation:

- Add HTTPS ingress through API Gateway or Load Balancer.
- Move Terraform state to remote backend before more infrastructure growth.

### Stale Knowledge Risks

- Release snapshot exists but is not yet a full watcher/intelligence/refresh workflow.
- Current release-impact analysis is advisory and cautionary, not authoritative.

Mitigation:

- Add release snapshot age checks and stale-source alarms.
- Add current-vs-historical comparison in release-aware responses.

### Retrieval Quality Risks

- Corpus is still intentionally small.
- Required service coverage is checked heuristically, not semantically.
- Full citation-aware LLM synthesis is not implemented yet.

Mitigation:

- Expand official OCI sources.
- Add retrieval diff reports between `local_json`, Object Storage manifest, and Oracle AI Vector Search.
- Add unsupported-claim suppression before full LLM synthesis.

## Rollback Considerations

Rollback remains simple:

```bash
EMBEDDING_PROVIDER=local
RETRIEVAL_PROVIDER=local_json
KNOWLEDGE_INDEX_PATH=knowledge/snapshots/oci-rag-index.json
```

Then rerun:

```bash
app/backend/.venv/bin/python knowledge/ingestion/ingest.py --no-fetch
app/backend/.venv/bin/python infra/scripts/check_retrieval_health.py --provider local_json
app/backend/.venv/bin/python infra/scripts/retrieval_regression_check.py \
  --cases evals/golden-prompts.jsonl \
  --cases evals/edge-cases.jsonl \
  --output-dir evals/reports/retrieval
cd app/backend && PYTHONPATH=src .venv/bin/pytest -q
```

## Confidence Level

Confidence: **Medium-high for continued Sprint 2 development**

Rationale:

- The current app baseline is healthy.
- Regression and staging smoke tests pass.
- Retrieval remains grounded and citation-aware.
- OCI platform connectivity is validated.
- The remaining uncertainty is the active Oracle AI Vector Search cutover, which has not yet been enabled in staging.

## Go / No-Go

Decision: **GO for continued Sprint 2 development**

No-go boundary:

- Do not claim production Oracle AI Vector Search cutover until the active staging provider changes from `local_json` to the OCI-native read path and passes parity/eval checks.

## Recommended Next Milestone

Single highest-value next milestone:

**Run dual-provider retrieval parity in staging using OCI Object Storage manifest retrieval, then promote it behind configuration only if golden evals, edge evals, retrieval regression, and scenario spot checks match the local baseline.**

This is the safest next step because it proves OCI-native retrieval storage without forcing an immediate Oracle AI Vector Search cutover or risking the working advisory workflow.
