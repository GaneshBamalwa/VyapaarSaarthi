# Start VyapaarOS Backend
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
    Write-Host "[Setup] Creating virtual environment..."
    python -m venv .venv
}

Write-Host "[Setup] Activating venv and installing dependencies..."
& ".venv\Scripts\Activate.ps1"
pip install -r requirements.txt -q

# Copy .env if not present
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[Setup] Created .env from .env.example (mock GCP mode enabled)"
}

Write-Host "[VyapaarOS] Starting FastAPI server on http://localhost:8000"
Write-Host "[VyapaarOS] API docs at http://localhost:8000/docs"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
