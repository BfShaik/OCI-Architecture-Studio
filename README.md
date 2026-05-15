# OCI Architecture Studio

OCI Architecture Studio is an enterprise AI platform for OCI architecture guidance, migration advisory, cost optimization, and release-aware OCI knowledge synchronization.

The project is monorepo-first, RAG-first, modular, and evaluation-driven. Prompts, retrieval code, evals, and application code are treated as first-class assets from the start.

## Current Working Flow

OCI Architecture Studio currently supports a validated advisory flow in local development and OCI staging:

1. User asks an OCI architecture, migration, DR, cost, security, or release-awareness question in the React UI.
2. The frontend calls the FastAPI backend.
3. The backend classifies the request intent and applies the matching orchestration profile.
4. Retrieval runs through a config-selected provider.
5. The active staging provider is `oci_object_storage`, reading the validated vector manifest from OCI Object Storage.
6. `local_json` remains the tested config-only rollback provider.
7. The controlled multi-agent pilot selects bounded specialist advisors, shares the same retrieved evidence across them, and runs a validation critic over evidence support, citations, freshness, and unsupported-claim risk.
8. One final synthesis step generates the advisory response through the configured provider with deterministic rollback available.
9. The continuous intelligence pipeline refreshes OCI release knowledge on schedule, validates candidate snapshots, and promotes them only after gates pass.
10. The UI renders intent, prompt template, active agents, specialist contributions, aggregation decision, critic findings, confidence, recommendations, assumptions, risks, citations, and next steps.

LangGraph, advanced memory, autonomous agent swarms, and Oracle AI Vector Search active reads are intentionally deferred until the controlled pilot and the next vector-search parity gate are ready.

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
- Deterministic local embeddings for development
- JSON vector index for local retrieval
- Citation-friendly chunk metadata with service, domain, trust, intent tags, and freshness score
- OCI-native retrieval migration hooks:
  - optional OCI Generative AI embedding adapter
  - optional Object Storage vector-manifest retrieval
  - guarded Oracle AI Vector Search adapter boundary
  - retrieval regression reporting for citations, intents, and required service coverage
- Separate local OCI release snapshot pipeline
- Knowledge refresh policy for scheduled release-note watching, candidate snapshot validation, selective reindex, eval-gated promotion, version lineage, and rollback-safe updates
- Optional OCI-native recurring refresh scaffold with OCI Functions and OCI Resource Scheduler
- Continuous intelligence status endpoint at `/knowledge/refresh/status`
- Intent-aware orchestration for:
  - product overview
  - architecture
  - migration
  - disaster recovery
  - cost
  - security
  - release awareness
  - general questions
- Golden prompt regression suite
- Machine-readable golden eval dataset
- Negative and edge-case eval dataset
- Local eval runner with JSON/Markdown reports, failure diagnostics, retrieval-support checks, and stale-guidance checks
- CI workflow for knowledge/release ingestion smoke tests, backend tests, golden/edge evals, and frontend build
- Backend tests covering API, retrieval, and intent routing
- OCI staging deployment with smoke tests, resource visibility checks, and rollback runbooks
- Dual-provider retrieval parity gate comparing `local_json` and `oci_object_storage`
- Config-only staging promotion to `oci_object_storage` with rollback validation
- Evidence-linked recommendations, confidence scoring, uncertainty flags, and advisory quality metrics
- Config-selectable advisory synthesis with deterministic rollback and an OCI GenAI chat adapter
- Controlled multi-agent pilot with:
  - one in-process supervisor
  - deterministic specialist selection for architecture, migration, HA/DR, cost, and release-awareness advisors
  - shared retrieval evidence across all agents
  - one final synthesis step
  - specialist contribution metadata
  - aggregation decision visibility
  - validation critic findings
  - config-only rollback to `supervised` or `single_pass`
  - `/orchestration/health` observability

## Run Locally

### Build the Local OCI RAG Index

Run this once before starting the backend if `knowledge/snapshots/oci-rag-index.json` does not exist:

```bash
python3 knowledge/ingestion/ingest.py
```

The ingestion pipeline reads `knowledge/source_registry.json`, fetches a small approved set of OCI documentation pages when network access is available, chunks the text, creates deterministic local embeddings, and writes a JSON vector index to `knowledge/snapshots/oci-rag-index.json`.

For a fully offline seed index using the registry fallback text:

