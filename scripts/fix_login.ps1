# Fix Buddybug login
# Run from project root: .\scripts\fix_login.ps1

$base = "http://127.0.0.1:8000"

Write-Host "Buddybug Login Fix" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Reset DB and seed
Write-Host "1. Resetting database and seeding demo data..." -ForegroundColor Yellow
python scripts/fix_dev_setup.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "   fix_dev_setup failed" -ForegroundColor Red
    exit 1
}
Write-Host "   Done." -ForegroundColor Green
Write-Host ""

# Step 2: Check if backend is running
Write-Host "2. Checking backend on port 8000..." -ForegroundColor Yellow
try {
    $null = Invoke-RestMethod -Uri "$base/health" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "   Backend is running." -ForegroundColor Green
} catch {
    Write-Host "   Backend is NOT running." -ForegroundColor Red
    Write-Host ""
    Write-Host "   Start the backend in a NEW terminal:" -ForegroundColor Yellow
    Write-Host "   cd $PWD" -ForegroundColor White
    Write-Host "   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000" -ForegroundColor White
    Write-Host ""
    Write-Host "   Then run this script again: .\scripts\fix_login.ps1" -ForegroundColor Yellow
    exit 1
}

# Step 3: Seed admin (in case backend uses different DB)
Write-Host ""
Write-Host "3. Seeding admin user..." -ForegroundColor Yellow
try {
    $r = Invoke-RestMethod -Uri "$base/dev/seed-admin" -Method POST -ErrorAction Stop
    Write-Host "   $($r.hint)" -ForegroundColor Green
} catch {
    Write-Host "   (Endpoint may not exist in older backend - that's OK)" -ForegroundColor Gray
}

# Step 4: Test login
Write-Host ""
Write-Host "4. Testing login..." -ForegroundColor Yellow
$body = '{"email":"admin@buddybug.local","password":"Admin123!"}'
try {
    $token = Invoke-RestMethod -Uri "$base/users/login" -Method POST -ContentType "application/json" -Body $body -ErrorAction Stop
    Write-Host "   Login OK!" -ForegroundColor Green
    Write-Host ""
    Write-Host "SUCCESS. Log in at http://127.0.0.1:3000/login with:" -ForegroundColor Green
    Write-Host "   Email:    admin@buddybug.local" -ForegroundColor Cyan
    Write-Host "   Password: Admin123!" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or click the 'Demo: Admin123!' button on the login page." -ForegroundColor Cyan
} catch {
    Write-Host "   Login failed." -ForegroundColor Red
    Write-Host "   Error: $($_.ErrorDetails.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "   The backend may be running OLD code. Do this:" -ForegroundColor Yellow
    Write-Host "   1. Stop the backend (Ctrl+C in its terminal)" -ForegroundColor White
    Write-Host "   2. Start it again: python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000" -ForegroundColor White
    Write-Host "   3. Run this script again: .\scripts\fix_login.ps1" -ForegroundColor White
    exit 1
}
