$ErrorActionPreference = "Stop"

Write-Host "Starting GridMind Backend in a new window..." -ForegroundColor Green
Start-Process -FilePath "backend\venv\Scripts\python.exe" -ArgumentList "-m uvicorn backend.api.main:app --reload --port 8000"

Write-Host "Starting GridMind Frontend UI in a new window..." -ForegroundColor Green
Set-Location -Path "frontend"
Start-Process -FilePath "npm.cmd" -ArgumentList "run dev"

Write-Host "GridMind is now launching!" -ForegroundColor Cyan
Write-Host "Two new console windows should appear." -ForegroundColor Cyan
Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend UI: http://localhost:5173" -ForegroundColor Cyan

Read-Host -Prompt "Press Enter to close this launcher (the servers will remain running in their own windows)"
