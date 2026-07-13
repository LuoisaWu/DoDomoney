@echo off
setlocal

set "ROOT=%~dp0"
set "DESKTOP_DIR=%ROOT%apps\desktop"

cd /d "%DESKTOP_DIR%" || (
  echo [Dodomoney] Cannot enter apps\desktop.
  pause
  exit /b 1
)

if not exist "node_modules" (
  echo [Dodomoney] Installing desktop dependencies...
  if not defined ELECTRON_MIRROR set "ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/"
  npm install
  if errorlevel 1 (
    echo [Dodomoney] Desktop dependency installation failed.
    echo [Dodomoney] Try: set ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
    pause
    exit /b 1
  )
)

echo [Dodomoney] Desktop app starting...
npm run dev

pause
