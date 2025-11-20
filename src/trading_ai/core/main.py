# ==========================================
# main.py — стабильный запуск Trading AI Crew
# ==========================================

import sys
from pathlib import Path
from dotenv import load_dotenv

# -----------------------------------------------------------
# 1) Определяем корневую директорию проекта
#    main.py → src/trading_ai/core/main.py
# -----------------------------------------------------------
CORE_DIR = Path(__file__).resolve().parent               # src/trading_ai/core
TRADING_AI_DIR = CORE_DIR.parent                        # src/trading_ai
SRC_DIR = TRADING_AI_DIR.parent                         # src
PROJECT_ROOT = SRC_DIR.parent                           # trading_ai

CONFIG_DIR = TRADING_AI_DIR / "config"                  # src/trading_ai/config
CORE_DIR = TRADING_AI_DIR / "core"                      # src/trading_ai/core

# -----------------------------------------------------------
# 2) Загружаем .env из корня
# -----------------------------------------------------------
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
    print(f"✅ Loaded .env: {ENV_PATH}")
else:
    print(f"⚠️ .env not found at {ENV_PATH}")

# -----------------------------------------------------------
# 3) Настраиваем sys.path аккуратно
# -----------------------------------------------------------
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(TRADING_AI_DIR))
sys.path.insert(0, str(CORE_DIR))

print("🧩 sys.path configured:")
for p in sys.path[:5]:
    print("   ", p)

# -----------------------------------------------------------
# 4) Импортируем ядро
# -----------------------------------------------------------
try:
    from trading_ai.core.crew import TradingAi
except Exception as e:
    print(f"❌ Ошибка импорта TradingAi: {e}")
    print(f"Ищу crew.py по пути: {CORE_DIR}")
    sys.exit(1)

# -----------------------------------------------------------
# 5) Запуск
# -----------------------------------------------------------
if __name__ == "__main__":
    print("\n🚀 Launching Trading AI Crew...\n")

    try:
        app = TradingAi()
        output = app.run()
        print("\n✅ Crew operation finished.\n")

    except Exception as err:
        print(f"\n❌ Ошибка при запуске Crew: {err}\n")
