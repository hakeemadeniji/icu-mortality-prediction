# ICU Mortality Prediction System - Complete Startup Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ICU MORTALITY PREDICTION SYSTEM" -ForegroundColor Cyan
Write-Host "Advanced AI Interface" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set working directory
Set-Location "C:\Users\adeni\Documents\icu-mortality-prediction"

# Step 1: Start Backend
Write-Host "Step 1: Starting Backend Server (Port 8054)..." -ForegroundColor Green
$backendDir = "C:\Users\adeni\Documents\icu-mortality-prediction\backend"
$venvPython = "$backendDir\venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv "$backendDir\venv"
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    & "$backendDir\venv\Scripts\pip.exe" install fastapi uvicorn pydantic pydantic-settings python-dotenv
}

Write-Host "Starting backend server..." -ForegroundColor Green
Start-Process -FilePath $venvPython -ArgumentList "main.py" -WorkingDirectory $backendDir -WindowStyle Normal

# Wait for backend to start
Start-Sleep -Seconds 5

# Step 2: Start Frontend
Write-Host "Step 2: Starting Frontend Server (Port 3054)..." -ForegroundColor Green
$frontendDir = "C:\Users\adeni\Documents\icu-mortality-prediction\frontend"

if (-not (Test-Path "$frontendDir\node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location $frontendDir
    npm install
    Set-Location "C:\Users\adeni\Documents\icu-mortality-prediction"
}

Write-Host "Starting frontend server..." -ForegroundColor Green
Start-Process -FilePath "npm" -ArgumentList "run dev" -WorkingDirectory $frontendDir -WindowStyle Normal

# Step 3: Open Browser
Write-Host "Step 3: Opening browser..." -ForegroundColor Green
Start-Sleep -Seconds 5
Start-Process "http://localhost:3054"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SYSTEM STARTUP COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend: http://localhost:3054" -ForegroundColor Yellow
Write-Host "Backend API: http://localhost:8054" -ForegroundColor Yellow
Write-Host "API Documentation: http://localhost:8054/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop this script (servers will continue running)" -ForegroundColor Red

# Keep script running
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "Cleanup completed." -ForegroundColor Green
}