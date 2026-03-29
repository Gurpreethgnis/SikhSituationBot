# Strip birthday-related Google Cloud config after dropping user.birthday.read from the app.
#
# Usage:
#   .\scripts\gcp-oauth-cleanup.ps1 -ProjectId your-gcp-project-id
#
# Requires gcloud in PATH (install: winget install Google.CloudSDK)

param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectId
)

$ConsentUrl = "https://console.cloud.google.com/apis/credentials/consent?project=$ProjectId"

$gcloud = Get-Command gcloud -ErrorAction SilentlyContinue
if ($gcloud) {
    gcloud config set project $ProjectId 2>$null
    Write-Host "Disabling People API (optional)..."
    gcloud services disable people.googleapis.com --project=$ProjectId --quiet 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  (Skipped: already disabled, not enabled, or no permission.)"
    }
    else {
        Write-Host "  people.googleapis.com disabled."
    }
}
else {
    Write-Warning "gcloud not in PATH. Install: winget install Google.CloudSDK"
}

Write-Host ""
Write-Host "Open OAuth consent screen and remove birthday scope if listed:"
Write-Host "  $ConsentUrl"
Write-Host "  Edit app -> Scopes -> remove user.birthday.read -> Save"

Start-Process $ConsentUrl
