#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <namespace> <bucket-name>" >&2
  exit 1
fi

NAMESPACE="$1"
BUCKET="$2"
OCI_CLI_PROFILE="${OCI_CLI_PROFILE:-DEFAULT}"
REBUILD_SNAPSHOTS_BEFORE_UPLOAD="${REBUILD_SNAPSHOTS_BEFORE_UPLOAD:-false}"

cd "$(dirname "$0")/../.."

if [[ "$REBUILD_SNAPSHOTS_BEFORE_UPLOAD" == "true" ]]; then
  app/backend/.venv/bin/python knowledge/ingestion/ingest.py --no-fetch
  app/backend/.venv/bin/python knowledge/refresh/ingest_releases.py --no-fetch
fi

app/backend/.venv/bin/python infra/scripts/validate_refresh_candidate.py \
  --knowledge-index knowledge/snapshots/oci-rag-index.json \
  --release-snapshot knowledge/snapshots/oci-release-snapshot.json

oci os object bulk-upload \
  --namespace-name "$NAMESPACE" \
  --bucket-name "$BUCKET" \
  --src-dir knowledge/snapshots \
  --include "*.json" \
  --overwrite \
  --profile "$OCI_CLI_PROFILE"

echo "Uploaded knowledge and release snapshots to bucket $BUCKET with OCI CLI profile $OCI_CLI_PROFILE"
