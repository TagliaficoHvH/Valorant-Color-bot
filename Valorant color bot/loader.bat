@echo off
:: Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python is not installed. Downloading and installing Python...
    start https://www.python.org/ftp/python/3.10.0/python-3.10.0-amd64.exe
    echo Please install Python and run this script again.
    pause
    exit /b
)

:: Check and install required dependencies
echo Checking dependencies...
pip install pyautogui keyboard opencv-python numpy mss >nul 2>&1

:: Run the main application
echo Starting the application...
python main.pyw
pause