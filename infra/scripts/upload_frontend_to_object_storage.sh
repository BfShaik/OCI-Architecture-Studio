#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <namespace> <bucket-name>" >&2
  exit 1
fi

NAMESPACE="$1"
BUCKET="$2"
FRONTEND_DIR="app/frontend"
OCI_CLI_PROFILE="${OCI_CLI_PROFILE:-DEFAULT}"

cd "$(dirname "$0")/../.."

npm --prefix "$FRONTEND_DIR" run build

oci os object bulk-upload \
  --namespace-name "$NAMESPACE" \
  --bucket-name "$BUCKET" \
  --src-dir "$FRONTEND_DIR/dist" \
  --overwrite \
  --profile "$OCI_CLI_PROFILE"

echo "Uploaded frontend assets to bucket $BUCKET with OCI CLI profile $OCI_CLI_PROFILE"
