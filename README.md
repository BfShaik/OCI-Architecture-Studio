# OCI Architecture Studio

OCI Architecture Studio is an enterprise AI platform for OCI architecture guidance, migration advisory, cost optimization, and release-aware OCI knowledge synchronization.

Current version: `1.0.3`

The project is monorepo-first, RAG-first, modular, and evaluation-driven. Prompts, retrieval code, evals, and application code are treated as first-class assets from the start.

## Current Working Flow

OCI Architecture Studio currently supports a validated advisory flow in local development and OCI staging:

1. User asks an OCI architecture, migration, DR, cost, security, or release-awareness question in the React UI.
2. The frontend calls the FastAPI backend.
3. The backend classifies the request intent and applies the matching advisory profile.
4. Retrieval runs through a config-selected provider, applies source-service mapping, detects architecture-domain heuristics, and reranks a wider candidate set before selecting final chunks.
5. The active staging provider is `oci_object_storage`, reading the validated vector manifest from OCI Object Storage.
6. Local development defaults to `local_json`; it also remains the tested config-only rollback provider for staging.
7. The controlled orchestration layer selects deterministic specialist roles, shares the same retrieved evidence across them, and runs a validation critic over evidence support, citations, freshness, and unsupported-claim risk. These are in-process role boundaries, not autonomous agents.
8. One final synthesis step generates the advisory response through the configured provider with deterministic rollback available. Deterministic synthesis now uses lightweight architecture pattern profiles, retrieved evidence, workload heuristics, and consistency checks rather than only profile boilerplate. OCI GenAI synthesis can be enabled through configuration and uses the same retrieved context through a dedicated grounding prompt builder.
9. Release-awareness uses local release snapshots, deterministic release classification, impact analysis, release overlays on affected chunks, and refresh-policy automation. In staging, release-watch refresh now runs from the OCI backend VM cron path with live release fetch, quick gates, gated promotion, and Object Storage upload; stable-doc refresh remains safe/candidate-only. Refresh still never runs on user queries.
10. The backend returns structured recommendations, concise decision reasoning metadata, consistency findings, confidence, evidence links, section citation metadata, deterministic enterprise-governance assessment metadata, lightweight architecture topology metadata, executive experience metadata, FinOps/migration optimization metadata, optional retrieval debug traces, release context, temporal knowledge context, and standard architecture response sections. The current UI renders the main advisory fields, executive brief, implementation sequence, topology/dependency summaries, comparison summaries, explainability highlights, migration/FinOps optimization summaries, exportable Markdown summary, and citation cards. Full section-level citation UI, live diagram rendering, and release-context UI are future work.
11. Operational diagnostics expose deployment profile, retrieval health, release refresh freshness, synthesis availability, OCI secret/config posture, API Gateway/OCI DevOps readiness metadata, infrastructure visibility, governance/risk counters, runtime readiness, and lightweight runtime analytics through additive endpoints. Live OCI connectivity checks are opt-in so local development stays offline-safe.

LangGraph, advanced memory, and autonomous agent execution remain deferred. Oracle AI Vector Search provider code, Autonomous Database infrastructure, schema/index tooling, and shadow sync exist and have been validated against the refreshed 47-chunk snapshot, but staging active-read promotion remains deferred until refreshed parity, regression, smoke, and rollback gates pass without exception.

## Repository Layout

```text
docs/                 Product, roadmap, sprint, and architecture docs
app/backend/          Python 3.12 FastAPI backend
app/frontend/         React + Vite frontend
knowledge/            Source registries, ingestion, release refresh, and snapshots
prompts/              Versioned prompt templates
evals/                Regression prompts and expected behavior
infra/                Deployment and CI/CD assets
tests/                Backend and integration tests
```

## Current Capabilities

