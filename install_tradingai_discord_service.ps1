Write-Host "=== TradingAI Discord Bot Service Installer ===" -ForegroundColor Cyan

# -------------------------------------------
# 1. ПЕРЕМЕННЫЕ
# -------------------------------------------

$projectRoot = "C:\Users\Win11\Desktop\trading_ai"
$srcDir = "$projectRoot\src"
$python = "C:\Users\Win11\venv\Scripts\python.exe"
$nssmExe = "C:\nssm\nssm.exe"
$serviceName = "TradingAI-DiscordBot"
$logDir = "$projectRoot\logs"
$downloadUrl = "https://nssm.cc/release/nssm-2.24.zip"
$tempZip = "$env:TEMP\nssm.zip"

# -------------------------------------------
# 2. ПРОВЕРЯЕМ NSSM
# -------------------------------------------

if (-Not (Test-Path $nssmExe)) {
    Write-Host "[INFO] NSSM не найден. Скачиваю..." -ForegroundColor Yellow

    Invoke-WebRequest -Uri $downloadUrl -OutFile $tempZip
    Expand-Archive -Path $tempZip -DestinationPath "C:\nssm" -Force

    $nssmExe = (Get-ChildItem -Recurse "C:\nssm" -Filter "nssm.exe")[0].FullName
    Write-Host "[OK] NSSM установлен: $nssmExe" -ForegroundColor Green
} else {
    Write-Host "[OK] NSSM найден: $nssmExe" -ForegroundColor Green
}

# -------------------------------------------
# 3. СОЗДАЁМ ЛОГИ
# -------------------------------------------

if (-Not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir
    Write-Host "[OK] Папка logs создана: $logDir" -ForegroundColor Green
} else {
    Write-Host "[OK] Папка logs уже существует" -ForegroundColor Green
}

# -------------------------------------------
# 4. УДАЛЯЕМ СТАРЫЙ СЕРВИС (если есть)
# -------------------------------------------

& $nssmExe stop $serviceName 2>$null
& $nssmExe remove $serviceName confirm 2>$null

Write-Host "[OK] Старый сервис очищен" -ForegroundColor Green

# -------------------------------------------
# 5. СОЗДАЁМ НОВЫЙ СЕРВИС
# -------------------------------------------

Write-Host "[INFO] Создаю новый сервис..." -ForegroundColor Cyan

& $nssmExe install $serviceName $python "-m trading_ai.services.discord.bot"

# Настройки
& $nssmExe set $serviceName AppDirectory $srcDir
& $nssmExe set $serviceName AppStdout "$logDir\discord_out.log"
& $nssmExe set $serviceName AppStderr "$logDir\discord_err.log"
& $nssmExe set $serviceName Start SERVICE_AUTO_START

Write-Host "[OK] Сервис создан" -ForegroundColor Green

# -------------------------------------------
# 6. ЗАПУСК СЕРВИСА
# -------------------------------------------

Write-Host "[INFO] Запускаю сервис..." -ForegroundColor Cyan
& $nssmExe start $serviceName

Start-Sleep -Seconds 2

Write-Host "[INFO] Статус сервиса:" -ForegroundColor Cyan
& $nssmExe status $serviceName

Write-Host "=== Установка завершена ===" -ForegroundColor Green
