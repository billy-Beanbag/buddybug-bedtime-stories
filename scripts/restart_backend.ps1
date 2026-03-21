# Restart Buddybug backend - kills existing process and starts fresh
$port = 8000
$ErrorActionPreference = "Stop"

Write-Host "Stopping backend on port $port..."
$conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "Stopped."
} else {
    Write-Host "Nothing running on $port."
}

Write-Host ""
Write-Host "Starting backend..."
Write-Host "Run this in a separate terminal to keep it running:"
Write-Host "  cd $PSScriptRoot\.."
Write-Host "  uvicorn app.main:app --reload --host 127.0.0.1 --port $port"
Write-Host ""
Write-Host "Or press Enter to start it here (Ctrl+C to stop)..."
Read-Host

Set-Location $PSScriptRoot\..
uvicorn app.main:app --reload --host 127.0.0.1 --port $port
