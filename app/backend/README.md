# Backend

FastAPI backend for OCI Architecture Studio.

The backend is config-driven:

| Setting | Local default | Staging value |
| --- | --- | --- |
| `ADVISORY_SYNTHESIS_PROVIDER` | `deterministic` | `oci_genai` |
| `RETRIEVAL_PROVIDER` | `local_json` | `oracle_ai_vector_search` |
| `EMBEDDING_PROVIDER` | `local` | `oci_genai` |

The code reads these values in `src/oci_arch_studio_backend/core/config.py`.

## Run

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src uvicorn oci_arch_studio_backend.main:app --reload --port 8000
```

Build the local RAG index from the repository root before starting the API:

```bash
python3 knowledge/ingestion/ingest.py
```

## Main Endpoints

- `GET /health`
- `GET /retrieval/health`
- `GET /operations/health`
- `GET /operations/readiness`
- `POST /architecture-review`
- `GET /review-history`
