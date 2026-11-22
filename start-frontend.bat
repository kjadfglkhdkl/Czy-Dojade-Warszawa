@echo off
setlocal
cd /d "%~dp0src\frontend"
where npm >nul 2>nul
if errorlevel 1 (echo Node.js/npm not found. Install Node.js LTS from https://nodejs.org/.& pause& exit /b 1)
if not exist node_modules (
  echo Installing frontend dependencies...
  npm install
  if errorlevel 1 (echo npm install failed.& pause& exit /b 1)
)
echo Frontend uses same-origin /api proxy to backend 127.0.0.1:8000
echo Opening frontend at http://127.0.0.1:5174
npm run dev -- --host 127.0.0.1 --port 5174 --strictPort
pause
