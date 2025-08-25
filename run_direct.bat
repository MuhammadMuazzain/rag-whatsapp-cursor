@echo off
echo Running WhatsApp API with Python 3.10 directly...
echo.

REM Install packages for Python 3.10 if needed
"C:\Program Files\Python310\python.exe" -m pip install fastapi uvicorn httpx python-dotenv

echo.
echo Starting server...
echo.

REM Run the server
"C:\Program Files\Python310\python.exe" whatsapp_cloud_api.py

pause