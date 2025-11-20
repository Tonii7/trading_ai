# ===========================
# main.py — запуск Trading AI Crew
# ===========================

from __future__ import annotations

import os
import sys
from dotenv import load_dotenv

# Путь до корня проекта (trading_ai/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

# Загружаем .env из корня
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
    print(f"✅ .env loaded from: {ENV_PATH}")
else:
    print("⚠️ .env not found in project root, continuing without it.")

# Добавляем корень проекта в sys.path
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from trading_ai.core.crew import TradingAi  # noqa: E402


if __name__ == "__main__":
    crew = TradingAi()
    try:
        result = crew.run()
        # Сохраняем результат как last_report.txt
        last_report = os.path.join(PROJECT_ROOT, "last_report.txt")
        os.makedirs(os.path.dirname(last_report), exist_ok=True)
        with open(last_report, "w", encoding="utf-8") as f:
            f.write(result)
        print("\n📄 Финальный отчёт сохранён в last_report.txt")
    except Exception as e:
        print("\n❌ Ошибка при запуске агентов:", e)
