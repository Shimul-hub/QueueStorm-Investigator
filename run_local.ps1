# Start QueueStorm Investigator locally (loads .env automatically)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
    .\.venv\Scripts\pip install -r requirements.txt
}

if (-not (Test-Path ".env")) {
    Write-Host "Copy .env.example to .env and set OPENROUTER_API_KEY first."
    exit 1
}

Write-Host "Starting API at http://localhost:8000"
Write-Host "Swagger UI: http://localhost:8000/docs"
.\.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
