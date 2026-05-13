# CTDA - Complete Project Runner
# This script starts both Backend (Flask) and Frontend (Vite) servers

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "CTDA - WhatsApp Chat Data Analysis" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& c:\ctda-main\.venv\Scripts\Activate.ps1

# Start Backend in background job
Write-Host "Starting Flask Backend Server..." -ForegroundColor Green
$backendJob = Start-Job -ScriptBlock {
    cd c:\ctda-main\backend
    python app.py
} -Name "CTDA-Backend"

Start-Sleep -Seconds 2

# Start Frontend in background job
Write-Host "Starting Vite Frontend Server..." -ForegroundColor Green
$frontendJob = Start-Job -ScriptBlock {
    cd c:\ctda-main\frontend\ctda
    npm run dev
} -Name "CTDA-Frontend"

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "✅ Both servers started!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📌 Backend:  http://127.0.0.1:5000" -ForegroundColor Yellow
Write-Host "📌 Frontend: http://localhost:5176" -ForegroundColor Yellow
Write-Host ""
Write-Host "Watching for changes..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop all servers" -ForegroundColor Red
Write-Host ""

# Display live logs from both jobs
while ($true) {
    $backendOutput = Receive-Job -Job $backendJob -Keep
    $frontendOutput = Receive-Job -Job $frontendJob -Keep
    
    if ($backendOutput) {
        Write-Host "[BACKEND] $backendOutput" -ForegroundColor Cyan
    }
    if ($frontendOutput) {
        Write-Host "[FRONTEND] $frontendOutput" -ForegroundColor Magenta
    }
    
    Start-Sleep -Milliseconds 500
}
