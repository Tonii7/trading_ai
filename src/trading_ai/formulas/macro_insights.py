"""
macro_insights.py — модуль интерпретации макроэкономических данных.
Объединяет результаты из macro.py и macro_fast.py, формируя текстовые выводы.
Используется Supervisor, CFA Agent и Macro Strategist.
"""

from src.trading_ai.formulas.macro import MacroFormulas
from src.trading_ai.formulas.macro_fast import MacroFast

class MacroInsights:
    """Генератор текстовых выводов по макроданным."""

    @staticmethod
    def describe_economy(data: dict) -> str:
        """
        Принимает словарь данных от FRED или агента (например):
        {
            "cpi": 324.3,
            "prev_cpi": 320.2,
            "nominal_rate": 5.25,
            "inflation_rate": 3.1,
            "yield_10y": 4.5,
            "fed_funds": 5.0,
            "m2_supply": 22212.5,
            "gdp": 28500.0
        }
        Возвращает аналитический текст.
        """

        cpi_growth = MacroFormulas.inflation_rate(data.get("cpi"), data.get("prev_cpi"))
        real_rate = MacroFormulas.real_interest_rate(data.get("nominal_rate"), data.get("inflation_rate"))
        yield_spread = MacroFormulas.yield_curve_spread(data.get("yield_10y"), data.get("fed_funds"))
        recession_risk = MacroFast.recession_probability(yield_spread)
        velocity = MacroFormulas.money_velocity(data.get("gdp"), data.get("m2_supply"))

        insights = []

        # --- Inflation
        if cpi_growth is not None:
            if cpi_growth > 4:
                insights.append(f"📈 Инфляция ускоряется ({cpi_growth}%), что может усилить давление на ФРС.")
            elif cpi_growth < 2:
                insights.append(f"🧊 Инфляция низкая ({cpi_growth}%), что создаёт пространство для смягчения политики.")
            else:
                insights.append(f"⚖️ Инфляция стабильна на уровне {cpi_growth}%.")

        # --- Real rates
        if real_rate is not None:
            if real_rate > 2:
                insights.append(f"💰 Реальные ставки высокие ({real_rate}%), что снижает стимулы к заимствованию.")
            elif real_rate < 0:
                insights.append(f"🔥 Отрицательные реальные ставки ({real_rate}%) поддерживают спрос и активы.")
            else:
                insights.append(f"🏦 Реальная ставка сбалансирована ({real_rate}%).")

        # --- Yield curve
        if yield_spread is not None:
            if yield_spread < 0:
                insights.append(f"⚠️ Кривая доходности инвертирована ({yield_spread}%), сигнал возможной рецессии.")
            else:
                insights.append(f"✅ Нормальная кривая доходности ({yield_spread}%).")

        # --- Recession probability
        if recession_risk is not None:
            if recession_risk > 40:
                insights.append(f"🚨 Вероятность рецессии оценивается в {recession_risk}%.")
            elif recession_risk > 15:
                insights.append(f"⚠️ Умеренный риск рецессии ({recession_risk}%).")
            else:
                insights.append(f"🟢 Риск рецессии низкий ({recession_risk}%).")

        # --- Money velocity
        if velocity is not None:
            if velocity < 1.2:
                insights.append(f"💤 Скорость обращения денег ({velocity}) указывает на слабую экономическую активность.")
            elif velocity > 1.8:
                insights.append(f"🚀 Высокая скорость обращения денег ({velocity}) сигнализирует о росте деловой активности.")
            else:
                insights.append(f"⚙️ Денежное обращение стабильное ({velocity}).")

        if not insights:
            insights.append("Нет достаточно данных для анализа макроэкономической ситуации.")

        return "\n".join(insights)
