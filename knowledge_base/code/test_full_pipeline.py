import pandas as pd
import numpy as np
import os
import importlib

print("🚀 Starting full pipeline simulation...")

# ---------- 1️⃣ Попытка импортировать агентов ----------
try:
    from src.trading_ai.agents.manager import AgentManager

except (ImportError, ModuleNotFoundError):
    print("⚠️ AgentManager not found — using dummy manager instead.")

    class AgentManager:
        def run_all(self):
            print("🤖 [Dummy] Running simulated agents: research, cfa, macro, analytics... done!")

# ---------- 2️⃣ Импорт аналитики ----------
from src.trading_ai.analytics.backtester import full_backtest_report, run_strategy_backtest
from src.trading_ai.analytics.statistics import calc_return_stats

# ---------- 3️⃣ Генерация тестовых данных ----------
dates = pd.date_range("2024-01-01", periods=1500, freq="h")
prices = pd.Series(np.cumsum(np.random.randn(len(dates))) + 100, index=dates)
df = pd.DataFrame({"Close": prices})
df["signal"] = (df["Close"] > df["Close"].rolling(48).mean()).astype(int)

# ---------- 4️⃣ Запуск агентов ----------
manager = AgentManager()
manager.run_all()

# ---------- 5️⃣ Аналитика ----------
print("\n📈 Calculating statistics...")
stats = calc_return_stats(df)
bt = run_strategy_backtest(df, "signal", "Close")
report = full_backtest_report("TEST_CHAIN", df, "signal")

# ---------- 6️⃣ Сохранение ----------
os.makedirs("reports", exist_ok=True)
with open("reports/full_chain_report.txt", "w", encoding="utf-8") as f:
    f.write(report)

print("\n✅ Full pipeline executed successfully!")
print("📁 Report saved: reports/full_chain_report.txt")
