# Start Buddybug - backend on 8765, frontend on 3000 (avoids conflicts with old 8000)
$ErrorActionPreference = "Continue"
$root = Split-Path $PSScriptRoot -Parent
$backendPort = 8765
$frontendPort = 3000

Write-Host "Buddybug startup" -ForegroundColor Cyan
Write-Host ""

# Kill existing
$conns = Get-NetTCPConnection -LocalPort $backendPort,$frontendPort -State Listen -ErrorAction SilentlyContinue
if ($conns) {
  Write-Host "Stopping existing processes..." -ForegroundColor Yellow
  $conns | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
  Start-Sleep -Seconds 2
}

Write-Host "1. Backend: http://127.0.0.1:$backendPort" -ForegroundColor Green
$backendCmd = "Set-Location '$root'; if (Test-Path .venv-agent\Scripts\Activate.ps1) { .\.venv-agent\Scripts\Activate.ps1 }; python -m uvicorn app.main:app --reload --host 127.0.0.1 --port $backendPort"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal

Write-Host "2. Frontend: http://127.0.0.1:$frontendPort (starting in 8s...)" -ForegroundColor Green
Start-Sleep -Seconds 8
$frontendCmd = "Set-Location '$root\buddybug_frontend'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -WindowStyle Normal

Write-Host ""
Write-Host "Login at http://127.0.0.1:$frontendPort/login" -ForegroundColor Cyan
Write-Host "  Email: admin@buddybug.local  |  Password: Admin123!" -ForegroundColor White
