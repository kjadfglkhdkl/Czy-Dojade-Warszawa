@echo off
setlocal
cd /d "%~dp0src\backend"
where py >nul 2>nul
if errorlevel 1 (
  where python >nul 2>nul
  if errorlevel 1 (echo Python not found. Install Python 3.11+ and check Add Python to PATH.& pause& exit /b 1)
)
if not exist .venv (
  echo Creating backend virtual environment...
  py -3 -m venv .venv 2>nul
  if errorlevel 1 python -m venv .venv
  if errorlevel 1 (echo Could not create venv.& pause& exit /b 1)
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 (echo Python dependencies installation failed.& pause& exit /b 1)
echo.
echo Starting FastAPI at http://127.0.0.1:8000
python -m app
pause
