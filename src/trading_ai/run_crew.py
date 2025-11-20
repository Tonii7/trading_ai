import os
import json
from datetime import datetime

from crewai import Agent, Task, Crew, LLM


# ============================================================
# 1. Подключение Llama3 через Ollama
# ============================================================

llm = LLM(
    model="llama3",                         # имя модели в Ollama
    provider="ollama",                      # провайдер
    api_base="http://127.0.0.1:11434",      # Ollama API endpoint
    temperature=0.3,
    timeout=60,
)


# ============================================================
# 2. Определяем агентов
# ============================================================

ny_agent = Agent(
    name="NY Session Setup Agent",
    role="Intraday NY session analyst",
    goal=(
        "Generate a structured pre-market trading setup for the upcoming "
        "New York session for US30 and SP500."
    ),
    backstory=(
        "You are an experienced NY session day trader. You analyze liquidity, "
        "overnight ranges, Asia/London structure, key levels and session timing."
    ),
    llm=llm,
    verbose=True,
)

research_agent = Agent(
    name="Research Agent",
    role="Trading strategy researcher",
    goal=(
        "Generate 1–2 practical trading ideas that Eldar can use "
        "for US30/SP500 during today's NY session."
    ),
    backstory=(
        "You specialize in trading research, modern price action, institutional concepts "
        "and volatility filters."
    ),
    llm=llm,
    verbose=True,
)

manager_agent = Agent(
    name="Supervisor",
    role="Coordinator",
    goal=(
        "Combine insights from both agents into one clear, structured, "
        "actionable briefing for Eldar in Russian language."
    ),
    backstory=(
        "You act like a trading floor manager. You summarize, refine and combine outputs "
        "into a final trading plan."
    ),
    llm=llm,
    verbose=True,
)


# ============================================================
# 3. Определяем задачи
# ============================================================

ny_task = Task(
    description=(
        "Provide a detailed NY session pre-market setup for US30 and SP500. "
        "Include: current bias, overnight high/low, Asia/London structure, "
        "liquidity pools, key levels, scenario A/B and invalidation."
    ),
    expected_output="Structured markdown trading plan.",
    agent=ny_agent,
)

research_task = Task(
    description=(
        "Provide 1–2 short, practical ideas for intraday NY session trading today. "
        "Focus on timing, volatility windows, liquidity grabs and risk filters."
    ),
    expected_output="Bullet list with explanation.",
    agent=research_agent,
)

manager_task = Task(
    description=(
        "Combine outputs of NY Setup and Research Agent. Create final NY session briefing "
        "for Eldar, in Russian, concise, suitable for Telegram."
    ),
    expected_output="Final Russian briefing.",
    agent=manager_agent,
)


# ============================================================
# 4. Crew (Команда агентов)
# ============================================================

crew = Crew(
    agents=[ny_agent, research_agent, manager_agent],
    tasks=[ny_task, research_task, manager_task],
    verbose=True,
)


# ============================================================
# 5. Логирование результатов
# ============================================================

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "ny_session_setups.jsonl")

os.makedirs(LOG_DIR, exist_ok=True)


def save_log(result_text: str):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "result": result_text,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ============================================================
# 6. Запуск
# ============================================================

if __name__ == "__main__":
    result = crew.run()

    print("\n========== FINAL NY SESSION BRIEFING ==========\n")
    print(result)

    save_log(str(result))
