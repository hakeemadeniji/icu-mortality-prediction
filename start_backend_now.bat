@echo off
REM ── Canonical backend launcher ─────────────────────────────────────────
REM Runs the FastAPI app with uvicorn from the backend venv.
REM Uses the module target "main:app" so the `from main import ...` service
REM globals resolve correctly. API will be available at http://localhost:8054
echo Starting ICU backend API on http://localhost:8054 ...
cd /d "%~dp0backend"
"venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8054
pause
