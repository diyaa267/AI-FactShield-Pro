@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo       AI FactShield Pro - Starter
echo ==========================================

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo Installing/updating required packages...
venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo Package installation failed.
    pause
    exit /b 1
)

echo.
echo Starting AI FactShield Pro...
echo Open http://127.0.0.1:5000 in your browser.
echo Press Ctrl+C to stop the server.
echo.
venv\Scripts\python.exe app.py
pause