- Local OCI source registry and ingestion pipeline
- Curated local OCI architecture corpus with 47 chunks in the current branch
- Scalable ingestion scaffolding for source groups, source categories, release tags, chunk lineage, section hierarchy, and source traceability
- Deterministic local embeddings for development
- Optional OCI Generative AI embeddings with provider switching, dimensional validation, failure diagnostics, and deterministic local fallback
- JSON vector index for local retrieval
- Citation-friendly chunk metadata with service, service category, domain, workload, architecture pattern, trust, intent tags, migration mappings, and freshness score
- Automatic chunk-level metadata enrichment for OCI service references, workload/domain labels, migration relevance, HA/DR relevance, cost relevance, security/compliance tags, and architecture pattern tags
- Lightweight corpus health validation for chunk count, metadata completeness, missing service tags, orphaned chunks, duplicate content, empty embeddings, and coverage gaps
- Lightweight retrieval reranking that combines semantic similarity, intent match, service relevance, metadata overlap, architecture pattern match, workload/domain relevance, topic match, and migration mapping match
- Optional retrieval debug traces through request flag `retrieval_debug` or environment flag `RETRIEVAL_DEBUG_ENABLED`
- Backend section citation plumbing with chunk ID, source document, OCI service category, and service name
- Architecture-domain heuristics for ecommerce, fintech, SaaS, AI/ML inference, observability platforms, and analytics platforms
- AWS-to-OCI service mapping for container, database, storage, CDN/DNS, networking, observability, security, AI/ML, and data engineering source services
- Deterministic architecture pattern profiles for HA web apps, Kubernetes modernization, fintech DR, AI inference, analytics/data lake, multi-region SaaS, active/passive DR, event-driven systems, serverless workloads, and secure landing zones
- Deterministic architecture reasoning profiles for HA/DR, migration, SaaS, fintech, AI/ML inference, analytics/data platforms, observability platforms, and cost-optimized workloads
- Lightweight synthesis quality signals for grounding, OCI specificity, workload alignment, migration accuracy, recommendation diversity, and citation coverage
- Concise architecture decision reasoning metadata with service choice rationale, workload signals, tradeoffs, rejected alternatives, source chunk IDs, and confidence
- Explicit architecture tradeoff analysis for cost/resilience, performance/complexity, managed/self-managed, latency/multi-region resilience, simplicity/scalability, and flexibility/operational overhead
- Per-recommendation confidence indicators with reasoning basis, supporting chunk IDs, assumptions, and known limitations
- Lightweight architecture consistency validation for conflicting requirements, migration mapping coverage, HA/DR alignment, observability coverage, security coverage, and simple unsupported combination risks
- Deterministic enterprise governance assessment metadata with executive summary, governance annotations, security posture checks, risk classifications, recommendation priorities, architecture comparisons, enterprise review findings, and auditability trace
- Lightweight architecture topology metadata with service nodes, dependencies, deployment topology, HA/DR topology, operational notes, and a simple Mermaid flow for future UI rendering
- Executive experience metadata and UI rendering for executive summaries, decision briefs, implementation sequencing, topology/dependency summaries, architecture comparisons, explainability highlights, and Markdown review export
- Deterministic migration and FinOps optimization metadata with phased migration waves, modernization options, rightsizing/autoscaling/storage lifecycle guidance, workload optimization signals, implementation readiness checks, and cost-vs-resilience comparison reasoning
- Frontend rendering for migration and FinOps optimization summaries, including phased migration steps, FinOps levers, workload-specific optimization signals, and implementation readiness notes
- Expanded confidence sub-signals for service relevance, workload alignment, migration mapping certainty, and citation coverage
- Release snapshot schema and temporal knowledge metadata schema for current-vs-historical scaffolding
- Deterministic release intelligence for release normalization, change-category classification, impacted-service/source/chunk analysis, targeted eval impact reporting, and refresh action recommendations
- OCI-native retrieval migration hooks:
  - optional OCI Generative AI embedding adapter
  - optional Object Storage vector-manifest retrieval
  - optional Oracle AI Vector Search provider with schema SQL, vector upsert, similarity search, metadata filters, health checks, and local fallback
  - retrieval regression reporting for citations, intents, and required service coverage
