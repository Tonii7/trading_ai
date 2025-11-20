# ==============================================
# src/trading_ai/agents/backtester_agent.py
# BacktesterAgent — служебный агент для прогонки стратегий
# и анализа паттернов времени.
# ==============================================

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from trading_ai.analytics.backtester import full_backtest_report
from trading_ai.analytics.statistics import ensure_datetime_index


@dataclass
class BacktesterConfig:
    initial_balance: float = 100_000.0
    fee_per_trade: float = 0.0  # можно позже задать реальную комиссию
    price_col: str = "Close"
    signal_col: str = "signal"


class BacktesterAgent:
    """
    Агент-бэктестер.
    Его задача:
      - взять данные по инструменту (CSV / DataFrame),
      - найти колонку сигналов (signal_col),
      - запустить backtest+time-analysis,
      - выдать текстовый отчёт и (опционально) сохранить его в файл.
    """

    def __init__(self, config: Optional[BacktesterConfig] = None):
        self.config = config or BacktesterConfig()

    def load_csv(self, path: str) -> pd.DataFrame:
        if not os.path.exists(path):
            raise FileNotFoundError(f"CSV file not found: {path}")
        df = pd.read_csv(path, parse_dates=True)
        # Попробуем привести индекс к дате, если есть колонка "Date" или "datetime"
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date")
        elif "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.set_index("datetime")
        return ensure_datetime_index(df)

    def run_on_dataframe(self, name: str, df: pd.DataFrame) -> str:
        df = ensure_datetime_index(df)
        if self.config.signal_col not in df.columns:
            raise ValueError(
                f"DataFrame must contain signal column '{self.config.signal_col}'."
            )

        report = full_backtest_report(
            name=name,
            df=df,
            signal_col=self.config.signal_col,
            price_col=self.config.price_col,
            initial_balance=self.config.initial_balance,
            fee_per_trade=self.config.fee_per_trade,
        )
        return report

    def run_on_csv(self, name: str, csv_path: str, save_report: bool = True) -> str:
        df = self.load_csv(csv_path)
        report = self.run_on_dataframe(name, df)

        if save_report:
            # сохраняем в папку reports/
            base_dir = os.path.dirname(os.path.dirname(__file__))  # src/trading_ai
            project_root = os.path.dirname(base_dir)               # trading_ai/
            reports_dir = os.path.join(project_root, "reports")
            os.makedirs(reports_dir, exist_ok=True)

            out_path = os.path.join(reports_dir, f"backtest_{name}.txt")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"💾 Backtest report saved to: {out_path}")

        return report


if __name__ == "__main__":
    # Пример использования:
    agent = BacktesterAgent()
    # Ожидаем, что у тебя есть CSV вида:
    # Date,Open,High,Low,Close,Volume,signal
    example_csv = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "..",
        "data",
        "example_us30_signals.csv"
    )

    if os.path.exists(example_csv):
        txt = agent.run_on_csv("US30_example", example_csv)
        print(txt)
    else:
        print("⚠️ Example CSV not found. Place a file at data/example_us30_signals.csv.")
