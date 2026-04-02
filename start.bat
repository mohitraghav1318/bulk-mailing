@echo off
REM =============================================================================
REM start.bat — One-click setup and run for Windows users
REM =============================================================================
REM This script:
REM   1. Creates a virtual environment if it doesn't exist
REM   2. Activates the virtual environment
REM   3. Installs dependencies from requirements.txt
REM   4. Starts the Flask app
REM =============================================================================

echo.
echo ========================================
echo   Bulk Mailer - Starting...
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python from https://python.org and add it to PATH.
    echo During installation, check "Add Python to PATH".
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created.
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt -q
echo.

REM Start the app
echo ========================================
echo   App running at: http://localhost:5000
echo   Press Ctrl+C to stop
echo ========================================
echo.
python app.py
