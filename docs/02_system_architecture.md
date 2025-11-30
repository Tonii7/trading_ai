# Eldar — TradingAI Technical Intelligence Book  
## Section 2 — System Architecture  
(Архитектура системы TradingAI)

---

## 2.1. Общая архитектура

TradingAI представляет собой модульную многоуровневую систему с чётким разделением ответственности между компонентами.  

Основная идея архитектуры:  
**каждый слой отвечает за свою зону, а взаимодействие происходит через строго определённые интерфейсы.**

Архитектура состоит из следующих уровней:

1. **Interaction Layer (пользовательские интерфейсы)**
2. **Agent Layer (CrewAI многоагентная система)**
3. **Service Layer (рынок, Discord, сессии, утилиты)**
4. **Data Layer (данные, логи, отчёты, знания)**
5. **Execution Layer (скрипты запуска, batch и runtime)**

---

## 2.2. Общая архитектурная диаграмма

```
                    ┌───────────────────────────────┐
                    │       Interaction Layer        │
                    │     (Discord, CLI, Scripts)    │
                    └───────────────┬────────────────┘
                                    │
                     ┌──────────────▼──────────────┐
                     │      CrewAI Agent Layer      │
                     │ Supervisor, Analyzer, etc.   │
                     └───────────────┬──────────────┘
                                     │
       ┌─────────────────────────────▼────────────────────────────┐
       │                     Service Layer                         │
       │ cTrader API | Market Engines | NY Session | Utils | Config│
       └───────────────┬──────────────┬────────────┬──────────────┘
                        │              │            │
           ┌────────────▼────────┐┌────▼───────────┐┌──────────────▼────────────┐
           │   Market Data        ││  Knowledge Base ││  Logs & Reports Storage   │
           │ Candles, Tick Data   ││  Structured KB  ││ CrewAI & Market Logs      │
           └──────────────────────┘└─────────────────┘└───────────────────────────┘
```

---

## 2.3. Описание уровней

### 1. Interaction Layer  
Отвечает за приём команд и отдачу отчётов.

Компоненты:
- Discord Bot  
- CLI запуск (`run_*.py`)  
- Batch-файлы (`run_discord_bot.bat`)  
- PowerShell сервисы  

Задача:  
**взаимодействие пользователя → система.**

---

### 2. Agent Layer (CrewAI)

Многоагентная система, выполняющая:

- анализ рынка  
- обработку новостей  
- генерацию отчётов  
- принятие решений  
- синхронизацию данных  
- автоматизацию логики  

Основные агенты:
- Supervisor Agent  
- Market Analyzer  
- News Screener  
- Python Engineer  
- Расширяемые кастомные агенты  

Главный файл:  
```
src/trading_ai/run_crew.py
```

---

### 3. Service Layer

Сервисный слой — ядро операционной логики TradingAI.

Ключевые сервисы:

#### a) cTrader Service  
Работа с API брокера через:
- `ctrader_openapi_client.py`  
- `ctrader_price_source.py`  
- `ctrader_candles_data.py`  
- `ctrader_symbol_details.py`  
- `market_snapshot.py`

Именно отсюда поступает рыночная информация.

#### b) Discord Service  
- слушает сообщения  
- отправляет отчёты  
- делегирует задачи агентам  

Папка:  
```
src/trading_ai/services/discord/
```

#### c) NY Session Engine  
Самостоятельная система анализа поведения рынка в Нью-Йоркскую сессию.

#### d) Logging & Output Routing  
Конфигурация маршрутов вывода данных:  
```
src/trading_ai/config/output_routes.yaml
```

---

### 4. Data Layer

Слой данных включает:

- **knowledge** — текстовые файлы, база знаний  
- **knowledge_base** — внутренний KB  
- **reports** — JSON, TXT отчёты  
- **utils** — вспомогательные обработчики данных  

Система максимально прозрачна:  
все данные сохраняются и доступны для анализа.

---

### 5. Execution Layer

Отвечает за запуск всей системы.

Ключевые элементы:
- Batch-файлы  
- PowerShell сервисы  
- Скрипты запуска  
- Runtime-модули  

Примеры:
```
run_discord_bot.bat
src/trading_ai/run_market_engine.py
src/trading_ai/run_discord_test.py
```

---

## 2.4. Поток выполнения (Execution Flow)

### Основная последовательность:

1. Пользователь отправляет команду → Discord Bot  
2. Discord передаёт запрос в Supervisor Agent  
3. Supervisor распределяет задачу между агентами  
4. Агент вызывает нужный сервис  
5. Сервис получает данные (cTrader, рынок, KB)  
6. Агент формирует вывод  
7. Вывод поступает обратно в Discord  

---

## 2.5. Поток данных (Data Flow)

```
Market Prices → cTrader API → Market Engine → CrewAI →
   → Supervisor Agent → Discord Bot → User
```

Одновременно:

```
News → News Screener → CrewAI → Report → Discord  
Logs → reports/ → persist as JSONL  
Knowledge → used by AI agents
```

---

## 2.6. Интеграционные точки

### 1) cTrader ↔ CrewAI  
Агенты могут запрашивать рыночные данные напрямую.

### 2) Discord ↔ CrewAI  
Командный интерфейс.

### 3) Output Routes  
Гибкое управление маршрутами:
```
src/trading_ai/config/output_routes.yaml
```

### 4) Market Snapshot  
Реализация live snapshot модели.

---

## 2.7. Назначение ключевых папок

| Папка                      | Назначение |
|---------------------------|------------|
| `src/trading_ai/agents`   | Агенты CrewAI |
| `src/trading_ai/services` | Сервисные модули системы |
| `src/trading_ai/config`   | Настройки маршрутов |
| `reports/`                | JSON/TXT отчёты системы |
| `knowledge/`              | Файлы знаний |
| `knowledge_base/`         | Расширенная база знаний |
| `utils/`                  | Вспомогательные инструменты |

---

## 2.8. Принципы архитектуры

1. **Модульность**  
2. **Разделение ответственности**  
3. **Расширяемость**  
4. **Прозрачность данных**  
5. **Управляемость**  
6. **Совместимость с AI-системами**  
7. **Документируемость**

---

## 2.9. Итоги секции

Система TradingAI представляет собой гибкую, масштабируемую архитектуру, где каждый слой имеет свою зону ответственности, а взаимодействие происходит через чёткие интеграционные точки.

Эта архитектура позволяет:
- подключать новые источники данных  
- расширять набор агентов  
- интегрировать новые сервисы  
- обеспечивать стабильность системы  
- строить аналитику уровня фонда  
