@echo off
echo ========================================
echo    AI VULNERABILITY DISCOVERY TOOL
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "myenv" (
    echo Creating virtual environment...
    python -m venv myenv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
echo Activating virtual environment...
call myenv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing dependencies...
pip install -r requirementupdated_fixed.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo Dependencies installed successfully!

REM Create necessary directories
echo Creating output directories...
if not exist "outputs" mkdir outputs
if not exist "data\prompts" mkdir data\prompts
if not exist "data\reference" mkdir data\reference

REM Check config.json exists
if not exist "config.json" (
    echo WARNING: config.json not found!
    echo Please create config.json with your API keys and settings
    pause
    exit /b 1
)

REM Run the main discovery script
echo.
echo ========================================
echo Starting Vulnerability Discovery...
echo ========================================
echo.

REM Ask user which script to run
echo Choose which script to run:
echo 1. Standard discovery (run_discovery.py)
echo 2. Checkpoint-enabled discovery (run_discovery_checkpoint.py)
echo.

set /p choice="Enter choice (1 or 2): "

if "%choice%"=="1" (
    echo Running standard discovery...
    python run_discovery.py
) else if "%choice%"=="2" (
    echo Running checkpoint-enabled discovery...
    python run_discovery_checkpoint.py
) else (
    echo Invalid choice, running standard discovery...
    python run_discovery.py
)

echo.
echo ========================================
echo Discovery process completed!
echo Check the 'outputs' directory for results
echo ========================================
pause
