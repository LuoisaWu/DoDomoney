@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
set "ADB="

for /f "usebackq delims=" %%I in (`powershell.exe -NoProfile -Command "$p = Get-Process adb -ErrorAction SilentlyContinue | Where-Object Path | Select-Object -First 1 -ExpandProperty Path; if ($p) { $p }"`) do set "ADB=%%I"

if not defined ADB (
  for /d %%D in ("C:\uniapp\HBuilderX*") do (
    if exist "%%~fD\HBuilderX\plugins\launcher-tools\tools\adbs\adb.exe" (
      set "ADB=%%~fD\HBuilderX\plugins\launcher-tools\tools\adbs\adb.exe"
    )
  )
)

if not defined ADB (
  echo [Dodomoney] HBuilderX adb.exe was not found.
  echo Start HBuilderX, connect the phone, and run this file again.
  pause
  exit /b 1
)

echo [Dodomoney] Using ADB:
echo   %ADB%
echo.
"%ADB%" devices
"%ADB%" reverse tcp:8000 tcp:8000
if errorlevel 1 (
  echo [Dodomoney] Failed to create USB port forwarding.
  echo Confirm USB debugging authorization on the phone and retry.
  pause
  exit /b 1
)

echo.
echo [Dodomoney] USB forwarding ready:
echo   Phone http://127.0.0.1:8000  ^>  Computer http://127.0.0.1:8000
echo.
netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul
if errorlevel 1 (
  echo [Dodomoney] Starting API in a separate window...
  start "Dodomoney API" cmd.exe /k call "%ROOT%start-api.bat"
) else (
  echo [Dodomoney] API is already listening on port 8000.
)
echo.
echo In the App login page, tap "Use USB debugging" and then log in.
pause
