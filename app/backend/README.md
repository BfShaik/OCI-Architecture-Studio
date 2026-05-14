# Backend

FastAPI backend for OCI Architecture Studio.

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

## Endpoints

- `GET /health`
- `POST /architecture-review`
