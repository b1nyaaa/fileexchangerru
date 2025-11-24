# File Exchanger Client Launcher
# Используйте этот файл для быстрого открытия клиента

$serverIP = Read-Host "Введите IP адрес сервера (например: 192.168.1.100)"
$port = "8888"

$url = "http://${serverIP}:${port}"

Write-Host "Открываю $url в браузере..."
Write-Host "Если браузер не открылся, скопируйте адрес выше и вставьте в браузер"

Start-Process $url
