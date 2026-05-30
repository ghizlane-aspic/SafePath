@echo off
echo ========================================
echo   SafePath - Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

echo [4/5] Installing dependencies...
echo This may take a few minutes...
python -m pip install --only-binary=:all: numpy
python -m pip install scipy flask flask-cors opencv-python mediapipe

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    echo.
    echo Troubleshooting:
    echo - Make sure you have internet connection
    echo - Try running: pip install --upgrade pip
    echo - Check if your firewall is blocking pip
    pause
    exit /b 1
)

echo [5/5] Generating alert sound...
python generate_alert_sound.py

echo.
echo ========================================
echo   Setup Complete! 
echo ========================================
echo.
echo To start the application:
echo   1. Run: start_application.bat
echo   OR manually:
echo   2. cd backend
echo   3. python app.py
echo   4. Open browser to http://127.0.0.1:5000
echo.
pause
