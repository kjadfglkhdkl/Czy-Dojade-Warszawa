@echo off
setlocal
cd /d "%~dp0"
echo Starting Czy dojade - API and Frontend...
start "Czy dojade - API" cmd /k "cd /d "%~dp0" && call start-api.bat"
start "Czy dojade - Frontend" cmd /k "cd /d "%~dp0" && call start-frontend.bat"
echo.
echo API docs: http://127.0.0.1:8000/docs
echo Frontend:  http://127.0.0.1:5174
echo Wait until both terminal windows show that their servers started.
timeout /t 5 /nobreak >nul
start "" "http://127.0.0.1:5174"
