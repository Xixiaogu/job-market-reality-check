param(
    [int]$Port = 8765,
    [switch]$Reload
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

if (-not $projectRoot) {
    $projectRoot = (Get-Location).Path
}

Set-Location $projectRoot
$env:PYTHONUTF8 = "1"

python -c "import fastapi, uvicorn"

if ($LASTEXITCODE -ne 0) {
    throw "FastAPI or Uvicorn is missing. Re-run the Phase 6A setup script."
}

python -m local_api.cli doctor

if ($LASTEXITCODE -ne 0) {
    throw "Local API environment check failed."
}

$tokenPath = Join-Path $projectRoot "local_api\runtime\api_token.txt"
$dbPath = Join-Path $projectRoot "data\job_market.db"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Job Market Reality Check Local API" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Address: http://127.0.0.1:$Port"
Write-Host "API docs: http://127.0.0.1:$Port/docs"
Write-Host "Database: $dbPath"
Write-Host "Token file: $tokenPath"
Write-Host "Stop server: Ctrl + C"
Write-Host ""

$arguments = @(
    "-m",
    "uvicorn",
    "local_api.main:app",
    "--host",
    "127.0.0.1",
    "--port",
    "$Port"
)

if ($Reload) {
    $arguments += "--reload"
}

& python @arguments

if ($LASTEXITCODE -ne 0) {
    throw "Local API exited with code: $LASTEXITCODE"
}
