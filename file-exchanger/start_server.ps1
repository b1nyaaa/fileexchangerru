# File Exchanger Quick Launch Script
# PowerShell script to quickly start the server

Write-Host ""
Write-Host "╔════════════════════════════════════════╗"
Write-Host "║  📁 FILE EXCHANGER - Server Launcher  ║"
Write-Host "╚════════════════════════════════════════╝"
Write-Host ""

# Navigate to server directory
$serverPath = Join-Path $PSScriptRoot "server"

if (-not (Test-Path $serverPath)) {
    Write-Host "❌ Error: Server directory not found at $serverPath"
    Write-Host ""
    pause
    exit 1
}

# Check Python
Write-Host "Проверяю Python..."
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python найден: $pythonVersion"
} catch {
    Write-Host "❌ Python не найден!"
    Write-Host "Установите Python с https://www.python.org/downloads/"
    Write-Host ""
    pause
    exit 1
}

Write-Host ""
Write-Host "Запускаю сервер..."
Write-Host ""

# Change to server directory and start server
Set-Location $serverPath
python server.py

# If script reaches here, server has stopped
Write-Host ""
Write-Host "Сервер остановлен."
pause
