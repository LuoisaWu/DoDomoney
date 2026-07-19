@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
set "PHONE_DIR=%ROOT%apps\phone\Dodomoney"
set "WLAN_IP="

for /f "tokens=4" %%I in ('route print -4 ^| findstr /R /C:"^ *0.0.0.0 *0.0.0.0"') do (
  if not defined WLAN_IP set "WLAN_IP=%%I"
)

if not defined WLAN_IP (
  echo [Dodomoney] Could not detect the current hotspot/WLAN IPv4 address.
  echo Run ipconfig and enter the WLAN IPv4 manually on the App login page.
  pause
  exit /b 1
)

if /i "%~1"=="--detect-only" (
  echo !WLAN_IP!
  exit /b 0
)

(
  echo VITE_API_BASE_URL=http://127.0.0.1:8000
  echo VITE_APP_API_BASE_URL=http://!WLAN_IP!:8000
) > "%PHONE_DIR%\.env.local"

echo [Dodomoney] Hotspot/WLAN address detected:
echo   http://!WLAN_IP!:8000
echo.
echo [Dodomoney] Updated:
echo   apps\phone\Dodomoney\.env.local
echo.

netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul
if errorlevel 1 (
  echo [Dodomoney] Starting API in a separate window...
  start "Dodomoney API" cmd.exe /k call "%ROOT%start-api.bat"
) else (
  echo [Dodomoney] API is already listening on port 8000.
)

echo.
echo Next:
echo   1. Run the project to your phone again in HBuilderX.
echo   2. Tap "Use hotspot debugging" on the login page.
echo   3. Confirm the address is http://!WLAN_IP!:8000 and log in.
echo.
echo If the phone still cannot connect, use start-phone-debug.bat for USB forwarding.
pause
