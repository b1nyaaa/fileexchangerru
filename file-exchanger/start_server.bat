@echo off
REM File Exchanger Server Starter
echo.
echo ========================================
echo    File Exchanger - Server
echo ========================================
echo.

cd /d "%~dp0server"

echo Starting server...
echo.

py server.py

pause
