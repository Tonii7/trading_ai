import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

try:
    from crewai import Agent, Task, Crew, Process, LLM
except ModuleNotFoundError:
    class _DummyLLM:
        def __init__(self, *a, **k): ...
    class _DummyAgent:
        def __init__(self, *a, **k): ...
    class _DummyTask:
        def __init__(self, *a, **k): ...
    class _DummyCrew:
        def __init__(self, *a, **k): ...
        def kickoff(self, *a, **k):
            return "CrewAI not available. Install in real environment."
    class _Process:
        sequential = "sequential"
        concurrent = "concurrent"
    Agent = _DummyAgent
    Task = _DummyTask
    Crew = _DummyCrew
    Process = _Process
    LLM = _DummyLLM

# -------------------------------------------------
# Базовые пути и ENV
# -------------------------------------------------
try:
    ROOT = Path(__file__).resolve().parents[2]
except Exception:
    ROOT = Path.cwd()

ENV_PATH = ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

LOG_DIR = ROOT / "reports"
LOG_DIR.mkdir(exist_ok=True)

MODEL = os.getenv("MODEL", "ollama/llama3")
OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://127.0.0.1:11434")

# Реальный рыночный контекст
from trading_ai.data.market_data import load_realtime_market_context

# -------------------------------------------------
# Инициализация LLM через LiteLLM + Ollama
# -------------------------------------------------
llm = LLM(
    model=MODEL,
    provider="ollama",
    api_base=OLLAMA_API_BASE,
    temperature=0.3,
)

# -------------------------------------------------
# Агенты
# -------------------------------------------------
ny_session_agent = Agent(
    name="NY Index Session Setup Agent",
    role="Планировщик торгов по индексам на Нью-Йоркскую сессию",
    goal=(
        "Подготовить структурированный торговый план для NY-сессии по индексам "
        "(US30, S&P500, NAS100) с учётом новостей, ликвидности и ключевых уровней."
    ),
    backstory=(
        "Опытный внутридневной трейдер по американским индексам, формализующий сетапы "
        "в виде чёткого плана: контекст, уровни, сценарии и риски."
    ),
    verbose=True,
    llm=llm,
)

research_agent = Agent(
    name="Strategy Research Agent",
    role="Исследователь торговых стратегий",
    goal=(
        "Изучать и предлагать новые/существующие стратегии по индексам, указывать условия "
        "применения, сильные и слабые стороны."
    ),
    backstory=(
        "Квант-исследователь, умеющий объяснять сложные идеи простым языком и привязывать "
        "стратегии к рыночным режимам."
    ),
    verbose=True,
    llm=llm,
)

coordinator_agent = Agent(
    name="Session Coordinator Agent",
    role="Координатор торговой сессии",
    goal="Свести анализ, идеи и конечный план действий в единый документ для трейдера.",
    backstory=(
        "Профессиональный риск-менеджер, превращающий разрозненные идеи в исполнимый план "
        "с акцентом на риск-параметры."
    ),
    verbose=True,
    llm=llm,
)

# -------------------------------------------------
# Задачи
# -------------------------------------------------
ny_context_task = Task(
    name="NY market context",
    description=(
        "Собери краткий контекст по рынку перед открытием NY-сессии:"
        "\n- общая картина по US индексам (US30, S&P500, NASDAQ)"
        "\n- важные движения Азии и Европы"
        "\n- ключевые новости (макро, FOMC, earnings)"
        "\n- признаки risk-on / risk-off"
    ),
    expected_output="Краткий структурированный контекст NY-сессии",
    agent=ny_session_agent,
)

strategy_research_task = Task(
    name="Strategy ideas for today",
    description=(
        "Предложи 2–3 стратегии для NY-сессии. Для каждой укажи:"
        "\n- тип (пробой, возврат, ротация, импульс)"
        "\n- идею входа"
        "\n- таймфреймы"
        "\n- риск-параметры"
    ),
    expected_output="2–3 стратегии с триггерами и рисками",
    agent=research_agent,
)

final_plan_task = Task(
    name="NY session final plan",
    description=(
        "Подготовь финальный план NY-сессии:"
        "\n1. Контекст"
        "\n2. Ключевые уровни US30/S&P/NASDAQ"
        "\n3. Сценарии bull/bear/range"
        "\n4. Риск-рамки"
        "\n5. Чек-лист"
    ),
    expected_output="Финальный план NY session",
    agent=coordinator_agent,
)

crew = Crew(
    agents=[ny_session_agent, research_agent, coordinator_agent],
    tasks=[ny_context_task, strategy_research_task, final_plan_task],
    process=Process.sequential,
    verbose=True,
)

# -------------------------------------------------
# Логирование
# -------------------------------------------------
def save_log(result_text: str) -> None:
    log_file = LOG_DIR / "ny_session_crew_log.jsonl"
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "model": MODEL,
        "ollama_api_base": OLLAMA_API_BASE,
        "result": result_text,
    }
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# -------------------------------------------------
# Точка входа
# -------------------------------------------------
if __name__ == "__main__":
    print("\n[TradingAI] Запуск NY Session Crew...\n")
    print(f"ROOT: {ROOT}")
    print(f"Используем модель: {MODEL}")
    print(f"Ollama endpoint: {OLLAMA_API_BASE}\n")

    # 1) Подтягиваем реальный рыночный контекст
    market_context = load_realtime_market_context()
    ny_context_task.context = market_context

    # 2) Запускаем Crew
    result = crew.kickoff()

    # 3) Выводим и логируем
    print("\n========== FINAL NY SESSION BRIEFING ==========")
    print(result)
    save_log(str(result))
    print("\n[TradingAI] Результат сохранён в reports/ny_session_crew_log.jsonl\n")
