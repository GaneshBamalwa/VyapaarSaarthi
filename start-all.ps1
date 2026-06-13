# Start both backend and frontend in separate PowerShell windows
$root = $PSScriptRoot

Write-Host "Starting VyapaarOS..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\backend'; .\start.ps1"
Start-Sleep 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\frontend'; .\start.ps1"

Write-Host ""
Write-Host "Services starting:"
Write-Host "  Backend:  http://localhost:8000"
Write-Host "  API Docs: http://localhost:8000/docs"
Write-Host "  Frontend: http://localhost:5173"
