@echo off
REM CTDA - Complete Project Runner
REM This script starts Backend and Frontend servers

setlocal enabledelayedexpansion

echo.
echo =====================================
echo CTDA - WhatsApp Chat Data Analysis
echo =====================================
echo.

REM Activate venv and start both servers
cd /d c:\ctda-main

echo Starting Backend (Flask) and Frontend (Vite)...
echo.
echo Backend:  http://127.0.0.1:5000
echo Frontend: http://localhost:5176
echo.
echo Press Ctrl+C in either terminal to stop
echo.

REM Start backend in new window
start "CTDA Backend" cmd /k "cd c:\ctda-main\backend && python app.py"

REM Wait a moment then start frontend
timeout /t 2 /nobreak
start "CTDA Frontend" cmd /k "cd c:\ctda-main\frontend\ctda && npm run dev"

echo Both servers started in new windows!
pause