- Hybrid retrieval path combining provider vector similarity, metadata filters, reranking heuristics, intent/domain heuristics, and intent-critical service coverage
- Separate local OCI release snapshot pipeline
- Knowledge refresh policy scaffolding for release-note watching, candidate snapshot validation, selective reindex, release overlay tagging, eval-gated promotion, historical snapshot retention, version lineage, and rollback-safe updates
- OCI-native release-watch refresh from the backend OCI Compute VM cron path with live release fetch, quick gates, gated promotion, and Object Storage upload; stable-doc refresh remains conservative/candidate-only
- Continuous intelligence status endpoint at `/knowledge/refresh/status`
- OCI-native runtime profiles for `local_dev`, `oci_vm`, and `oke` under `infra/runtime-profiles/`
- Additive operational diagnostics endpoints: `/operations/profile`, `/operations/health`, `/operations/readiness`, `/operations/infrastructure`, and `/operations/analytics`
- Runtime readiness checks for startup paths, provider/dependency configuration, fallback paths, API Gateway readiness, OCI DevOps readiness, and runtime safeguards
- Lightweight operational analytics for retrieval provider usage, synthesis provider usage, fallback events, hallucination findings, governance policy triggers, governance risk trends, architecture comparison usage, recommendation category trends, visualization generation, review artifact generation, runtime degradation events, workload-category usage, confidence distribution, and response latency
- OCI Vault configuration-secret readiness checks, with local environment compatibility for development
- OCI Logging, Audit, Monitoring, Notifications, and Events configuration visibility in operational diagnostics. Audit support is currently surfaced as platform-native OCI Audit posture metadata, not custom audit event export.
- Operational readiness checker under `infra/scripts/operational_readiness_check.py`
- Internal beta readiness gate under `infra/scripts/internal_beta_readiness_check.py` for deployed endpoint, retrieval, operational diagnostics, governance, executive, topology, migration/FinOps, and release-context validation
- Intent-aware orchestration for:
  - product overview
  - architecture
  - migration
  - disaster recovery
  - cost
  - observability
  - AI/ML
  - security
  - modernization
  - SaaS platform
  - analytics
  - release awareness
  - general questions
- Golden prompt regression suite
- Machine-readable golden eval dataset
- Negative and edge-case eval dataset
- Local eval runner with JSON/Markdown reports, failure diagnostics, retrieval-support checks, and stale-guidance checks
- Evaluation intelligence layer with multi-dimensional architecture scoring, hallucination findings, benchmark checks, response-quality analytics, and configurable quality gates
- Enterprise governance eval dataset for security realism, migration governance, FinOps, auditability, operational ownership, and implementation-priority signals
- Enterprise platform maturity eval dataset for topology, executive usability, runtime degradation handling, observability readiness, migration realism, and internal beta readiness signals
- Executive experience eval dataset for executive-summary quality, recommendation readability, architecture visualization usefulness, comparison quality, migration presentation quality, operational guidance clarity, and export-friendly review artifacts
- FinOps and migration optimization eval dataset for phased migration realism, modernization guidance, rightsizing/autoscaling/storage lifecycle guidance, cost-performance tradeoffs, workload optimization, rollback planning, and implementation readiness
- CI workflow for knowledge/release ingestion smoke tests, backend tests, golden/edge evals, and frontend build
- Backend tests covering API, retrieval, and intent routing
- OCI staging deployment with smoke tests, resource visibility checks, and rollback runbooks
- Dual-provider retrieval parity gate comparing `local_json` and `oci_object_storage`
- Config-only staging promotion to `oci_object_storage` with rollback validation
- Evidence-linked recommendations, confidence scoring, decision reasoning metadata, consistency findings, synthesis quality signals, uncertainty flags, and advisory quality metrics
- Config-selectable advisory synthesis with deterministic rollback and an OCI GenAI chat adapter
- Retrieval-grounded GenAI prompt construction with detected intent, mapped OCI services, workload/domain profile, architecture pattern hints, reasoning profile, retrieved OCI chunks, and required response structure
- Optional synthesis debug traces with selected provider, retrieved chunk IDs, grounding prompt sections, approximate input tokens, token usage when available, and fallback reason
- Controlled in-process orchestration pilot with:
  - one in-process supervisor
  - deterministic specialist selection for architecture, migration, HA/DR, cost, and release-awareness advisors
  - shared retrieval evidence across all agents
  - one final synthesis step
  - specialist contribution metadata
  - aggregation decision visibility
  - validation critic findings
  - config-only rollback to `supervised` or `single_pass`
  - `/orchestration/health` observability

