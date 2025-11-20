# ==============================================
# src/trading_ai/analytics/backtester.py
# Расширенный бэктест и анализ паттернов:
# - day of week / hour of day / month of year
# - обёртка над simple_signal_backtest
# ==============================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd

# ✅ корректный импорт — путь начинается с src, как в твоей структуре проекта
from src.trading_ai.analytics.statistics import (
    simple_signal_backtest,
    calc_return_stats,
    ensure_datetime_index,
    BacktestResult,
)


# ---------- Вспомогательные структуры ----------
@dataclass
class TimePatternAnalysis:
    day_of_week: pd.DataFrame
    hour_of_day: Optional[pd.DataFrame]
    month_of_year: pd.DataFrame


# ---------- Вспомогательные функции ----------
def _returns_from_prices(df: pd.DataFrame, price_col: str = "Close") -> pd.Series:
    df = ensure_datetime_index(df)
    return df[price_col].pct_change().dropna()


def day_of_week_performance(df: pd.DataFrame, price_col: str = "Close") -> pd.DataFrame:
    rets = _returns_from_prices(df, price_col)
    dow = rets.index.dayofweek
    grp = rets.groupby(dow)
    stats = pd.DataFrame({
        "mean_ret": grp.mean(),
        "std_ret": grp.std(),
        "count": grp.count(),
        "win_rate": grp.apply(lambda x: (x > 0).sum()) / grp.count(),
    })
    stats["mean_ret_pct"] = stats["mean_ret"] * 100
    stats["std_ret_pct"] = stats["std_ret"] * 100
    stats["win_rate_pct"] = stats["win_rate"] * 100
    stats = stats.sort_values("mean_ret", ascending=False)
    stats.index.name = "day_of_week"
    return stats


def hour_of_day_performance(df: pd.DataFrame, price_col: str = "Close") -> Optional[pd.DataFrame]:
    df = ensure_datetime_index(df)
    if not isinstance(df.index, pd.DatetimeIndex):
        return None

    hours = df.index.hour
    if len(set(hours)) <= 1:
        return None

    rets = df[price_col].pct_change().dropna()
    grp = rets.groupby(rets.index.hour)
    stats = pd.DataFrame({
        "mean_ret": grp.mean(),
        "std_ret": grp.std(),
        "count": grp.count(),
        "win_rate": grp.apply(lambda x: (x > 0).sum()) / grp.count(),
    })
    stats["mean_ret_pct"] = stats["mean_ret"] * 100
    stats["std_ret_pct"] = stats["std_ret"] * 100
    stats["win_rate_pct"] = stats["win_rate"] * 100
    stats = stats.sort_values("mean_ret", ascending=False)
    stats.index.name = "hour"
    return stats


def month_of_year_performance(df: pd.DataFrame, price_col: str = "Close") -> pd.DataFrame:
    rets = _returns_from_prices(df, price_col)
    grp = rets.groupby(rets.index.month)
    stats = pd.DataFrame({
        "mean_ret": grp.mean(),
        "std_ret": grp.std(),
        "count": grp.count(),
        "win_rate": grp.apply(lambda x: (x > 0).sum()) / grp.count(),
    })
    stats["mean_ret_pct"] = stats["mean_ret"] * 100
    stats["std_ret_pct"] = stats["std_ret"] * 100
    stats["win_rate_pct"] = stats["win_rate"] * 100
    stats = stats.sort_values("mean_ret", ascending=False)
    stats.index.name = "month"
    return stats


def analyze_time_patterns(df: pd.DataFrame, price_col: str = "Close") -> TimePatternAnalysis:
    df = ensure_datetime_index(df)
    return TimePatternAnalysis(
        day_of_week=day_of_week_performance(df, price_col),
        hour_of_day=hour_of_day_performance(df, price_col),
        month_of_year=month_of_year_performance(df, price_col),
    )


def summarize_time_patterns(name: str, patterns: TimePatternAnalysis) -> str:
    lines = [f"⏱ Time pattern analysis for {name}"]

    # День недели
    dow = patterns.day_of_week
    if not dow.empty:
        best_dow_idx = int(dow.index[0])
        best_dow = dow.iloc[0]
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        dow_name = day_names[best_dow_idx] if 0 <= best_dow_idx < len(day_names) else str(best_dow_idx)
        lines.append(f"- Best day: {dow_name} ({best_dow['mean_ret_pct']:.2f}% mean, win {best_dow['win_rate_pct']:.1f}%)")

    # Месяц
    moy = patterns.month_of_year
    if not moy.empty:
        best_m_idx = int(moy.index[0])
        best_m = moy.iloc[0]
        lines.append(f"- Best month: {best_m_idx} ({best_m['mean_ret_pct']:.2f}% mean, win {best_m['win_rate_pct']:.1f}%)")

    # Час
    if patterns.hour_of_day is not None and not patterns.hour_of_day.empty:
        hod = patterns.hour_of_day
        best_h_idx = int(hod.index[0])
        best_h = hod.iloc[0]
        lines.append(f"- Best hour: {best_h_idx}:00 ({best_h['mean_ret_pct']:.2f}% mean, win {best_h['win_rate_pct']:.1f}%)")
    else:
        lines.append("- No intraday data detected")

    return "\n".join(lines)


# ---------- Основная логика ----------
def run_strategy_backtest(df: pd.DataFrame, signal_col: str, price_col: str = "Close",
                          initial_balance: float = 100_000.0, fee_per_trade: float = 0.0) -> BacktestResult:
    df = ensure_datetime_index(df)
    if signal_col not in df.columns:
        raise ValueError(f"Signal column '{signal_col}' not found in DataFrame.")
    return simple_signal_backtest(df, signal_col, price_col, initial_balance, fee_per_trade)


def full_backtest_report(name: str, df: pd.DataFrame, signal_col: str,
                         price_col: str = "Close", initial_balance: float = 100_000.0,
                         fee_per_trade: float = 0.0) -> str:
    df = ensure_datetime_index(df)
    base_stats = calc_return_stats(df, price_col=price_col)
    bt_res = run_strategy_backtest(df, signal_col, price_col, initial_balance, fee_per_trade)
    patterns = analyze_time_patterns(df, price_col)
    time_txt = summarize_time_patterns(name, patterns)

    lines = [f"📑 Backtest report for {name}"]
    lines.append("")
    lines.append("=== Asset base performance (buy & hold) ===")
    lines.append(f"- Total return: {base_stats.total_return:.2f}%")
    lines.append(f"- Annual return: {base_stats.annual_return:.2f}%")
    lines.append(f"- Annual volatility: {base_stats.annual_vol:.2f}%")
    lines.append(f"- Sharpe (approx): {base_stats.sharpe:.2f}")
    lines.append("")
    lines.append("=== Strategy performance (signals) ===")
    lines.append(f"- Initial balance: {bt_res.initial_balance:.2f}")
    lines.append(f"- Final balance: {bt_res.final_balance:.2f}")
    lines.append(f"- Total return: {bt_res.total_return_pct:.2f}%")
    lines.append(f"- Max drawdown: {bt_res.max_drawdown_pct:.2f}%")
    lines.append("")
    lines.append("=== Time patterns ===")
    lines.append(time_txt)

    return "\n".join(lines)


if __name__ == "__main__":
    dates = pd.date_range("2024-01-01", periods=500, freq="H")
    prices = pd.Series(np.cumsum(np.random.randn(len(dates))) + 100, index=dates)
    df = pd.DataFrame({"Close": prices})
    df["signal"] = (df["Close"] > df["Close"].rolling(24).mean()).astype(int)
    print(full_backtest_report("TEST_ASSET", df, "signal"))
