@echo off
echo ========================================
echo ICU MORTALITY PREDICTION SYSTEM
echo Ghost in the Shell Edition
echo ========================================
echo.

echo Starting Backend Server (Port 8054)...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
echo Installing dependencies...
pip install -r requirements.txt
echo Starting FastAPI server...
start "Backend Server" cmd /k "python main.py"
cd ..

echo.
echo Starting Frontend Server (Port 3054)...
cd frontend
echo Installing dependencies...
call npm install
echo Starting Next.js development server...
start "Frontend Server" cmd /k "npm run dev"
cd ..

echo.
echo ========================================
echo SYSTEM STARTUP COMPLETE
echo ========================================
echo.
echo Frontend: http://localhost:3054
echo Backend API: http://localhost:8054
echo API Documentation: http://localhost:8054/docs
echo.
echo Press any key to exit...
pause