The orchestration pilot does not perform autonomous tool use, long-running planning, multi-step memory, or independent agent execution. Those remain deferred until there is enough quality data to justify them.

## GenAI Activation Status

OCI Architecture Studio is evolving from deterministic scaffolding into an OCI GenAI-assisted advisor. The current runtime still defaults to deterministic mode for safety and offline repeatability.

Implemented today:

- `EMBEDDING_PROVIDER=local|oci_genai`
- `EMBEDDING_FALLBACK_ENABLED=true|false`
- `ADVISORY_SYNTHESIS_PROVIDER=deterministic|oci_genai`
- `SYNTHESIS_DEBUG_ENABLED=true|false`
- request-level `synthesis_debug`
- fail-closed OCI GenAI synthesis fallback to deterministic synthesis
- deterministic fallback for OCI GenAI embedding activation or generation failures when fallback is enabled
- deterministic-vs-OCI GenAI comparison reporting under `infra/scripts/genai_synthesis_parity_check.py`

Current limitations:

- The active local corpus is still curated and incomplete, but has expanded to 47 chunks across 44 services and 14 service domains in the current branch.
- OCI GenAI mode requires valid OCI SDK auth, compartment, model IDs, region/endpoint policy access, and parity validation before promotion.
- Live GenAI comparison is skipped when required OCI GenAI environment variables are absent.
- GenAI output is still constrained by retrieved evidence quality; deeper official OCI documentation coverage remains necessary before production-grade breadth.

## Run Locally

### Build the Local OCI RAG Index

Run this once before starting the backend if `knowledge/snapshots/oci-rag-index.json` does not exist:

```bash
python3 knowledge/ingestion/ingest.py
```

The ingestion pipeline reads `knowledge/source_registry.json`, applies source-group defaults, fetches the approved OCI documentation pages when network access is available, preserves document and section context during chunking, enriches chunk metadata, creates deterministic local embeddings by default, and writes a JSON vector index to `knowledge/snapshots/oci-rag-index.json`.

For a fully offline seed index using the registry fallback text:

```bash
python3 knowledge/ingestion/ingest.py --no-fetch
```

Validate corpus health:

```bash
app/backend/.venv/bin/python knowledge/ingestion/corpus_health.py \
  --index knowledge/snapshots/oci-rag-index.json \
  --min-chunks 40
```

### Build the Local OCI Release Snapshot

Release awareness uses a separate source registry and snapshot so current-release checks do not get mixed into the normal architecture knowledge index:

```bash
python3 knowledge/refresh/ingest_releases.py
```

For an offline seed snapshot:

```bash
python3 knowledge/refresh/ingest_releases.py --no-fetch
```

### Run the Knowledge Refresh Policy

Release notes and fast-changing sources are refreshed by policy, not on user queries:

```bash
python3 knowledge/refresh/refresh_policy.py --mode release-watch --no-fetch --quick-gates
```

