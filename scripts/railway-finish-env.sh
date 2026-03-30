#!/usr/bin/env bash
# Finish Railway (Flask) env vars for Vercel + Railway deployment.
#
# Prerequisites (run from repo root):
#   npx @railway/cli@latest login
#   npx @railway/cli@latest link    # select your Flask service project
#
# Required:
#   VERCEL_URL — your production site, no trailing slash
#     e.g. export VERCEL_URL=https://sikhsituationbot.vercel.app
#
# Optional:
#   SERVICE    — railway service name if you have multiple (-s "$SERVICE")
#   SET_JWT=1  — also set JWT_SECRET (generates one if JWT_SECRET env empty)
#   JWT_SECRET — use this value when SET_JWT=1 instead of generating
#
# Example:
#   export VERCEL_URL=https://your-app.vercel.app
#   SET_JWT=1 ./scripts/railway-finish-env.sh

set -euo pipefail

RAILWAY="${RAILWAY_CMD:-npx --yes @railway/cli@latest}"

if ! command -v npx >/dev/null 2>&1; then
  echo "npx is required (Node.js)." >&2
  exit 1
fi

if [[ -z "${VERCEL_URL:-}" ]]; then
  echo "Set VERCEL_URL to your Vercel deployment URL (no trailing slash)." >&2
  echo "  export VERCEL_URL=https://your-app.vercel.app" >&2
  exit 1
fi

VERCEL_URL="${VERCEL_URL%/}"

svc=()
if [[ -n "${SERVICE:-}" ]]; then
  svc=( -s "$SERVICE" )
fi

echo "Setting PUBLIC_APP_URL=$VERCEL_URL on Railway..."
$RAILWAY variable set "${svc[@]}" "PUBLIC_APP_URL=$VERCEL_URL"

if [[ "${SET_JWT:-}" == "1" ]]; then
  if [[ -z "${JWT_SECRET:-}" ]]; then
    if ! command -v openssl >/dev/null 2>&1; then
      echo "openssl not found; set JWT_SECRET in the environment or install openssl." >&2
      exit 1
    fi
    JWT_SECRET="$(openssl rand -base64 48)"
    echo "Generated JWT_SECRET (not printed). Sending to Railway via stdin..."
  else
    echo "Using JWT_SECRET from environment (not printed). Sending to Railway via stdin..."
  fi
  printf '%s' "$JWT_SECRET" | $RAILWAY variable set "${svc[@]}" JWT_SECRET --stdin
  echo "JWT_SECRET updated on Railway. Existing JWTs will stop working until users sign in again."
fi

echo ""
if [[ -n "${SERVICE:-}" ]]; then
  echo "Done. Verify with: $RAILWAY variable list -s $SERVICE"
else
  echo "Done. Verify with: $RAILWAY variable list"
fi
echo ""
echo "Vercel (same values as Railway where noted):"
echo "  - FLASK_INTERNAL_API_KEY  → must equal Railway FLASK_INTERNAL_API_KEY"
echo "  - NEXT_PUBLIC_API_URL     → https://<your-railway-flask>.up.railway.app (or custom domain)"
echo "  - FLASK_API_URL           → same as NEXT_PUBLIC_API_URL (server-side oauth-sync / login)"
echo "  - NEXTAUTH_URL            → $VERCEL_URL"
echo "  - NEXTAUTH_SECRET         → openssl rand -base64 32 (required)"
echo "  - GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET → Web client; redirect: \${NEXTAUTH_URL}/api/auth/callback/google"
