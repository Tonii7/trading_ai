import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from src.trading_ai.analytics.backtester import run_strategy_backtest
from src.trading_ai.analytics.statistics import calc_return_stats
from src.trading_ai.analytics.report_definitions import METRIC_DEFINITIONS

# ---------- 1️⃣ Подготовка ----------
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

# ---------- 2️⃣ Генерация данных (синтетика, потом заменим на реальные фиды) ----------
dates = pd.date_range("2024-01-01", periods=1500, freq="h")
prices = pd.Series(np.cumsum(np.random.randn(len(dates))) + 100, index=dates)
df = pd.DataFrame({"Close": prices})

# ---------- 3️⃣ Определение стратегий ----------
strategies = {
    "MA_24": (df["Close"] > df["Close"].rolling(24).mean()).astype(int),
    "MA_72": (df["Close"] > df["Close"].rolling(72).mean()).astype(int),
    "MA_168": (df["Close"] > df["Close"].rolling(168).mean()).astype(int),
}

# ---------- 4️⃣ Запуск тестов ----------
results = []

for name, signal in strategies.items():
    df["signal"] = signal
    bt = run_strategy_backtest(df, "signal", "Close")
    base_stats = calc_return_stats(df)

    results.append(
        {
            "Strategy": name,
            "Total Return %": bt.total_return_pct,
            "Max Drawdown %": bt.max_drawdown_pct,
            "Final Balance": bt.final_balance,
            "Sharpe": base_stats.sharpe,
        }
    )

# ---------- 5️⃣ Таблица результатов ----------
res_df = pd.DataFrame(results).sort_values("Total Return %", ascending=False)

print("\n📊 Strategy Comparison Results:\n")
print(res_df.to_string(index=False))

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# ---------- 6️⃣ Сохранение CSV ----------
csv_path = os.path.join(REPORTS_DIR, f"strategy_comparison_{timestamp}.csv")
res_df.to_csv(csv_path, index=False)
print(f"\n💾 CSV report saved to: {csv_path}")

# ---------- 7️⃣ HTML-отчёт с цветами ----------

def highlight_best_worst(col: pd.Series):
    styles = [""] * len(col)
    if col.dtype.kind in "if":
        max_val = col.max()
        min_val = col.min()
        for i, v in enumerate(col):
            if v == max_val:
                styles[i] = "background-color: #c6efce; color: #006100;"  # зелёный
            elif v == min_val:
                styles[i] = "background-color: #ffc7ce; color: #9c0006;"  # красный
    return styles

styled = res_df.style.apply(highlight_best_worst, axis=0)

html_path = os.path.join(REPORTS_DIR, f"strategy_comparison_{timestamp}.html")
styled.to_html(html_path, justify="center")
print(f"🌐 HTML report saved to: {html_path}")

# ---------- 8️⃣ Добавляем описания метрик ----------
html_definitions = "<h2>📘 Metric Definitions</h2><ul>"
for metric, desc in METRIC_DEFINITIONS.items():
    html_definitions += f"<li><b>{metric}</b>: {desc}</li>"
html_definitions += "</ul>"

with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()
html_content += html_definitions

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print("🧾 Added metric definitions to HTML report.")

# ---------- 9️⃣ Логирование отчётов ----------
history_path = os.path.join(REPORTS_DIR, "history.json")

entry = {
    "timestamp": timestamp,
    "strategies": list(strategies.keys()),
    "results": res_df.to_dict(orient="records"),
    "report_paths": {
        "csv": csv_path,
        "html": html_path,
    },
}

if os.path.exists(history_path):
    with open(history_path, "r", encoding="utf-8") as f:
        history = json.load(f)
else:
    history = []

history.append(entry)

with open(history_path, "w", encoding="utf-8") as f:
    json.dump(history, f, indent=4, ensure_ascii=False)

print(f"📚 Report logged to history.json ({len(history)} total entries).")

# ---------- 🔟 Визуализация equity curves ----------
plt.figure(figsize=(10, 5))
for name, signal in strategies.items():
    df["signal"] = signal
    bt = run_strategy_backtest(df, "signal", "Close")
    plt.plot(bt.equity_curve.index, bt.equity_curve.values, label=name)

plt.title("📈 Strategy Comparison — Equity Curves")
plt.xlabel("Date")
plt.ylabel("Equity (USD)")
plt.legend()
plt.grid(True)

png_path = os.path.join(REPORTS_DIR, f"equity_curves_{timestamp}.png")
plt.savefig(png_path, dpi=300, bbox_inches="tight")
plt.show()
print(f"🖼️ Equity chart saved to: {png_path}")
