@echo off
echo ========================================
echo   SafePath - Starting Application
echo ========================================
echo.

REM Activate virtual environment
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

echo Starting Flask server...
echo.
echo Dashboard will be available at: http://127.0.0.1:5000
echo.
echo Press CTRL+C to stop the server
echo.

cd backend
python app.py
