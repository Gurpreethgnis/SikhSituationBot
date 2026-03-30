# Apply PostgreSQL schema updates (Windows / PowerShell).
# Idempotent. Requires: psql on PATH.
#
#   $env:DATABASE_URL = "postgresql://USER:PASS@HOST:5432/DBNAME"
#   .\server\scripts\apply_postgres_migrations.ps1
#
# Or:
#   .\server\scripts\apply_postgres_migrations.ps1 -DatabaseUrl "postgresql://..."

param(
    [string]$DatabaseUrl = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SqlFile = Join-Path $ScriptDir "add_user_memory_postgres.sql"

$raw = $DatabaseUrl
if (-not $raw) { $raw = $env:DATABASE_URL }
if (-not $raw) {
    Write-Error "Set DATABASE_URL or pass -DatabaseUrl 'postgresql://...'"
}

$url = $raw
if ($url -match '^postgresql\+psycopg2://') {
    $url = "postgresql://" + ($url -replace '^postgresql\+psycopg2://', '')
}
if ($url -match '^postgres://') {
    $url = $url -replace '^postgres://', 'postgresql://'
}

if (-not (Get-Command psql -ErrorAction SilentlyContinue)) {
    Write-Error "psql not found. Install PostgreSQL client tools and add to PATH."
}

Write-Host "Applying migrations from $ScriptDir ..."
& psql $url -v ON_ERROR_STOP=1 -f $SqlFile
Write-Host "Migrations applied successfully."
