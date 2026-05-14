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

VITE_API_BASE_URL="${VITE_API_BASE_URL:-}" npm --prefix "$FRONTEND_DIR" run build

while IFS= read -r -d '' file; do
  object_name="${file#"$FRONTEND_DIR/dist/"}"
  case "$object_name" in
    *.html) content_type="text/html; charset=utf-8" ;;
    *.css) content_type="text/css; charset=utf-8" ;;
    *.js) content_type="application/javascript; charset=utf-8" ;;
    *.json) content_type="application/json; charset=utf-8" ;;
    *.svg) content_type="image/svg+xml" ;;
    *.png) content_type="image/png" ;;
    *.jpg | *.jpeg) content_type="image/jpeg" ;;
    *) content_type="application/octet-stream" ;;
  esac
  oci os object put \
    --namespace-name "$NAMESPACE" \
    --bucket-name "$BUCKET" \
    --file "$file" \
    --name "$object_name" \
    --content-type "$content_type" \
    --force \
    --profile "$OCI_CLI_PROFILE" >/dev/null
  echo "Uploaded $object_name ($content_type)"
done < <(find "$FRONTEND_DIR/dist" -type f -print0)

echo "Uploaded frontend assets to bucket $BUCKET with OCI CLI profile $OCI_CLI_PROFILE"
