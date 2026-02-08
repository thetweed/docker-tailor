@echo off
echo Job Tracker Setup Script
echo.

REM Check Python
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Please install Python 3.8+
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Install Playwright
echo Installing Playwright browsers (this may take a minute)...
playwright install chromium

REM Create necessary directories
echo Creating directories...
if not exist uploads mkdir uploads
if not exist flask_session mkdir flask_session
if not exist flask_cache mkdir flask_cache

REM Create .env from example
if not exist .env (
    echo Creating .env file...
    if exist .env.example (
        copy .env.example .env
        echo IMPORTANT: Edit .env and add your Anthropic API key!
    ) else (
        echo Creating .env with template...
        (
            echo # Anthropic API Key
            echo ANTHROPIC_API_KEY=your-api-key-here
            echo.
            echo # Flask Secret Key (generate a random string^)
            echo FLASK_SECRET_KEY=your-secret-key-here
        ) > .env
        echo IMPORTANT: Edit .env and add your Anthropic API key!
    )
) else (
    echo .env file already exists
)

REM Initialize database
echo Initializing database...
python -c "from app import create_app; app = create_app(); app.app_context().push(); print('Database initialized')" 2>nul || echo Database will be initialized on first run

echo.
echo Setup complete!
echo.
echo Next steps:
echo   1. Edit .env and add your Anthropic API key
echo      Get one at: https://console.anthropic.com/settings/keys
echo.
echo   2. Start the app:
echo      python app.py
echo.
echo   3. Open your browser:
echo      http://localhost:5000
echo.
echo Tip: Keep this terminal window open while the app is running
echo.
pause