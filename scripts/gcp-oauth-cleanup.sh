#!/usr/bin/env bash
# Strip birthday-related Google Cloud config after dropping user.birthday.read from the app.
#
# Usage:
#   export GCP_PROJECT_ID=your-project-id
#   ./scripts/gcp-oauth-cleanup.sh
#   # or
#   ./scripts/gcp-oauth-cleanup.sh your-project-id
#
# Requires: Google Cloud SDK (gcloud). Install: https://cloud.google.com/sdk/docs/install
# Windows (winget): winget install Google.CloudSDK

set -euo pipefail

PROJECT="${1:-${GCP_PROJECT_ID:-}}"
if [[ -z "$PROJECT" ]]; then
  echo "Usage: GCP_PROJECT_ID=your-id $0   OR   $0 your-project-id" >&2
  exit 1
fi

CONSENT_URL="https://console.cloud.google.com/apis/credentials/consent?project=${PROJECT}"

if command -v gcloud >/dev/null 2>&1; then
  gcloud config set project "$PROJECT" 2>/dev/null || true
  echo "Disabling People API (optional; app no longer uses birthdays)..."
  if gcloud services disable people.googleapis.com --project="$PROJECT" --quiet 2>/dev/null; then
    echo "  people.googleapis.com disabled."
  else
    echo "  (Skip if already disabled, API not enabled, or insufficient permission.)"
  fi
else
  echo "gcloud not found in PATH. Install Google Cloud SDK, then run this script again." >&2
  echo "  https://cloud.google.com/sdk/docs/install" >&2
fi

echo ""
echo "OAuth consent scopes are not fully manageable via gcloud; open the Console once:"
echo "  ${CONSENT_URL}"
echo "  → Edit app → Scopes → remove https://www.googleapis.com/auth/user.birthday.read (if listed) → Save"
