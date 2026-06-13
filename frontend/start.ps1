# Start VyapaarOS Frontend
Set-Location $PSScriptRoot

if (-not (Test-Path "node_modules")) {
    Write-Host "[Setup] Installing npm dependencies..."
    npm install
}

Write-Host "[VyapaarOS] Starting React dev server on http://localhost:5173"
npm run dev
