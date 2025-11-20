# src/trading_ai/formulas/macro.py
"""
📘 macro.py — модуль с формулами для макроэкономического анализа.
Его используют агенты (например, FRED агент, Market Analyzer).
"""

import math

class MacroFormulas:
    """Сборник формул и индикаторов для анализа макроэкономических данных."""

    @staticmethod
    def inflation_rate(current_cpi, previous_cpi):
        """Темп инфляции, %"""
        if not previous_cpi or previous_cpi == 0:
            return None
        return round(((current_cpi - previous_cpi) / previous_cpi) * 100, 2)

    @staticmethod
    def real_interest_rate(nominal_rate, inflation_rate):
        """Реальная ставка (Фишера): nominal - inflation"""
        if inflation_rate is None:
            return None
        return round(nominal_rate - inflation_rate, 2)

    @staticmethod
    def yield_curve_spread(yield_10y, fed_funds):
        """Разница между доходностью 10-летних облигаций и ставкой ФРС"""
        if yield_10y is None or fed_funds is None:
            return None
        return round(yield_10y - fed_funds, 2)

    @staticmethod
    def recession_probability(yield_spread):
        """Простая модель вероятности рецессии"""
        if yield_spread is None:
            return None
        # если инверсия — риск рецессии возрастает
        if yield_spread < 0:
            return min(100, round(abs(yield_spread) * 25, 1))
        return 0

    @staticmethod
    def money_velocity(gdp, m2_supply):
        """Скорость обращения денег = ВВП / М2"""
        if not m2_supply or m2_supply == 0:
            return None
        return round(gdp / m2_supply, 3)

    @staticmethod
    def liquidity_index(m2_growth, rate_diff):
        """Индекс ликвидности: совмещает рост денежной массы и ставку"""
        try:
            score = m2_growth - (rate_diff * 2)
            return round(score, 2)
        except Exception:
            return None

    @staticmethod
    def pmi_composite(manufacturing, services):
        """Средневзвешенный PMI"""
        if manufacturing is None or services is None:
            return None
        return round((manufacturing * 0.6 + services * 0.4), 2)

    @staticmethod
    def macro_health_index(real_rate, yield_spread):
        """Общий индекс здоровья экономики"""
        if real_rate is None or yield_spread is None:
            return None
        return round((real_rate + yield_spread) / 2, 2)
