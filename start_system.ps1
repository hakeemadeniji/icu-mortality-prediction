# ICU Mortality Prediction System Startup Script
# Ghost in the Shell Edition

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ICU MORTALITY PREDICTION SYSTEM" -ForegroundColor Cyan
Write-Host "Ghost in the Shell Edition" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start Backend Server
Write-Host "Starting Backend Server (Port 8054)..." -ForegroundColor Green
$backendProcess = Start-Process -FilePath "python" -ArgumentList "backend/main.py" -WorkingDirectory (Get-Location) -PassThru -WindowStyle Normal

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start Frontend Server
Write-Host "Starting Frontend Server (Port 3054)..." -ForegroundColor Green
$frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run dev" -WorkingDirectory "frontend" -PassThru -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SYSTEM STARTUP COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend: http://localhost:3054" -ForegroundColor Yellow
Write-Host "Backend API: http://localhost:8054" -ForegroundColor Yellow
Write-Host "API Documentation: http://localhost:8054/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop all servers" -ForegroundColor Red

# Keep script running
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "Stopping servers..." -ForegroundColor Yellow
    Stop-Process -Id $backendProcess.Id -Force
    Stop-Process -Id $frontendProcess.Id -Force
    Write-Host "Servers stopped." -ForegroundColor Green
}