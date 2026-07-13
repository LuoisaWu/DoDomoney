@echo off
setlocal

set "ROOT=%~dp0"

echo [Dodomoney] Opening API and desktop terminals...
start "Dodomoney API" cmd /k call "%ROOT%start-api.bat"
timeout /t 3 /nobreak >nul
start "Dodomoney Desktop" cmd /k call "%ROOT%start-desktop.bat"

echo [Dodomoney] Started. Keep both terminal windows open while developing.
