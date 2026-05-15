# OCI Architecture Studio

OCI Architecture Studio is an enterprise AI platform for OCI architecture guidance, migration advisory, cost optimization, and release-aware OCI knowledge synchronization.

The project is monorepo-first, RAG-first, modular, and evaluation-driven. Prompts, retrieval code, evals, and application code are treated as first-class assets from the start.

## Current Vertical Slice

The initial working flow is intentionally simple:

1. User asks an OCI architecture question in the React UI.
2. The frontend calls the FastAPI backend.
3. The backend classifies the request intent.
4. The backend retrieves relevant chunks from a small local OCI RAG index.
5. Intent-aware orchestration shapes a structured response from that context.
6. The UI renders intent, prompt template, recommendations, assumptions, risks, citations, and next steps.

LangGraph, advanced memory, production vector storage, full LLM synthesis, and production release intelligence are intentionally out of scope for this scaffold.

## Repository Layout

```text
docs/                 Product, roadmap, sprint, and architecture docs
app/backend/          Python 3.12 FastAPI backend
app/frontend/         React + Vite frontend
knowledge/            Future ingestion, classification, refresh, and snapshots
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

1. Expand the source registry with dedicated WAF, Vault, Cloud Guard, Logging, Monitoring, and Budgets sources.
2. Replace fallback release parsing with stronger extraction from official OCI release pages.
3. Improve retrieval-support checks beyond required service terms.
4. Add release-impact evals that assert service/domain/impact classification.
5. Replace local hashing embeddings with the selected production embedding provider when the corpus grows.

## Run Evaluations

```bash
app/backend/.venv/bin/python evals/run_golden.py --output-dir evals/reports/golden
app/backend/.venv/bin/python evals/run_golden.py --cases evals/edge-cases.jsonl --output-dir evals/reports/edge-cases
```

Reports are written to `evals/reports/` and ignored by git.

## Run Retrieval Regression Checks

```bash
app/backend/.venv/bin/python infra/scripts/check_retrieval_health.py --provider local_json
app/backend/.venv/bin/python infra/scripts/retrieval_regression_check.py \
  --cases evals/golden-prompts.jsonl \
  --cases evals/edge-cases.jsonl \
  --output-dir evals/reports/retrieval
```

This checks retrieval health, intent alignment, citation availability, top chunks, stale citations, and required OCI service coverage before changing retrieval providers.

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
app/backend/.venv/bin/python infra/scripts/retrieval_regression_check.py --cases evals/golden-prompts.jsonl --cases evals/edge-cases.jsonl --output-dir evals/reports/retrieval
app/backend/.venv/bin/python knowledge/ingestion/ingest.py --no-fetch
app/backend/.venv/bin/python knowledge/refresh/ingest_releases.py --no-fetch
cd app/backend && PYTHONPATH=src .venv/bin/pytest -q
cd ../frontend && npm run build
```

## Project Status

Latest full validation: 2026-05-15.

- Local backend tests: `30 passed`
- Golden evals: `6 passed, 0 failed`
- Edge-case evals: `8 passed, 0 failed`
- Retrieval regression: `14 passed, 0 failed`
- Knowledge ingestion: `13 chunks`
- Release ingestion: `3 release items`
- Frontend build: passed
- Terraform fmt/validate: passed for `dev`, `test`, and `staging`
- OCI staging smoke: passed for backend, frontend, OCI SDK, retrieval, and resource visibility
- Post-migration readiness: passed for continued Sprint 2 development; staging still uses `local_json` as the active read provider until OCI-native parity is proven
- Dual-provider retrieval parity: passed, `14/14`, comparing `local_json` with `oci_object_storage`

See `docs/status.md` for the current completed work, pending work, and known limitations.

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

See `docs/terraform-plan-review.md` for the first staging Terraform planning workflow, plan review, apply readiness criteria, and post-apply smoke-test plan.

See `docs/oci-staging-deployment-report.md` for the first OCI staging apply result, deployment validation, smoke-test output, and next hardening steps.

See `docs/baseline-freeze.md` and `docs/operational-runbook.md` for the frozen working baseline, post-deploy verification checklist, regression guardrails, and day-to-day staging operations.