```bash
python3 knowledge/ingestion/ingest.py --no-fetch
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

The policy runner classifies changed release items, maps them to affected source IDs, builds candidate snapshots under `knowledge/reports/runs/<run_id>/candidates`, runs retrieval/eval gates against the candidate paths, and promotes refreshed knowledge only when validation passes.

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
2. Run the scheduled refresh function in staging with candidate-first promotion and watch `/knowledge/refresh/status`.
3. Continue expanding the source registry with Budgets, Audit, Data Guard, and deeper service-specific architecture sources.
4. Replace local hashing embeddings with OCI Generative AI embeddings once provider settings and cost controls are finalized.
5. Validate Oracle AI Vector Search schema/query parity before enabling active reads.
6. Add Oracle AI Vector Search dual-run checks against the Object Storage provider before any active-read promotion.
7. Replace fallback release parsing with stronger extraction from official OCI release pages.

## Run Evaluations

```bash
app/backend/.venv/bin/python evals/run_golden.py --output-dir evals/reports/golden
app/backend/.venv/bin/python evals/run_golden.py --cases evals/edge-cases.jsonl --output-dir evals/reports/edge-cases
app/backend/.venv/bin/python evals/run_golden.py --cases evals/advisory-quality.jsonl --output-dir evals/reports/advisory-quality
app/backend/.venv/bin/python evals/run_golden.py --cases evals/orchestration-quality.jsonl --output-dir evals/reports/orchestration-quality
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
```

This checks retrieval health, intent alignment, citation availability, top chunks, stale citations, and required OCI service coverage before changing retrieval providers.

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
app/backend/.venv/bin/python infra/scripts/retrieval_regression_check.py --cases evals/golden-prompts.jsonl --cases evals/edge-cases.jsonl --output-dir evals/reports/retrieval
app/backend/.venv/bin/python infra/scripts/retrieval_parity_check.py --oci-region us-ashburn-1 --oci-profile DEFAULT --oci-namespace idsmrn7rvqb6 --oci-vector-bucket oci-architecture-studio-staging-knowledge-snapshots --oci-vector-object-name oci-rag-index.json --output-dir evals/reports/retrieval-parity
app/backend/.venv/bin/python knowledge/ingestion/ingest.py --no-fetch
app/backend/.venv/bin/python knowledge/refresh/ingest_releases.py --no-fetch
app/backend/.venv/bin/python knowledge/refresh/refresh_policy.py --mode release-watch --no-fetch --quick-gates
cd app/backend && PYTHONPATH=src .venv/bin/pytest -q
cd ../frontend && npm run build
```

## Project Status

Latest full validation: 2026-05-15.

- Local backend tests: `50 passed`
- Golden evals: `6 passed, 0 failed`
- Edge-case evals: `8 passed, 0 failed`
- Advisory-quality evals: `5 passed, 0 failed`
- Controlled orchestration evals: `5 passed, 0 failed`
- Retrieval regression: `14 passed, 0 failed`
- Knowledge ingestion: `21 chunks`
- Release ingestion: `3 release items`
- Knowledge refresh policy smoke: passed
- Frontend build: passed
- Terraform fmt/validate: passed for `dev`, `test`, and `staging`
- OCI staging smoke: passed for backend, frontend, OCI SDK, retrieval, and resource visibility
- Dual-provider retrieval parity: passed, `14/14`, comparing `local_json` with `oci_object_storage`
- Staging retrieval promotion: passed, active provider is `oci_object_storage`
- Rollback validation: passed, `local_json` can be restored through config only and `oci_object_storage` was restored after the rollback test
- Deployment synchronization: passed, staging exposes current repo endpoints including `/orchestration/health` and `/knowledge/refresh/status`
- GenAI activation readiness: parity checker implemented; live OCI GenAI comparison is gated on `OCI_GENAI_COMPARTMENT_ID` and `OCI_GENAI_CHAT_MODEL_ID`
- Live post-promotion scenario checks: passed for architecture, migration, HA/DR, cost, and release-awareness prompts

See `docs/status.md` for the current completed work, pending work, and known limitations.

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

See `docs/advisory-intelligence.md` for evidence-linked recommendations, confidence scoring, citation enforcement, uncertainty handling, and advisory-quality observability.

See `docs/genai-advisory-hardening.md` for GenAI synthesis configuration, fail-closed fallback behavior, citation enforcement, confidence scoring, eval strategy, and rollback guidance.

See `docs/post-stabilization-architecture-review.md` for the factual current-state architecture after repo/staging synchronization, active providers, GenAI readiness, validation summary, and next milestone.

See `docs/terraform-plan-review.md` for the first staging Terraform planning workflow, plan review, apply readiness criteria, and post-apply smoke-test plan.

See `docs/oci-staging-deployment-report.md` for the first OCI staging apply result, deployment validation, smoke-test output, and next hardening steps.

See `docs/baseline-freeze.md` and `docs/operational-runbook.md` for the frozen working baseline, post-deploy verification checklist, regression guardrails, and day-to-day staging operations.
