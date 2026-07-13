@echo off
setlocal

set "ROOT=%~dp0"
set "API_DIR=%ROOT%apps\api"

cd /d "%API_DIR%" || (
  echo [Dodomoney] Cannot enter apps\api.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [Dodomoney] Creating Python virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    py -m venv .venv
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo [Dodomoney] Failed to create .venv. Please install Python 3.11+ and try again.
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"

python -c "import fastapi, uvicorn, pydantic_settings" >nul 2>nul
if errorlevel 1 (
  echo [Dodomoney] Installing backend dependencies...
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [Dodomoney] Backend dependency installation failed.
    pause
    exit /b 1
  )
)

echo [Dodomoney] API starting at http://127.0.0.1:8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause
