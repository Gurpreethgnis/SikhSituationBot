#!/usr/bin/env bash
# Apply one-off PostgreSQL schema updates for the Flask app.
# Idempotent: safe to re-run (IF NOT EXISTS / soft patterns).
#
# Usage:
#   export DATABASE_URL='postgresql://USER:PASS@HOST:5432/DBNAME'
#   ./server/scripts/apply_postgres_migrations.sh
#
# Or pass the URL as the first argument:
#   ./server/scripts/apply_postgres_migrations.sh 'postgresql://...'
#
# SQLAlchemy URLs are normalized automatically, e.g.:
#   postgresql+psycopg2://user:pass@host/db  -> postgresql://...
#
# Requires: psql (PostgreSQL client) on PATH.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

RAW="${DATABASE_URL:-${1:-}}"
if [[ -z "$RAW" ]]; then
  echo "Error: DATABASE_URL is not set and no connection string was passed." >&2
  echo "" >&2
  echo "  export DATABASE_URL='postgresql://USER:PASS@HOST:5432/DBNAME'" >&2
  echo "  bash server/scripts/apply_postgres_migrations.sh" >&2
  echo "" >&2
  echo "  # or" >&2
  echo "  bash server/scripts/apply_postgres_migrations.sh 'postgresql://...'" >&2
  exit 1
fi

# Strip SQLAlchemy driver prefix so libpq accepts the URI
URL="$RAW"
URL="${URL#postgresql+psycopg2://}"
URL="${URL#postgresql+asyncpg://}"
if [[ "$URL" != "$RAW" ]]; then
  URL="postgresql://${URL}"
fi
URL="${URL/postgres:\/\//postgresql:\/\/}"

if ! command -v psql >/dev/null 2>&1; then
  echo "Error: psql not found. Install PostgreSQL client tools." >&2
  exit 1
fi

echo "Applying migrations from $SCRIPT_DIR ..."
psql "$URL" -v ON_ERROR_STOP=1 -f "$SCRIPT_DIR/add_user_memory_postgres.sql"
echo "Migrations applied successfully."
