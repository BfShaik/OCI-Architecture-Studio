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

1. Convert the golden prompts into a structured machine-readable eval file.
2. Add a local eval runner for golden prompts.
3. Improve ingestion cleanup and source metadata.
4. Expand the source registry with WAF/CDN, Object Storage, Vault, Cloud Guard, Logging, Monitoring, and Budgets sources.
5. Add CI for ingestion smoke tests, backend tests, frontend build, linting, and prompt/eval validation.
6. Replace local hashing embeddings with the selected production embedding provider when the corpus grows.

## Project Status

See `docs/status.md` for the current completed work, pending work, and known limitations.

See `docs/two-week-plan.md` for the active two-week execution plan.
