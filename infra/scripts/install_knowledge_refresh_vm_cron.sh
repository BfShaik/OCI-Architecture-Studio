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
REMOTE_DIR="${REMOTE_DIR:-/opt/oci-architecture-studio}"
CRON_FILE="/etc/cron.d/oci-architecture-studio-knowledge-refresh"

cd "$(dirname "$0")/../.."

SSH_OPTS=()
RSYNC_SSH="ssh"
if [[ -n "${SSH_KEY}" ]]; then
  SSH_OPTS=(-i "${SSH_KEY}")
  RSYNC_SSH="ssh -i ${SSH_KEY}"
fi

rsync -az -e "${RSYNC_SSH}" \
  infra/scripts/run_knowledge_refresh_vm.sh \
  "${SSH_USER}@${BACKEND_HOST}:${REMOTE_DIR}/infra/scripts/run_knowledge_refresh_vm.sh"

ssh "${SSH_OPTS[@]}" "${SSH_USER}@${BACKEND_HOST}" "REMOTE_DIR='${REMOTE_DIR}' CRON_FILE='${CRON_FILE}' bash -s" <<'REMOTE'
set -euo pipefail

sudo chmod 0755 "${REMOTE_DIR}/infra/scripts/run_knowledge_refresh_vm.sh"
sudo mkdir -p /var/lib/oci-architecture-studio/knowledge-refresh/reports /var/log/oci-architecture-studio
sudo chown -R opc:opc /var/lib/oci-architecture-studio /var/log/oci-architecture-studio

sudo tee "${CRON_FILE}" >/dev/null <<CRON
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Safe release-watch refresh: candidate-only, no fetch, no upload.
17 */6 * * * opc VM_REFRESH_MODE=release-watch VM_REFRESH_NO_FETCH=true VM_REFRESH_QUICK_GATES=true VM_REFRESH_CANDIDATE_ONLY=true VM_REFRESH_UPLOAD=false ${REMOTE_DIR}/infra/scripts/run_knowledge_refresh_vm.sh

# Safe stable-docs refresh stays slower and conservative.
23 2 * * 0 opc VM_REFRESH_MODE=stable-docs VM_REFRESH_NO_FETCH=true VM_REFRESH_QUICK_GATES=true VM_REFRESH_CANDIDATE_ONLY=true VM_REFRESH_UPLOAD=false ${REMOTE_DIR}/infra/scripts/run_knowledge_refresh_vm.sh
CRON

sudo chmod 0644 "${CRON_FILE}"
sudo crontab -u opc -l >/tmp/oci-architecture-studio-opc-crontab.txt 2>/dev/null || true
sudo systemctl reload crond 2>/dev/null || sudo systemctl reload cron 2>/dev/null || true
cat "${CRON_FILE}"
REMOTE
