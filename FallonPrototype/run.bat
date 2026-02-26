@echo off
REM FALLON Launcher - Double-click to start

cd /d "%~dp0.."

REM Kill existing Python processes
taskkill /F /IM python.exe 2>nul
taskkill /F /IM python3.13.exe 2>nul
timeout /t 2 /nobreak >nul

REM Start Streamlit
start /b python -m streamlit run FallonPrototype/app.py

REM Wait for server
timeout /t 5 /nobreak >nul

REM Open Edge
start msedge http://localhost:8501

echo.
echo ========================================
echo   FALLON is running at localhost:8501
echo ========================================
echo.
echo Close this window to stop the server.
echo.

REM Keep window open
pause
taskkill /F /IM python.exe 2>nul
