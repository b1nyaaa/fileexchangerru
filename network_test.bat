@echo off
REM Network Test Script for File Exchanger
cls
echo.
echo ===============================================
echo     FILE EXCHANGER - Network Diagnostics
echo ===============================================
echo.

echo [1] Getting your local IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| find "IPv4"') do (
    set "ip=%%a"
    goto :ip_found
)

:ip_found
echo Your Local IP: %ip%
echo.

echo [2] Testing if port 8888 is available...
netstat -ano | find ":8888" >nul
if errorlevel 1 (
    echo ✓ Port 8888 is AVAILABLE
) else (
    echo ✗ Port 8888 is already in use!
    echo   Solution: Stop the other process or change the port
)
echo.

echo [3] Share this address with other computers:
echo    http://%ip%:8888
echo.

echo [4] Connection Instructions:
echo    - Both computers must be in the SAME network
echo    - Firewall must allow port 8888
echo    - Server must be running (start_server.bat)
echo.

pause