The policy runner classifies changed release items, runs deterministic impact analysis, maps affected services/domains/change categories to source IDs and chunk IDs, builds candidate snapshots under `knowledge/reports/runs/<run_id>/candidates`, applies release overlay metadata to affected chunks, runs retrieval/eval gates against the candidate paths, and promotes refreshed knowledge only when validation passes.

Report release impact without promoting snapshots:

```bash
python3 infra/scripts/release_impact_report.py \
  --output knowledge/reports/release-impact-report.json
```

Rollback the latest promoted refresh:

```bash
python3 knowledge/refresh/refresh_policy.py --rollback-latest
```

### Backend

```bash
cd app/backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../../.env.example .env
PYTHONPATH=src uvicorn oci_arch_studio_backend.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

Architecture review:

```bash
curl -X POST http://localhost:8000/architecture-review \
  -H "Content-Type: application/json" \
  -d '{"question":"How should I design a highly available web app on OCI?"}'
```

Optional retrieval debug trace:

```bash
curl -X POST http://localhost:8000/architecture-review \
  -H "Content-Type: application/json" \
  -d '{"question":"Migrate CloudWatch and IAM controls for a SaaS platform to OCI.","retrieval_debug":true}'
```

### Frontend

```bash
cd app/frontend
npm install
npm run dev
```

The frontend expects the backend at `http://localhost:8000` by default. Override with:

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## Recommended Next Steps

1. Keep staging on `RETRIEVAL_PROVIDER=oci_object_storage` and monitor retrieval latency, citations, and failure handling.
2. Keep release-watch refresh on the backend OCI VM cron path, monitor `/knowledge/refresh/status`, and keep stable-doc refresh in safe/candidate-only mode until its live cadence is validated.
3. Continue expanding the source registry with Budgets, Audit, Data Guard, and deeper service-specific architecture sources.
4. Replace local hashing embeddings with OCI Generative AI embeddings once provider settings and cost controls are finalized.
5. Keep Oracle AI Vector Search shadow-synced from the promoted Object Storage snapshot before enabling staging active reads.
6. Run refreshed Oracle AI Vector Search dual-run checks against the Object Storage provider before any active-read promotion.
7. Replace fallback release parsing with stronger extraction from official OCI release pages and keep impact-category mappings under review.
8. Use the evaluation-intelligence suite and advisory quality gate before promoting retrieval, synthesis, prompt, or provider changes.
9. Use OCI-native runtime profiles and `/operations/health` before staging changes; enable live OCI connectivity checks only after IAM policies and Vault access are ready.

## Run Evaluations

```bash
app/backend/.venv/bin/python evals/run_golden.py --output-dir evals/reports/golden
app/backend/.venv/bin/python evals/run_golden.py --cases evals/edge-cases.jsonl --output-dir evals/reports/edge-cases
app/backend/.venv/bin/python evals/run_golden.py --cases evals/advisory-quality.jsonl --output-dir evals/reports/advisory-quality
app/backend/.venv/bin/python evals/run_golden.py --cases evals/orchestration-quality.jsonl --output-dir evals/reports/orchestration-quality
app/backend/.venv/bin/python evals/run_golden.py --cases evals/architecture-realism.jsonl --output-dir evals/reports/architecture-realism
app/backend/.venv/bin/python evals/run_golden.py --cases evals/evaluation-intelligence.jsonl --output-dir evals/reports/evaluation-intelligence
app/backend/.venv/bin/python infra/scripts/advisory_quality_gate.py \
  --report evals/reports/evaluation-intelligence/evaluation-intelligence-report.json \
  --min-overall 0.55 \
  --min-oci-specificity 0.45 \
  --min-architecture-completeness 0.45 \
  --min-tradeoff-quality 0.35
app/backend/.venv/bin/python infra/scripts/genai_synthesis_parity_check.py --cases evals/genai-comparison.jsonl --output-dir evals/reports/genai-comparison --allow-skip
app/backend/.venv/bin/python infra/scripts/genai_synthesis_parity_check.py --cases evals/golden-prompts.jsonl --output-dir evals/reports/genai-parity --allow-skip
```

