$ErrorActionPreference = "Stop"

Write-Host "Starting GridMind Backend..." -ForegroundColor Green
Start-Process -NoNewWindow -FilePath "backend\venv\Scripts\python.exe" -ArgumentList "-m uvicorn backend.api.main:app --reload --port 8000"

Write-Host "Starting GridMind Frontend UI..." -ForegroundColor Green
Set-Location -Path "frontend"
Start-Process -NoNewWindow -FilePath "npm.cmd" -ArgumentList "run dev"

Write-Host "GridMind is now running!" -ForegroundColor Cyan
Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend UI: http://localhost:5173" -ForegroundColor Cyan

# Keep the window open
Read-Host -Prompt "Press Enter to exit and stop servers (you may need to manually kill Node/Python processes)"
