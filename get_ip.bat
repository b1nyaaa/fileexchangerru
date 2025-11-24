@echo off
REM Get Local IP Address Script
echo.
echo ===============================================
echo     Your Local IP Address
echo ===============================================
echo.

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| find "IPv4"') do echo Your Server IP: %%a

echo.
echo Share this IP address with other computers
echo to connect to your File Exchanger server
echo.
echo Example: http://192.168.1.100:8888
echo.
pause
