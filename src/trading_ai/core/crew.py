# ===========================================================
# crew.py — ядро Trading AI Crew с внешним хранилищем памяти
# ===========================================================

from crewai import Crew, Agent, Task, Process
from yaml import safe_load
import os
import datetime
import json
from pathlib import Path

# -------------------------------
# ОПРЕДЕЛЕНИЕ ПУТЕЙ
# -------------------------------
# этот файл: src/trading_ai/core/crew.py
CORE_DIR = Path(__file__).resolve().parent           # .../src/trading_ai/core
TRADING_AI_DIR = CORE_DIR.parent                     # .../src/trading_ai
CONFIG_DIR = TRADING_AI_DIR / "config"               # .../src/trading_ai/config
MEMORY_DIR = TRADING_AI_DIR / "memory"               # .../src/trading_ai/memory
REPORTS_DIR = TRADING_AI_DIR / "reports"             # .../src/trading_ai/reports

print("DEBUG TRADING_AI_DIR =", TRADING_AI_DIR)
print("DEBUG CONFIG_DIR     =", CONFIG_DIR)
print("DEBUG CONFIG EXISTS? =", CONFIG_DIR.exists())
print("DEBUG YAML FILES     =", list(CONFIG_DIR.glob("*.yaml")))


class TradingAi:
    """Главный класс Trading AI Crew с локальной памятью вне агентов."""

    def __init__(self):
        # === 1️⃣ Загружаем конфиги ===
        with open(CONFIG_DIR / "agents.yaml", "r", encoding="utf-8") as f:
            agents_cfg = safe_load(f).get("agents", {})

        with open(CONFIG_DIR / "tasks.yaml", "r", encoding="utf-8") as f:
            tasks_cfg = safe_load(f).get("tasks", {})

        # === 2️⃣ Директория памяти ===
        os.makedirs(MEMORY_DIR, exist_ok=True)
        self.memory_store = {}

        # === 3️⃣ Создаём агентов ===
        self.agents = {}
        for name, cfg in agents_cfg.items():
            key = name.lower().replace(" ", "_")

            self.agents[key] = Agent(
                role=cfg["role"],
                goal=cfg["goal"],
                backstory=cfg.get("backstory", ""),
                verbose=cfg.get("verbose", True)
            )

            # создаём файл памяти агента
            mem_file = MEMORY_DIR / f"{key}.json"
            if not mem_file.exists():
                with open(mem_file, "w", encoding="utf-8") as f:
                    json.dump({}, f)

            self.memory_store[key] = mem_file

        # === 4️⃣ Создаём задачи ===
        self.tasks = []
        for tkey, tcfg in tasks_cfg.items():
            agent_key = tcfg["agent"].lower().replace(" ", "_")
            if agent_key not in self.agents:
                raise ValueError(f"⚠️ Агент '{agent_key}' не найден в agents.yaml")

            self.tasks.append(
                Task(
                    description=tcfg["description"],
                    expected_output=tcfg["expected_output"],
                    agent=self.agents[agent_key]
                )
            )

        # === 5️⃣ Собираем команду ===
        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )

    # =======================================================
    # Метод запуска и сохранения отчётов
    # =======================================================
    def run(self):
        print("🚀 Launching Trading AI Crew...")
        results = self.crew.kickoff()
        print("✅ Crew operation completed!")

        result_text = str(results)

        # === Сохраняем отчёт ===
        os.makedirs(REPORTS_DIR, exist_ok=True)
        date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_path = REPORTS_DIR / f"{date_str}.txt"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(result_text)

        # === Записываем в память ===
        for key, mem_file in self.memory_store.items():
            try:
                with open(mem_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                data[f"report_{date_str}"] = {
                    "timestamp": date_str,
                    "text": result_text
                }

                with open(mem_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

                print(f"💾 Память обновлена: {key}")

            except Exception as e:
                print(f"⚠️ Ошибка записи памяти {key}: {e}")

        return result_text
