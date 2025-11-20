from __future__ import annotations

import os
from typing import Dict

from fredapi import Fred

from trading_ai.formulas.macro import MacroFormulas


def get_fred_client() -> Fred:
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise ValueError("FRED_API_KEY is not set in .env")
    return Fred(api_key=api_key)


def get_macro_data() -> Dict[str, float]:
    """
    Пример: тянем несколько базовых серий FRED и считаем макропоказатели.
    """
    fred = get_fred_client()

    # Коды серий FRED (примерные, ты можешь менять под себя)
    cpi = fred.get_series_latest_release("CPIAUCSL")      # CPI
    unrate = fred.get_series_latest_release("UNRATE")     # Unemployment
    dgs10 = fred.get_series_latest_release("DGS10")       # 10Y yield
    dgs2 = fred.get_series_latest_release("DGS2")         # 2Y yield
    fedfunds = fred.get_series_latest_release("FEDFUNDS") # Fed Funds
    m2 = fred.get_series_latest_release("WM2NS")          # M2

    # Приводим к числам
    data = {
        "cpi": float(cpi.iloc[-1]),
        "unemployment": float(unrate.iloc[-1]),
        "yield_10y": float(dgs10.iloc[-1]),
        "yield_2y": float(dgs2.iloc[-1]),
        "fed_funds": float(fedfunds.iloc[-1]),
        "m2": float(m2.iloc[-1]),
    }

    # Макроформулы
    real_rate = MacroFormulas.real_interest_rate(
        nominal_rate=data["yield_10y"], inflation_rate=data["cpi"] / 100.0
    )
    spread = MacroFormulas.yield_curve_spread(
        short_rate=data["yield_2y"], long_rate=data["yield_10y"]
    )
    recession_prob = MacroFormulas.recession_probability(spread)

    data.update(
        {
            "real_rate": real_rate,
            "yield_spread": spread,
            "recession_prob": recession_prob,
        }
    )
    return data


if __name__ == "__main__":
    print("📊 Testing FRED connection...")
    macro = get_macro_data()
    for k, v in macro.items():
        print(f"{k}: {round(v, 3)}")
