from trading_ai.core.orchestrator import run_full_pipeline


def process_trading_signal(signal: dict) -> dict:
    """
    Получает сигнал TradingView → вызывает твоих CrewAI агентов →
    возвращает готовый текст для Telegram.
    """

    print("📩 Received Signal:", signal)

    # Передаём сигнал твоему intelligence pipeline
    result = run_full_pipeline(
        override_instrument=signal.get("symbol"),
        override_direction=signal.get("direction"),
        override_price=signal.get("price"),
        source="TradingView"
    )

    formatted = {
        "header": f"🔔 SIGNAL FROM TRADINGVIEW ({signal.get('symbol')})",
        "direction": signal.get("direction"),
        "price": signal.get("price"),
        "ai_summary": result.get("summary"),
        "backtest": result.get("backtest"),
    }

    return formatted
