# Roadmap

## Phase 1 — MVP Foundation
Status: Validated Complete

Deliverables:
- monorepo setup — Done
- README and AGENTS — Done
- backend scaffold — Done
- frontend scaffold — Done
- prompt templates — Done
- first OCI knowledge ingestion — Done
- first architecture advisor flow — Done
- local RAG index — Done
- intent-aware orchestration — Done
- golden prompt suite — Done
- project status and two-week plan — Done
- edge-case eval suite — Done
- demo readiness checklist — Done

Exit criteria:
- A user can submit an OCI architecture question through the UI. — Done
- The backend returns a structured response through local retrieval and intent-aware orchestration. — Done
- The response includes intent, prompt template, assumptions, recommendations, risks, citations, and next steps. — Done
- Golden prompts capture expected behavior for core product intents. — Done
- A machine-readable eval runner exists. — Done

## Phase 2 — Grounded Retrieval
Status: In Progress — Object Storage active in staging

Architecture plan: `docs/phase-2-architecture.md`
OCI deployment plan: `docs/oci-deployment-architecture.md`
OCI deployment execution runbook: `docs/oci-deployment-execution.md`

Deliverables:
- curated seed corpus — In Progress
- document chunking — Done
- metadata model — Done
- local retrieval adapter — Done
- OCI Object Storage retrieval adapter — Done
- dual-provider retrieval parity gate — Done
- config-only Object Storage staging promotion — Done
- rollback validation to `local_json` — Done
- citation display — Done
- regression evals for grounded answers — Done
- config-only promotion and rollback path — Done
- evidence-linked recommendations — Done
- confidence scoring and low-confidence fallback — Done
- advisory-quality eval suite — Done
- production embedding provider — Pending
- Oracle AI Vector Search active read path — Pending

## Phase 2B — Advisory Intelligence Quality
Status: In Progress — controlled multi-agent pilot added

Deliverables:
- recommendation-to-citation evidence links — Done
- confidence scoring — Done
- not-enough-evidence behavior — Done
- unsupported requested service warnings — Done
- advisory-quality metrics endpoint — Done
- advisory-quality eval suite — Done
- config-selected OCI GenAI synthesis adapter — Done
- deterministic synthesis rollback — Done
- citation-aware GenAI synthesis hardening — MVP Done
- supervised orchestration mode — Done
- supervisor routing and specialist advisor boundaries — Done
- controlled multi-agent pilot mode — Done
- specialist contribution records — Done
- final synthesis aggregation decision — Done
- validation critic findings — Done
- orchestration observability endpoint — Done
- orchestration-quality eval suite — Done
- stronger unsupported-claim suppression — Pending
- critic policy-gate behavior — Pending
- quality trend dashboard — Pending

## Phase 2C — Supervised Agent Evolution
Status: Controlled Multi-Agent Pilot Complete

Deliverables:
- one supervisor/orchestrator — Done
- bounded architecture advisor — Done
- bounded migration advisor — Done
- bounded HA/DR advisor — Done
- bounded cost advisor — Done
- bounded release-awareness advisor — Done
- validation/critic agent — Done
- deterministic multi-agent specialist selection — Done
- shared evidence layer across agents — Done
- one final synthesis step — Done
- config-only rollback to single-pass flow — Done
- provider-agnostic synthesis boundary — Done
- autonomous planning loops — Deferred
- multi-agent memory — Deferred
- distributed orchestration framework — Deferred

## Phase 3 — Release-Aware Knowledge
Status: Continuous intelligence foundation implemented

Deliverables:
- OCI release source registry — Done
- refresh job scaffold — Done
- snapshot freshness metadata — Done
- change classification — MVP Done
- release-aware intent routing — Done
- release snapshot reader — Done
- scheduled release-note watcher policy — Done
- selective source refresh rules — Done
- eval-after-refresh workflow — Done
- candidate-first snapshot validation — Done
- eval-gated promotion — Done
- ingestion run/version lineage — Done
- refresh status endpoint — Done
- manifest-driven rollback automation — Done
- rollback-safe refresh snapshots — Done
- OCI scheduled refresh scaffold — Done
- release impact summaries — Pending
- stale-knowledge warnings — MVP Done
- OCI Monitoring metrics for refresh/gate health — Pending

## Phase 4 — OCI Deployment Execution
Status: Staging deployed and validated

Deliverables:
- OCI-native deployment architecture — Done
- Terraform foundation module — Done
- `dev`, `test`, and `staging` Terraform environments — Done
- staging deployment execution runbook — Done
- backend Compute deployment script — Done
- frontend Object Storage upload script — Done
- knowledge snapshot Object Storage upload script — Done
- OCI access validation helper — Done
- deployment smoke test for health, retrieval, and release-aware path — Done
- OCI-native deployment automation through OCI DevOps — Future
- first Terraform apply to OCI — Done
- first backend/frontend cloud smoke test — Done
- staging resource visibility checks — Done
- staging baseline guardrail — Done

## Phase 5 — Retrieval Promotion And Vector Search
Status: Started

Deliverables:
- promote staging to `RETRIEVAL_PROVIDER=oci_object_storage` — Done
- post-promotion smoke/eval/retrieval regression — Done
- Object Storage rollback validation — Done
- Oracle AI Vector Search schema design — Pending
- Oracle AI Vector Search indexing prototype — Pending
- Oracle AI Vector Search dual-run parity — Pending
- controlled promotion from Object Storage manifest to Oracle AI Vector Search — Pending
