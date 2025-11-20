"""
range_breakout_ea.py — Range Breakout Strategy (cTrader Integration)
--------------------------------------------------------------------
✅ Использует реальные данные из cTrader API
✅ Автоматический анализ и отчёт для orchestrator.py
✅ Работает с M15 таймфреймом (можно изменить)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from trading_ai.connectors.ctrader_connector import CTraderConnector

# === ПАРАМЕТРЫ СТРАТЕГИИ ===
SYMBOL = "US30"
TIMEFRAME = "M15"
BARS = 500
RANGE_HOURS = (14, 19)        # диапазон накопления
BREAKOUT_HOUR = 19.5           # 19:30
TP_MULT = 1.5
SL_MULT = 0.5
LOT_SIZE = 0.1


def main():
    print("📈 Загрузка данных из cTrader...")
    ctrader = CTraderConnector()
    data = ctrader.get_historical_data(SYMBOL, timeframe=TIMEFRAME, bars=BARS)

    if data is None or data.empty:
        print("⚠ Нет данных из cTrader, стратегия пропущена.")
        return {
            "symbol": SYMBOL,
            "total_trades": 0,
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "comment_ru": "Нет данных от брокера, рынок закрыт или API недоступен."
        }

    # === Расчёт стратегии ===
    trades = []
    open_trade = None
    range_high = None
    range_low = None

    for ts, row in data.iterrows():
        hour = ts.hour + ts.minute / 60

        # Диапазон накопления
        if RANGE_HOURS[0] <= hour < RANGE_HOURS[1]:
            range_high = row["high"] if range_high is None else max(range_high, row["high"])
            range_low = row["low"] if range_low is None else min(range_low, row["low"])

        # Пробой
        elif hour >= BREAKOUT_HOUR and range_high and range_low and open_trade is None:
            range_size = range_high - range_low
            buy_level = range_high
            sell_level = range_low
            tp_buy = buy_level + range_size * TP_MULT
            sl_buy = buy_level - range_size * SL_MULT
            tp_sell = sell_level - range_size * TP_MULT
            sl_sell = sell_level + range_size * SL_MULT

            if row["high"] >= buy_level:
                open_trade = {"type": "BUY", "entry": buy_level, "tp": tp_buy, "sl": sl_buy, "entry_time": ts}
            elif row["low"] <= sell_level:
                open_trade = {"type": "SELL", "entry": sell_level, "tp": tp_sell, "sl": sl_sell, "entry_time": ts}

        # Проверяем закрытие сделки
        if open_trade:
            if open_trade["type"] == "BUY":
                if row["low"] <= open_trade["sl"]:
                    trades.append({"result": open_trade["sl"] - open_trade["entry"]})
                    open_trade = None
                elif row["high"] >= open_trade["tp"]:
                    trades.append({"result": open_trade["tp"] - open_trade["entry"]})
                    open_trade = None
            elif open_trade["type"] == "SELL":
                if row["high"] >= open_trade["sl"]:
                    trades.append({"result": open_trade["entry"] - open_trade["sl"]})
                    open_trade = None
                elif row["low"] <= open_trade["tp"]:
                    trades.append({"result": open_trade["entry"] - open_trade["tp"]})
                    open_trade = None

    # === Результаты ===
    if not trades:
        return {
            "symbol": SYMBOL,
            "total_trades": 0,
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "comment_ru": "Пробой не произошёл. Нейтральный день на рынке."
        }

    df = pd.DataFrame(trades)
    df["pnl"] = df["result"] * LOT_SIZE * 100
    total_pnl = round(df["pnl"].sum(), 2)
    win_rate = round((df["pnl"] > 0).mean() * 100, 1)

    comment = (
        f"📊 За период протестировано {len(df)} сделок. "
        f"Итоговая прибыль: {total_pnl}$, винрейт {win_rate}%. "
        f"Рынок {'бычий' if total_pnl > 0 else 'медвежий'} на отрезке {TIMEFRAME}."
    )

    return {
        "symbol": SYMBOL,
        "total_trades": len(df),
        "total_pnl": total_pnl,
        "win_rate": win_rate,
        "comment_ru": comment
    }


if __name__ == "__main__":
    result = main()
    print(result)
