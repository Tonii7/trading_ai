import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from fredapi import Fred

# === Пути проекта ===
CURRENT_FILE = os.path.abspath(__file__)
AGENTS_DIR = os.path.dirname(CURRENT_FILE)
TRADING_AI_DIR = os.path.dirname(AGENTS_DIR)
SRC_DIR = os.path.dirname(TRADING_AI_DIR)
ROOT_DIR = os.path.dirname(SRC_DIR)

if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

# === Настройка окружения ===
load_dotenv()

# === Логирование ===
os.makedirs(os.path.join(ROOT_DIR, "logs"), exist_ok=True)
log_file = os.path.join(ROOT_DIR, "logs", "fred_agent.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# === Импорт формул ===
from trading_ai.formulas.macro import MacroFormulas


class FredAgent:
    """FRED агент — получает макроэкономические данные и рассчитывает ключевые формулы."""

    def __init__(self, api_key: str | None = None):
        api_key = api_key or os.getenv("FRED_API_KEY")
        if not api_key:
            raise ValueError("FRED_API_KEY не найден в .env или переменных окружения")
        self.fred = Fred(api_key=api_key)

    def get_macro_data(self) -> dict:
        """Получает данные из FRED и рассчитывает макроформулы."""

        cpi_series = self.fred.get_series_latest_release("CPIAUCSL")
        data = {
            "CPI": cpi_series.iloc[-1],
            "CPI_prev": cpi_series.iloc[-2],
            "UNRATE": self.fred.get_series_latest_release("UNRATE").iloc[-1],
            "FEDFUNDS": self.fred.get_series_latest_release("FEDFUNDS").iloc[-1],
            "GS10": self.fred.get_series_latest_release("GS10").iloc[-1],
            "M2": self.fred.get_series_latest_release("M2SL").iloc[-1],
            "GDP": self.fred.get_series_latest_release("GDP").iloc[-1],
        }

        # 🧮 Расчёты
        inflation = MacroFormulas.inflation_rate(data["CPI"], data["CPI_prev"])
        real_rate = MacroFormulas.real_interest_rate(data["FEDFUNDS"], inflation)
        yield_spread = MacroFormulas.yield_curve_spread(data["GS10"], data["FEDFUNDS"])
        recession_prob = MacroFormulas.recession_probability(yield_spread)
        velocity = MacroFormulas.money_velocity(data["GDP"], data["M2"])
        macro_health = MacroFormulas.macro_health_index(real_rate, yield_spread)

        computed = {
            "Inflation_rate": inflation,
            "Real_interest_rate": real_rate,
            "Yield_curve_spread": yield_spread,
            "Recession_probability": recession_prob,
            "Money_velocity": velocity,
            "Macro_health_index": macro_health,
        }

        result = {"Raw": data, "Computed": computed}
        return result

    def save_to_json(self, result: dict):
        """Сохраняет результат в JSON-файл с отметкой времени."""
        os.makedirs(os.path.join(ROOT_DIR, "data"), exist_ok=True)
        snapshot_path = os.path.join(ROOT_DIR, "data", "fred_snapshot.json")

        timestamp = datetime.utcnow().isoformat()
        snapshot = {"timestamp": timestamp, "data": result}

        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=4, ensure_ascii=False)

        logging.info(f"FRED data snapshot saved: {snapshot_path}")

    def run(self):
        """Метод для запуска как у обычного агента (используется в AgentManager)."""
        try:
            logging.info("FredAgent.run() started")
            result = self.get_macro_data()

            # краткий вывод в консоль
            print("🌍 FredAgent: latest macro snapshot:")
            print("  Raw:")
            for k, v in result["Raw"].items():
                print(f"    {k}: {v}")
            print("  Computed:")
            for k, v in result["Computed"].items():
                print(f"    {k}: {v}")

            # сохраняем в JSON
            self.save_to_json(result)
            print("✅ FredAgent: saved to data/fred_snapshot.json")
            logging.info("FredAgent.run() completed successfully")
        except Exception as e:
            logging.error(f"Error in FredAgent.run(): {e}")
            print(f"❌ FredAgent error: {e}")


if __name__ == "__main__":
    print("📊 Testing FRED Agent with logging & JSON export...\n")
    agent = FredAgent()
    agent.run()
