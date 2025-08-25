@echo off
echo ===========================================
echo Setting up WhatsApp Cloud API with Python 3.10
echo ===========================================

REM Check if virtual environment exists
if not exist "venv_whatsapp" (
    echo Creating virtual environment...
    "C:\Program Files\Python310\python.exe" -m venv venv_whatsapp
    echo Virtual environment created!
)

echo.
echo Activating virtual environment...
call venv_whatsapp\Scripts\activate.bat

echo.
echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn httpx python-dotenv

echo.
echo ===========================================
echo Starting WhatsApp Cloud API Server
echo ===========================================
echo.
python whatsapp_cloud_api.py

pause