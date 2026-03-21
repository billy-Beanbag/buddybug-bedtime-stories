# Start Buddybug backend - kills any existing process on 8000 first
$port = 8000
$root = Split-Path $PSScriptRoot -Parent

Write-Host "Stopping any process on port $port..." -ForegroundColor Yellow
$conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    $conn | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 2
    Write-Host "Stopped." -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting backend at http://127.0.0.1:$port" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

Set-Location $root
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port $port
