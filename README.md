# OCI Architecture Studio

OCI Architecture Studio is an enterprise AI platform for OCI architecture guidance, migration advisory, cost optimization, and release-aware OCI knowledge synchronization.

The project is monorepo-first, RAG-first, modular, and evaluation-driven. Prompts, retrieval code, evals, and application code are treated as first-class assets from the start.

## First Vertical Slice

The initial working flow is intentionally simple:

1. User asks an OCI architecture question in the React UI.
2. The frontend calls the FastAPI backend.
3. The backend retrieves relevant chunks from a small local OCI RAG index.
4. A prompt orchestration placeholder shapes a structured response from that context.
5. The UI renders the recommendation, assumptions, risks, citations, and next steps.

LangGraph, advanced memory, release intelligence, and production ingestion are intentionally out of scope for this scaffold.

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

1. Expand the source registry with approved OCI architecture and service documents.
2. Add source-grounded citation requirements to the first prompt template.
3. Add eval cases for architecture quality, unsupported claims, and missing assumptions.
4. Add CI for ingestion smoke tests, backend tests, frontend build, linting, and prompt/eval validation.
5. Replace local hashing embeddings with the selected production embedding provider when the corpus grows.

## Project Status

See `docs/status.md` for the current completed work, pending work, and known limitations.

See `docs/two-week-plan.md` for the active two-week execution plan.