Reports are written to `evals/reports/` and ignored by git.

## Run Retrieval Regression Checks

```bash
app/backend/.venv/bin/python infra/scripts/check_retrieval_health.py --provider local_json
app/backend/.venv/bin/python infra/scripts/check_retrieval_health.py --provider oci_object_storage \
  --oci-region us-ashburn-1 \
  --oci-profile DEFAULT \
  --oci-namespace idsmrn7rvqb6 \
  --oci-vector-bucket oci-architecture-studio-staging-knowledge-snapshots \
  --oci-vector-object-name oci-rag-index.json
app/backend/.venv/bin/python infra/scripts/retrieval_regression_check.py \
  --cases evals/golden-prompts.jsonl \
  --cases evals/edge-cases.jsonl \
  --output-dir evals/reports/retrieval
app/backend/.venv/bin/python infra/scripts/operational_readiness_check.py \
  --api-base-url http://localhost:8000
```

This checks retrieval health, intent alignment, citation availability, top chunks, stale citations, and required OCI service coverage before changing retrieval providers.

## Run Oracle Vector Index Checks

```bash
app/backend/.venv/bin/python infra/scripts/oracle_vector_index.py validate-local-index \
  --index-path knowledge/snapshots/oci-rag-index.json
app/backend/.venv/bin/python infra/scripts/oracle_vector_index.py print-schema
app/backend/.venv/bin/python infra/scripts/vector_retrieval_validation.py \
  --cases evals/vector-retrieval-cases.jsonl \
  --allow-skip \
  --output-dir evals/reports/vector-retrieval
```

`oracle_ai_vector_search` requires `OCI_VECTOR_DB_DSN`, `OCI_VECTOR_DB_USER`, `OCI_VECTOR_DB_PASSWORD`, and the `python-oracledb` package from backend requirements. When `RETRIEVAL_FALLBACK_ENABLED=true`, the backend can fall back to `local_json` if the Oracle vector provider is unavailable.

## Run Retrieval Parity Checks

```bash
app/backend/.venv/bin/python infra/scripts/retrieval_parity_check.py \
  --oci-region us-ashburn-1 \
  --oci-profile DEFAULT \
  --oci-namespace idsmrn7rvqb6 \
  --oci-vector-bucket oci-architecture-studio-staging-knowledge-snapshots \
  --oci-vector-object-name oci-rag-index.json \
  --output-dir evals/reports/retrieval-parity
```

Use this before promoting or rolling back retrieval provider config.

## OCI Deployment

The first OCI deployment path keeps one codebase and uses environment-specific configuration:

- local for development and testing
- OCI staging for the first cloud-hosted slice
- OCI demo/prod for later promoted environments

Start with the execution runbook:

```bash
docs/oci-deployment-execution.md
```

The scaffold includes Terraform environments, backend VM deployment, frontend Object Storage upload, snapshot upload, OCI access checks, and deployment smoke tests.

Current staging defaults:

- region: `us-ashburn-1`
- backend shape: `VM.Standard.E5.Flex`
- backend size: `8 OCPUs`, `128 GB`
- backend OS image family: Oracle Linux 9
- notifications: `baba.shaik@oracle.com`
- local SSH key path: `~/.ssh/oci-architecture-studio-staging`

The real staging `terraform.tfvars`, saved plan files, and SSH keys are intentionally ignored by git.

Validate deployment inputs with:

```bash
python3 infra/scripts/validate_deployment_config.py \
  --tfvars infra/terraform/envs/staging/terraform.tfvars \
  --profile DEFAULT
```

## Rerun After Changes

