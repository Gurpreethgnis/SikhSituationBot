# Create PR for SiddharthChopra branch (chat input feature)
# Usage: Set $env:GITHUB_TOKEN to a personal access token, then run:
#   .\create-pr.ps1
# Or: powershell -ExecutionPolicy Bypass -File create-pr.ps1

$token = $env:GITHUB_TOKEN
if (-not $token) {
  Write-Host "GITHUB_TOKEN not set. To create the PR automatically:"
  Write-Host "  1. Create a token at https://github.com/settings/tokens (scope: repo)"
  Write-Host "  2. Run: `$env:GITHUB_TOKEN = 'your-token'; .\create-pr.ps1"
  Write-Host ""
  Write-Host "Or open this link to create the PR in your browser:"
  Write-Host "  https://github.com/gurpreethgnis/sikhsituationbot/compare/main...SiddharthChopra?expand=1"
  exit 1
}

$body = @"
## Summary
Implements **Task 1** from TASK_ASSIGNMENTS.md for @siddharthchopra (UX): *Build chat input / search bar component* with a premium feel.

## Changes
- **Client scaffold**: Vite + React app in ``/client`` (port 5173)
- **ChatInput component**: Text input, Enter/Send submit, loading/disabled states, gold accent button
- **Theme**: Deep blue & gold (Sikh-inspired) in index.css
- **App**: ChatInput wired; onSend logs query to console (ready for Task 3)

## How to test
``````bash
cd client
npm install
npm run dev
``````
Open http://localhost:5173, type a message, press Enter or click Send — query in console.

## Related
- TASK_ASSIGNMENTS.md — @siddharthchopra (UX)
- Next: Task 2 — Persona toggle (Child/Teen/Adult) UI
"@

$json = @{
  title = "feat(ux): Add premium chat input / search bar component"
  head  = "SiddharthChopra"
  base  = "main"
  body  = $body
} | ConvertTo-Json

$headers = @{
  "Accept"        = "application/vnd.github.v3+json"
  "Authorization" = "Bearer $token"
}

try {
  $pr = Invoke-RestMethod -Uri "https://api.github.com/repos/gurpreethgnis/sikhsituationbot/pulls" -Method Post -Body $json -ContentType "application/json; charset=utf-8" -Headers $headers
  Write-Host "PR created: $($pr.html_url)"
} catch {
  Write-Host "Error: $_"
  exit 1
}
