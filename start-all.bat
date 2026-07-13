@echo off
setlocal

set "ROOT=%~dp0"

echo [Dodomoney] Opening API and desktop terminals...
start "Dodomoney API" cmd /k call "%ROOT%start-api.bat"

echo [Dodomoney] Waiting for API health check...
for /L %%I in (1,1,30) do (
  curl.exe -fsS http://127.0.0.1:8000/health >nul 2>nul && goto api_ready
  timeout /t 1 /nobreak >nul
)

echo [Dodomoney] API did not become ready within 30 seconds.
echo [Dodomoney] Check the API terminal, then run start-desktop.bat yourself.
exit /b 1

:api_ready
start "Dodomoney Desktop" cmd /k call "%ROOT%start-desktop.bat"

echo [Dodomoney] Started. Keep both terminal windows open while developing.