```bash
app/backend/.venv/bin/python evals/run_golden.py --output-dir evals/reports/golden
app/backend/.venv/bin/python evals/run_golden.py --cases evals/edge-cases.jsonl --output-dir evals/reports/edge-cases
app/backend/.venv/bin/python evals/run_golden.py --cases evals/advisory-quality.jsonl --output-dir evals/reports/advisory-quality
app/backend/.venv/bin/python evals/run_golden.py --cases evals/orchestration-quality.jsonl --output-dir evals/reports/orchestration-quality
app/backend/.venv/bin/python evals/run_golden.py --cases evals/architecture-realism.jsonl --output-dir evals/reports/architecture-realism
app/backend/.venv/bin/python evals/run_golden.py --cases evals/evaluation-intelligence.jsonl --output-dir evals/reports/evaluation-intelligence
app/backend/.venv/bin/python infra/scripts/advisory_quality_gate.py --report evals/reports/evaluation-intelligence/evaluation-intelligence-report.json --min-overall 0.55 --min-oci-specificity 0.45 --min-architecture-completeness 0.45 --min-tradeoff-quality 0.35
app/backend/.venv/bin/python infra/scripts/retrieval_regression_check.py --cases evals/golden-prompts.jsonl --cases evals/edge-cases.jsonl --output-dir evals/reports/retrieval
app/backend/.venv/bin/python infra/scripts/retrieval_parity_check.py --oci-region us-ashburn-1 --oci-profile DEFAULT --oci-namespace idsmrn7rvqb6 --oci-vector-bucket oci-architecture-studio-staging-knowledge-snapshots --oci-vector-object-name oci-rag-index.json --output-dir evals/reports/retrieval-parity
app/backend/.venv/bin/python knowledge/ingestion/ingest.py --no-fetch
app/backend/.venv/bin/python knowledge/refresh/ingest_releases.py --no-fetch
app/backend/.venv/bin/python infra/scripts/release_impact_report.py --output knowledge/reports/release-impact-report.json
app/backend/.venv/bin/python knowledge/refresh/refresh_policy.py --mode release-watch --no-fetch --quick-gates
cd app/backend && PYTHONPATH=src .venv/bin/pytest -q
cd ../frontend && npm run build
```

## Project Status

Latest full validation: 2026-05-15.

- Local backend tests: `121 passed`
- Golden evals: `18 passed, 0 failed`
- Edge-case evals: `8 passed, 0 failed`
- Advisory-quality evals: `5 passed, 0 failed`
- Controlled orchestration evals: `5 passed, 0 failed`
- Architecture-realism evals: `4 passed, 0 failed`
- Evaluation-intelligence evals: `9 passed, 0 failed`
- Enterprise-governance evals: `5 passed, 0 failed`
- Enterprise-platform-maturity evals: `4 passed, 0 failed`
- Runtime-production-readiness evals: `3 passed, 0 failed`
- Executive-experience evals: `3 passed, 0 failed`
- FinOps-migration-optimization evals: `4 passed, 0 failed`
- Advisory quality gate: passed with MVP thresholds
- Internal beta readiness gate: passed locally and against OCI staging
- Operational readiness check: passed locally and against staging; OCI DevOps remains a readiness warning until configured
- Retrieval regression: `26 passed, 0 failed` for the refreshed Object Storage path
- Retrieval health: passed for local `local_json` and staging `oci_object_storage` with 47 chunks
- Oracle AI Vector Search shadow health: passed with 47 chunks, valid table/index, 44 services, and 14 service domains
- Oracle vector shadow validation: passed 26 cases with average top-chunk overlap `0.977`
- Corpus health: passed for 47 chunks, 44 services, and 14 service domains
- Knowledge ingestion: `47 chunks`
- Release ingestion: `12 live release items` in the latest gated release-watch activation
- Release impact report: passed with deterministic classification, impacted sources/chunks, targeted eval cases, refresh actions, and unresolved-risk reporting
- Knowledge refresh policy: backend VM release-watch path passed with live fetch, quick gates, gated promotion, and Object Storage upload; stable-doc refresh remains safe/candidate-only
- Frontend build: passed
- Terraform fmt/validate: passed for `dev`, `test`, and `staging`
- OCI staging smoke: passed for backend, frontend, OCI SDK, retrieval, and resource visibility
- Staging enterprise governance smoke: passed, including `enterprise_governance` response metadata and governance analytics counters
- Dual-provider retrieval parity: passed, `14/14`, comparing `local_json` with `oci_object_storage`
- Staging retrieval promotion: passed, active provider is `oci_object_storage`
- Rollback validation: passed, `local_json` can be restored through config only and `oci_object_storage` was restored after the rollback test
- Deployment synchronization: passed, staging exposes current repo endpoints including `/orchestration/health` and `/knowledge/refresh/status`
- GenAI activation readiness: parity checker implemented; live OCI GenAI comparison is gated on `OCI_GENAI_COMPARTMENT_ID` and `OCI_GENAI_CHAT_MODEL_ID`
- Live post-promotion scenario checks: passed for architecture, migration, HA/DR, cost, and release-awareness prompts

