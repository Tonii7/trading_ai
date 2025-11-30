@echo off
echo [RUN] Starting TradingAI Discord Bot...

REM === Правильный рабочий каталог ===
cd /d C:\Users\Win11\Desktop\trading_ai

REM === Устанавливаем PYTHONPATH ===
call C:\Users\Win11\Desktop\trading_ai\set_env.bat

REM === Активируем виртуальное окружение ===
call C:\Users\Win11\venv\Scripts\activate.bat

REM === Запуск Discord бота ===
python -m trading_ai.services.discord.bot
