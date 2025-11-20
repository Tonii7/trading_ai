"""
macro_fast.py — лёгкая версия формул для быстрого анализа.
Используется Signal Generator, Backtester и краткосрочные агенты.
"""

from dataclasses import dataclass

@dataclass
class MacroFast:
    @staticmethod
    def real_interest_rate(nominal_rate: float, inflation_rate: float) -> float:
        """Реальная ставка: nominal - inflation"""
        return round(nominal_rate - inflation_rate, 2)

    @staticmethod
    def yield_curve_spread(short_rate: float, long_rate: float) -> float:
        """Разница доходностей: long - short"""
        return round(long_rate - short_rate, 2)

    @staticmethod
    def recession_probability(spread: float) -> float:
        """Эвристика вероятности рецессии"""
        if spread >= 1.0:
            return 5.0
        if 0.0 <= spread < 1.0:
            return 15.0
        if -0.5 <= spread < 0.0:
            return 25.0
        if -1.0 <= spread < -0.5:
            return 40.0
        return 60.0
