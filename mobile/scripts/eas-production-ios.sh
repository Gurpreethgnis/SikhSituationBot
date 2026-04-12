#!/usr/bin/env bash
# Run from repo: bash mobile/scripts/eas-production-ios.sh
# Prerequisite: eas login (or export EXPO_TOKEN=... for CI)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! eas whoami >/dev/null 2>&1; then
  echo "Not logged in to Expo. Run first:"
  echo "  eas login"
  echo "Or set EXPO_TOKEN (https://expo.dev/accounts/[account]/settings/access-tokens)"
  exit 1
fi

ENV_FILE="$ROOT/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE — copy from .env.example or run sync-env."
  exit 1
fi

# shellcheck disable=SC1090
set -a
# shellcheck source=/dev/null
source "$ENV_FILE"
set +a

if [[ -n "${EXPO_PUBLIC_FLASK_INTERNAL_KEY:-}" ]]; then
  eas env:create production \
    --name EXPO_PUBLIC_FLASK_INTERNAL_KEY \
    --value "$EXPO_PUBLIC_FLASK_INTERNAL_KEY" \
    --visibility secret \
    --non-interactive \
    --force \
    || true
fi

eas build --platform ios --profile production --non-interactive
eas submit --platform ios --latest --non-interactive

echo "Done."
