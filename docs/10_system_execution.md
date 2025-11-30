# Eldar — TradingAI Technical Intelligence Book  
## Section 10 — System Deployment & Execution  
(Запуск и работа системы TradingAI)

---

## Введение

Этот раздел описывает, **как запускаются основные подсистемы TradingAI**, какие файлы отвечают за их выполнение, и какие инструменты используются для работы системы в реальном времени.

TradingAI состоит из множества сервисов и модулей, однако запуск системы — простой и стандартизированный процесс.

---

# 10.1. Основные способы запуска

Существует три уровня запуска:

1. **Run Scripts** — Python файлы для локального запуска.  
2. **Batch files (.bat)** — удобные ярлыки для Windows.  
3. **PowerShell Services (.ps1)** — системные сервисы для фоновой работы.  

Эта многоуровневая система делает запуск гибким и удобным.

---

# 10.2. Запуск Discord Bot

Discord — это интерфейс управления TradingAI.

Запуск осуществляется через:

### Вариант 1 — Python  
```
python src/trading_ai/run_discord_test.py
```

или боевой режим:

```
python run_discord_bot.bat
```

### Вариант 2 — Windows Batch-файл  
```
run_discord_bot.bat
```

### Вариант 3 — PowerShell Service  
Установка:

```
install_tradingai_discord_service.ps1
```

После этого бот будет работать **фоном**, как сервис Windows.

---

# 10.3. Запуск CrewAI

Основной файл:

```
src/trading_ai/run_crew.py
```

Запуск:

```
python src/trading_ai/run_crew.py
```

Этот файл:

- инициализирует Supervisor  
- подгружает агентов  
- запускает многоагентный процесс  
- связывает CrewAI → Discord  

Если CrewAI работают с ошибками — их логи появятся в `reports/`.

---

# 10.4. Запуск Market Engines

Для Market Engine могут быть выделены отдельные процессы.

Примеры:

```
python src/trading_ai/run_market_engine.py
```

```
python src/run_ctrader_market_agent.py
```

Market Engine должен быть активным, если:

- нужны актуальные данные  
- используются свечи  
- включены рыночные сценарии  

Эти процессы работают как аналитические слои в реальном времени.

---

# 10.5. Запуск NY Session Engine

Если требуется анализ NY Session:

```
python src/trading_ai/services/NY Session/run_ny.py
```

Если файл всё ещё отсутствует — его можно добавить.

Логи будут записываться в:

```
reports/ny_session_crew_log.jsonl
src/reports/ny_session_crew_log.jsonl
```

---

# 10.6. Использование batch-файлов (.bat)

Примеры в корне:

```
run_discord_bot.bat
set_env.bat
```

**run_discord_bot.bat** — самый удобный стартовый файл.  
Он:

- активирует окружение  
- запускает Discord bot  
- инициализирует сервисы

---

# 10.7. PowerShell сервисы (.ps1)

Файл:

```
install_tradingai_discord_service.ps1
```

Позволяет:

- установить сервис Discord бота  
- запускать его автоматически при загрузке ПК  
- перезапускать при сбоях  
- интегрировать TradingAI в инфраструктуру Windows  

Этот вариант подходит для «боевого» режима 24/7.

---

# 10.8. Управление конфигурацией через environment variables

Файл:

```
env_from_scheduler.txt
```

Также используется:

```
set_env.bat
```

Они позволяют:

- передавать ключи  
- менять конфигурацию  
- перенастраивать компоненты  

Основные переменные среды обычно включают:

- Discord BOT TOKEN  
- cTrader API credentials  
- пути к логам  
- режим работы (debug / production)  

---

# 10.9. Где хранятся результаты работы системы

### Логи:
```
reports/*.jsonl
ABSOLUTE_DEBUG.txt
src/reports/
```

### Файлы сессий:
```
reports/ny_session_crew_log.jsonl
```

### Итоговые отчёты агентов:
```
reports/crew_output_*.txt
```

### Snapshot данных рынка:
```
reports/market_snapshot_*.json
```

---

# 10.10. Типовой сценарий запуска системы

### Шаг 1 — открыть PowerShell
```
cd C:\Users\Win11\Desktop\trading_ai
```

### Шаг 2 — активировать окружение
```
.\venv\Scripts\Activate.ps1
```

### Шаг 3 — запустить Discord
```
run_discord_bot.bat
```

### Шаг 4 — при необходимости запустить CrewAI
```
python src/trading_ai/run_crew.py
```

### Шаг 5 — запустить Market Engine
```
python src/trading_ai/run_market_engine.py
```

### Шаг 6 — пользоваться Discord для управления
Команды:
```
/market
/session
/crew
/test
```

---

# 10.11. Итоги секции

Система Deployment & Execution TradingAI:

- гибкая  
- удобная  
- поддерживает фоновый режим  
- позволяет запускать подсистемы независимо  
- обеспечивает отказоустойчивую архитектуру  
- масштабируется через сервисы  

Эта секция завершает инженерную часть документации, делая систему понятной для запуска и поддержки.
