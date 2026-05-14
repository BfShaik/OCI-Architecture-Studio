#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <backend-host> [ssh-user] [ssh-key-path]" >&2
  exit 1
}

if [[ $# -lt 1 ]]; then
  usage
fi

BACKEND_HOST="$1"
SSH_USER="${2:-opc}"
SSH_KEY="${3:-}"
REMOTE_DIR="/opt/oci-architecture-studio"
SERVICE_NAME="oci-architecture-studio"

cd "$(dirname "$0")/../.."

SSH_OPTS=()
if [[ -n "$SSH_KEY" ]]; then
  SSH_OPTS=(-i "$SSH_KEY")
fi

echo "Syncing application code to ${SSH_USER}@${BACKEND_HOST}:${REMOTE_DIR}"
ssh "${SSH_OPTS[@]}" "${SSH_USER}@${BACKEND_HOST}" "sudo mkdir -p ${REMOTE_DIR} && sudo chown ${SSH_USER}:${SSH_USER} ${REMOTE_DIR}"

rsync -az --delete \
  --exclude ".git" \
  --exclude ".terraform" \
  --exclude "node_modules" \
  --exclude ".venv" \
  --exclude "dist" \
  --exclude "__pycache__" \
  --exclude ".pytest_cache" \
  --exclude "knowledge/snapshots/*.json" \
  ./ "${SSH_USER}@${BACKEND_HOST}:${REMOTE_DIR}/"

ssh "${SSH_OPTS[@]}" "${SSH_USER}@${BACKEND_HOST}" "bash -s" <<'REMOTE'
set -euo pipefail
REMOTE_DIR="/opt/oci-architecture-studio"
SERVICE_NAME="oci-architecture-studio"
cd "$REMOTE_DIR"

python3 -m venv app/backend/.venv
app/backend/.venv/bin/python -m pip install --upgrade pip
app/backend/.venv/bin/pip install -r app/backend/requirements.txt
app/backend/.venv/bin/python knowledge/ingestion/ingest.py --no-fetch
app/backend/.venv/bin/python knowledge/refresh/ingest_releases.py --no-fetch

if [[ ! -f /etc/oci-architecture-studio.env ]]; then
  sudo tee /etc/oci-architecture-studio.env >/dev/null <<'ENVFILE'
APP_ENV=staging
LOG_LEVEL=INFO
BACKEND_CORS_ORIGINS=*
KNOWLEDGE_INDEX_PATH=/opt/oci-architecture-studio/knowledge/snapshots/oci-rag-index.json
RELEASE_SNAPSHOT_PATH=/opt/oci-architecture-studio/knowledge/snapshots/oci-release-snapshot.json
ENVFILE
fi

sudo tee /etc/systemd/system/${SERVICE_NAME}.service >/dev/null <<'SERVICE'
[Unit]
Description=OCI Architecture Studio FastAPI backend
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/oci-architecture-studio/app/backend
EnvironmentFile=/etc/oci-architecture-studio.env
Environment=PYTHONPATH=src
ExecStart=/opt/oci-architecture-studio/app/backend/.venv/bin/uvicorn oci_arch_studio_backend.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"
sudo systemctl status "${SERVICE_NAME}" --no-pager
REMOTE

echo "Backend deployment complete. Verify with:"
echo "python3 infra/scripts/smoke_oci_deployment.py --api-base-url http://${BACKEND_HOST}:8000"
