# run_full_market_report.py
"""
Полный сценарий:
1) Запуск всех агентов (включая FredAgent, Supervisor & co)
2) (Опционально) запуск тестового бэктеста
3) Сбор единого HTML-отчёта (macro + agents + backtest + glossary)
"""

import os
from pathlib import Path

import pandas as pd
import numpy as np

from src.trading_ai.agents.manager import AgentManager
from src.trading_ai.analytics.backtester import full_backtest_report, run_strategy_backtest
from src.trading_ai.analytics.statistics import calc_return_stats
from src.trading_ai.reports.full_report import build_full_market_report, save_full_market_report


ROOT_DIR = Path(__file__).resolve().parent
REPORTS_DIR = ROOT_DIR / "reports"


def run_backtest_and_save() -> Path:
    """Запускает тестовый бэктест и сохраняет результат в reports/full_chain_report.txt"""
    REPORTS_DIR.mkdir(exist_ok=True)

    dates = pd.date_range("2024-01-01", periods=1500, freq="h")
    prices = pd.Series(np.cumsum(np.random.randn(len(dates))) + 100, index=dates)
    df = pd.DataFrame({"Close": prices})
    df["signal"] = (df["Close"] > df["Close"].rolling(48).mean()).astype(int)

    stats = calc_return_stats(df)
    bt = run_strategy_backtest(df, "signal", "Close")
    report = full_backtest_report("TEST_CHAIN", df, "signal")

    out_path = REPORTS_DIR / "full_chain_report.txt"
    with out_path.open("w", encoding="utf-8") as f:
        f.write(report)

    print(f"📄 Backtest report saved to: {out_path}")
    return out_path


def main():
    print("🚀 Full day pipeline: agents + backtest + HTML report")

    # 1) Агенты
    try:
        manager = AgentManager()
        manager.run_all()
    except Exception as e:
        print(f"⚠️ AgentManager error (продолжаем без остановки): {e}")

    # 2) Бэктест (пока синтетический; позже подставим реальные данные)
    bt_path = run_backtest_and_save()

    # 3) Сбор HTML-отчёта
    html = build_full_market_report(
        market_name="US30 / XAUUSD / SPX500",
        backtest_report_path=bt_path,
    )
    out_html = save_full_market_report(html)

    print(f"\n✅ Full market HTML report ready: {out_html}")
    print("Открой этот файл в браузере (двойной клик в проводнике).")


if __name__ == "__main__":
    main()
