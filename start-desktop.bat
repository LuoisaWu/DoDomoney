@echo off
setlocal

set "ROOT=%~dp0"
set "DESKTOP_DIR=%ROOT%apps\desktop"

cd /d "%DESKTOP_DIR%" || (
  echo [Dodomoney] Cannot enter apps\desktop.
  pause
  exit /b 1
)

if not exist "package-lock.json" (
  echo [Dodomoney] Vue 3 dependency lock is not generated yet.
  echo [Dodomoney] Run this command yourself first: npm install
  pause
  exit /b 1
)

if not exist "node_modules\vue\package.json" (
  echo [Dodomoney] Vue 3 dependencies are not installed.
  echo [Dodomoney] Run this command yourself first: npm install
  pause
  exit /b 1
)

echo [Dodomoney] Desktop app starting...
npm run dev

pause
