@echo off
echo 🚑 Hospital Tracker - Quick Start
echo =================================
echo.

:: Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python detected

:: Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

echo.
echo ⚠️  IMPORTANT: Before starting the server
echo Edit app.py and add your HTTPSMS API key on line 25
echo.
pause

:: Start the application
echo 🚀 Starting Flask server...
python app.py
