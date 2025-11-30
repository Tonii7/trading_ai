import datetime
from typing import Dict, Any

# здесь позже подключим твои реальные функции cTrader
# из src/trading_ai/services/ctrader/*.py


def build_index_snapshot() -> str:
    """
    Собирает краткий снэпшот по индексам для NY-сессии.
    На этом этапе каркас: пока без реальных запросов, но строго
    запрещаем выдумывать цены внутри Crew – вся конкретика будет отсюда.
    """

    # TODO: здесь ты позже подключишь реальные данные из cTrader:
    # us30 = get_us30_data_from_ctrader(...)
    # sp500 = get_sp500_data_from_ctrader(...)
    # nas100 = get_nas100_data_from_ctrader(...)

    # Временно – только структура, без цифр:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    snapshot_lines = [
        f"NY session pre-open snapshot (generated {now}):",
        "",
        "US30:",
        "- Текущее направление: [укажи по H1/H4]",
        "- Диапазон Азии: [Asia high/low]",
        "- Диапазон Европы: [EU high/low]",
        "",
        "S&P500:",
        "- Текущее направление: [укажи по H1/H4]",
        "- Диапазон Азии: [Asia high/low]",
        "- Диапазон Европы: [EU high/low]",
        "",
        "NAS100:",
        "- Текущее направление: [укажи по H1/H4]",
        "- Диапазон Азии: [Asia high/low]",
        "- Диапазон Европы: [EU high/low]",
        "",
        "Макро / новости:",
        "- [ключевые события дня: FOMC, CPI, earnings, etc.]",
        "",
        "Важно: уровни и цены НЕ выдумывать в CrewAI, "
        "а подставлять отсюда, когда появятся реальные данные.",
    ]

    return "\n".join(snapshot_lines)
