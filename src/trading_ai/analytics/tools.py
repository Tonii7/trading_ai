# src/trading_ai/analytics/tools.py

from typing import Dict, Any
import pandas as pd

from src.trading_ai.analytics.statistics import (
    calc_return_stats,
    add_basic_indicators,
    detect_volume_spikes,
    correlation_matrix_from_dict,
)
from src.trading_ai.analytics.backtester import (
    full_backtest_report,
    analyze_time_patterns,
)

def analyze_asset_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Высокоуровневая функция: по одному активу считает:
    - базовые индикаторы
    - статистику доходности
    - аномалии объёма
    - временные паттерны
    """
    # 1. Индикаторы
    df_with_ind = add_basic_indicators(df.copy())

    # 2. Статистика доходности
    stats = calc_return_stats(df_with_ind["Close"])

    # 3. Аномалии объёма
    spikes = None
    if "Volume" in df_with_ind.columns:
        spikes = detect_volume_spikes(df_with_ind)

    # 4. Время (день/час/месяц)
    patterns = analyze_time_patterns(df_with_ind)

    return {
        "indicators_df": df_with_ind,
        "stats": stats,
        "volume_spikes": spikes,
        "time_patterns": patterns,
    }

def run_full_backtest_for_agent(df: pd.DataFrame, strategy_name: str = "default") -> str:
    """
    Готовит текстовый отчёт бэктеста для агента (использует full_backtest_report).
    """
    report = full_backtest_report(df, strategy_name=strategy_name)
    return report

def compute_correlation_for_assets(data_dict: Dict[str, pd.DataFrame]) -> Any:
    """
    Строит матрицу корреляций по нескольким активам.
    """
    return correlation_matrix_from_dict(data_dict)
