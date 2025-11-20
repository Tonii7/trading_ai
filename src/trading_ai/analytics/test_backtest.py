import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from src.trading_ai.analytics.backtester import full_backtest_report, run_strategy_backtest, analyze_time_patterns

# 1️⃣ Генерация данных
dates = pd.date_range("2024-01-01", periods=1000, freq="h")
prices = pd.Series(np.cumsum(np.random.randn(len(dates))) + 100, index=dates)

# 2️⃣ DataFrame
df = pd.DataFrame({"Close": prices})

# 3️⃣ Простая стратегия: long если цена выше 24-часовой средней
df["signal"] = (df["Close"] > df["Close"].rolling(24).mean()).astype(int)

# 4️⃣ Отчёт
report = full_backtest_report("TEST_ASSET", df, "signal")
print(report)

# 5️⃣ Equity curve
bt_res = run_strategy_backtest(df, "signal", "Close")

plt.figure(figsize=(10, 5))
plt.plot(bt_res.equity_curve.index, bt_res.equity_curve.values)
plt.title("📈 Equity Curve — TEST_ASSET Strategy")
plt.xlabel("Date")
plt.ylabel("Equity (USD)")
plt.grid(True)
plt.show()

# 6️⃣ Гистограмма дневных доходностей
df["returns"] = df["Close"].pct_change() * 100
plt.figure(figsize=(8, 5))
plt.hist(df["returns"].dropna(), bins=50, edgecolor="k", alpha=0.7)
plt.title("📊 Distribution of Daily Returns — TEST_ASSET")
plt.xlabel("Daily return (%)")
plt.ylabel("Frequency")
plt.grid(True)
plt.show()

# 7️⃣ Heatmap сезонности (месяц vs день недели)
df["day"] = df.index.dayofweek
df["month"] = df.index.month
pivot = df.pivot_table(values="returns", index="day", columns="month", aggfunc="mean")

plt.figure(figsize=(10, 6))
sns.heatmap(pivot, cmap="RdYlGn", center=0, annot=True, fmt=".2f")
plt.title("🌡️ Seasonality Heatmap (Mean Return %)")
plt.xlabel("Month")
plt.ylabel("Day of Week (0=Mon)")
plt.show()

# 8️⃣ Подсказка по функциям
print("\n🧩 ДОСТУПНЫЕ ФУНКЦИИ:\n")
print("full_backtest_report(df, signal_col)  — полный отчёт со всеми метриками и паттернами")
print("run_strategy_backtest(df, signal_col) — объект BacktestResult с equity curve и drawdown")
print("analyze_time_patterns(df)             — анализ по дням недели, месяцам, часам")
print("calc_return_stats(df)                 — метрики buy & hold")
print("simple_signal_backtest(df)            — быстрый бэктест сигналов без отчёта")
print("day_of_week_performance(df)           — статистика по дням недели")
print("hour_of_day_performance(df)           — статистика по часам")
print("month_of_year_performance(df)         — статистика по месяцам")
