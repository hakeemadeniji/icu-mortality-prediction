@echo off
echo ========================================
echo ICU MORTALITY PREDICTION SYSTEM
echo Advanced AI Interface
echo ========================================
echo.

echo Step 1: Starting Backend Server...
cd C:\Users\adeni\Documents\icu-mortality-prediction\backend
call venv\Scripts\activate
echo Backend dependencies installed. Starting server...
python main.py
pause