See `docs/status.md` for the current completed work, pending work, and known limitations.

See `docs/internal-beta-readiness-summary.md` for the internal beta gap assessment, accepted limitations, validation baseline, and milestone tagging guidance.

See `docs/architecture-diagrams.md` for presentation-friendly diagrams covering current staging, dual-provider retrieval parity, target OCI-native retrieval, release-awareness, and operational control points.

See `docs/two-week-plan.md` for the active two-week execution plan.

See `docs/demo-readiness.md` for the demo checklist, recommended demo prompts, Sprint 2 backlog, and closeout notes.

See `docs/phase-2-architecture.md` for the productionization architecture and Sprint 2 roadmap.

See `docs/oci-deployment-architecture.md` and `infra/terraform/` for the first OCI-native deployment architecture and Terraform scaffold.

See `docs/oci-landing-zone-runbook.md` for the first OCI landing-zone deployment workflow and smoke tests.

See `docs/oci-deployment-execution.md` for the command-by-command staging deployment sequence.

See `docs/pre-migration-readiness-report.md` for the OCI-native retrieval pre-migration validation, stability review, and go/no-go decision.

See `docs/oci-native-retrieval-migration.md` for the OCI-native retrieval architecture, phased migration guide, validation strategy, observability plan, and rollback path.

See `docs/oci-native-retrieval-runbook.md` for provider modes, validation gates, rollback steps, and troubleshooting for Sprint 2 retrieval migration.

See `docs/post-migration-readiness-report.md` for the full post-migration validation, retrieval quality assessment, OCI platform validation, risks, and go/no-go decision.

See `docs/retrieval-parity-validation-report.md` for dual-provider parity results, promotion criteria, config switching, rollback validation, and the go/no-go decision for `oci_object_storage` staging promotion.

See `docs/retrieval-provider-promotion-report.md` for the completed staging promotion, post-promotion validation results, rollback proof, and the next Oracle AI Vector Search boundary.

See `docs/advisory-intelligence.md` for evidence-linked recommendations, confidence scoring, citation enforcement, enterprise-governance metadata, uncertainty handling, and advisory-quality observability.

See `docs/genai-advisory-hardening.md` for GenAI synthesis configuration, fail-closed fallback behavior, citation enforcement, confidence scoring, eval strategy, and rollback guidance.

See `docs/post-stabilization-architecture-review.md` for the factual current-state architecture after repo/staging synchronization, active providers, GenAI readiness, validation summary, and next milestone.

See `docs/terraform-plan-review.md` for the first staging Terraform planning workflow, plan review, apply readiness criteria, and post-apply smoke-test plan.

See `docs/oci-staging-deployment-report.md` for the first OCI staging apply result, deployment validation, smoke-test output, and next hardening steps.

See `docs/baseline-freeze.md` and `docs/operational-runbook.md` for the frozen working baseline, post-deploy verification checklist, regression guardrails, and day-to-day staging operations.
