#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/opt/oci-architecture-studio}"
ENV_FILE="${ENV_FILE:-/etc/oci-architecture-studio.env}"
PYTHON_BIN="${PYTHON_BIN:-${REPO_DIR}/app/backend/.venv/bin/python}"
MODE="${VM_REFRESH_MODE:-release-watch}"
REPORT_BASE="${VM_REFRESH_REPORT_BASE:-/var/lib/oci-architecture-studio/knowledge-refresh/reports}"
LOG_DIR="${VM_REFRESH_LOG_DIR:-/var/log/oci-architecture-studio}"
LOCK_FILE="${VM_REFRESH_LOCK_FILE:-/var/lib/oci-architecture-studio/knowledge-refresh/refresh.lock}"
STATUS_PATH="${VM_REFRESH_STATUS_PATH:-${REPO_DIR}/knowledge/reports/knowledge-refresh-status.json}"
REPORT_PATH="${VM_REFRESH_REPORT_PATH:-${REPO_DIR}/knowledge/reports/knowledge-refresh-report.json}"

NO_FETCH="${VM_REFRESH_NO_FETCH:-true}"
QUICK_GATES="${VM_REFRESH_QUICK_GATES:-true}"
CANDIDATE_ONLY="${VM_REFRESH_CANDIDATE_ONLY:-true}"
UPLOAD="${VM_REFRESH_UPLOAD:-false}"
FORCE="${VM_REFRESH_FORCE:-false}"
OCI_AUTH_MODE="${OCI_AUTH_MODE:-instance_principal}"
OCI_NAMESPACE="${OCI_OBJECT_STORAGE_NAMESPACE:-}"
OCI_UPLOAD_BUCKET="${SNAPSHOTS_BUCKET:-${OCI_VECTOR_BUCKET:-}}"
OCI_UPLOAD_OBJECT="${OCI_VECTOR_OBJECT_NAME:-oci-rag-index.json}"

if [[ -r "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

mkdir -p "${REPORT_BASE}" "${LOG_DIR}" "$(dirname "${LOCK_FILE}")"

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-${MODE}"
REPORT_DIR="${REPORT_BASE}/${RUN_ID}"
LOG_FILE="${LOG_DIR}/knowledge-refresh-${MODE}.log"

command=(
  "${PYTHON_BIN}"
  "${REPO_DIR}/knowledge/refresh/refresh_policy.py"
  --mode "${MODE}"
  --oci-auth-mode "${OCI_AUTH_MODE}"
  --report-dir "${REPORT_DIR}"
)

if [[ "${NO_FETCH}" == "true" ]]; then
  command+=(--no-fetch)
fi
if [[ "${QUICK_GATES}" == "true" ]]; then
  command+=(--quick-gates)
fi
if [[ "${CANDIDATE_ONLY}" == "true" ]]; then
  command+=(--candidate-only)
fi
if [[ "${FORCE}" == "true" ]]; then
  command+=(--force)
fi
if [[ "${UPLOAD}" == "true" ]]; then
  if [[ -z "${OCI_NAMESPACE}" || -z "${OCI_UPLOAD_BUCKET}" ]]; then
    echo "Upload requested but OCI namespace or upload bucket is missing." >&2
    exit 2
  fi
  command+=(
    --oci-namespace "${OCI_NAMESPACE}"
    --oci-upload-bucket "${OCI_UPLOAD_BUCKET}"
    --oci-upload-object "${OCI_UPLOAD_OBJECT}"
  )
fi

{
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] starting knowledge refresh"
  echo "mode=${MODE} no_fetch=${NO_FETCH} quick_gates=${QUICK_GATES} candidate_only=${CANDIDATE_ONLY} upload=${UPLOAD}"
  echo "report_dir=${REPORT_DIR}"
  printf 'command='
  printf '%q ' "${command[@]}"
  echo
} >>"${LOG_FILE}"

(
  flock -n 9 || {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] skipped: refresh already running" >>"${LOG_FILE}"
    exit 0
  }
  cd "${REPO_DIR}"
  "${command[@]}" >>"${LOG_FILE}" 2>&1
) 9>"${LOCK_FILE}"

mkdir -p "$(dirname "${STATUS_PATH}")" "$(dirname "${REPORT_PATH}")"
if [[ -f "${REPORT_DIR}/knowledge-refresh-status.json" ]]; then
  cp "${REPORT_DIR}/knowledge-refresh-status.json" "${STATUS_PATH}"
fi
if [[ -f "${REPORT_DIR}/knowledge-refresh-report.json" ]]; then
  cp "${REPORT_DIR}/knowledge-refresh-report.json" "${REPORT_PATH}"
fi

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] completed knowledge refresh" >>"${LOG_FILE}"
