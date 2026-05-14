# OCI Architecture Studio

OCI Architecture Studio is an enterprise AI platform for OCI architecture guidance, migration advisory, cost optimization, and release-aware OCI knowledge synchronization.

The project is monorepo-first, RAG-first, modular, and evaluation-driven. Prompts, retrieval code, evals, and application code are treated as first-class assets from the start.

## First Vertical Slice

The initial working flow is intentionally simple:

1. User asks an OCI architecture question in the React UI.
2. The frontend calls the FastAPI backend.
3. The backend invokes a retrieval placeholder.
4. A prompt orchestration placeholder produces a structured response.
5. The UI renders the recommendation, assumptions, risks, citations, and next steps.

Full RAG, LangGraph, advanced memory, and production ingestion are intentionally out of scope for this scaffold.

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

## Run Locally

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

1. Replace the retrieval placeholder with a tiny curated OCI document index.
2. Add source-grounded citation requirements to the first prompt template.
3. Add eval cases for architecture quality, unsupported claims, and missing assumptions.
4. Add CI for backend tests, frontend build, linting, and prompt/eval validation.
5. Add a deployment target only after the local vertical slice is stable.
