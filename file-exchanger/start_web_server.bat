@echo off
REM File Exchanger Web Server Starter
cls
echo.
echo ========================================
echo    File Exchanger - Web Server
echo ========================================
echo.

cd /d "%~dp0web"

echo Starting web server...
echo.

py server.py

pause
