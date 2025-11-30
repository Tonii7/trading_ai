"""
market_snapshot.py — FULL Market Engine v1 + Candle Engine

Задачи:
- централизованный WATCHLIST по ключевым инструментам
- единый интерфейс получения:
  - snapshot по символу (bid/ask/last/spread/время)
  - набор свечей по символу и таймфрейму

Сейчас:
- по умолчанию используются фейковые данные (заглушки), чтобы всё работало и
  красиво писало в Discord.
- если в .env выставлен CTRADER_ENABLED=1, модуль пытается использовать
  реальные котировки через ctrader_price_source.py

На следующем шаге:
- в ctrader_price_source.py нужно будет добавить реальные вызовы cTrader Open API
  (ProtoOASubscribeSpotsReq, ProtoOAGetTrendbarsReq и т.д.) по документации.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Literal, Optional

# Попытка импортировать источник реальных котировок
try:
    from trading_ai.services.ctrader.ctrader_price_source import (
        get_realtime_snapshot,
        get_realtime_candles,
    )
except Exception:
    # Если что-то пошло не так — просто работаем на фейках
    get_realtime_snapshot = None  # type: ignore
    get_realtime_candles = None  # type: ignore


# ─────────────────────────────────────────────
# 0. Флаг использования cTrader
# ─────────────────────────────────────────────

CTRADER_ENABLED: bool = os.getenv("CTRADER_ENABLED", "0") == "1"


# ─────────────────────────────────────────────
# 1. Наблюдаемый список инструментов
# ─────────────────────────────────────────────

# Ключ — наше внутреннее имя, значение — SYMBOL_NAME в cTrader
WATCHLIST: Dict[str, str] = {
    # Индексы
    "US30": "US30",
    "DE40": "DE40",
    "USTEC": "USTEC",
    "SP500": "SPXUSD",  # у cTrader индекс SPX как SPXUSD

    # Forex
    "EURUSD": "EURUSD",
    "USDJPY": "USDJPY",
    "USDCHF": "USDCHF",
    "GBPUSD": "GBPUSD",

    # Metals / Commodities
    "XAUUSD": "XAUUSD",
    "BRENT": "BRENT",   # если нужно, можно дублировать как XBRUSD
}

# Поддерживаемые таймфреймы
Timeframe = Literal["M5", "M15", "M30", "H1", "H4", "D1"]

CANDLE_TIMEFRAMES: List[Timeframe] = ["M5", "M15", "M30", "H1", "H4", "D1"]


# ─────────────────────────────────────────────
# 2. Модели данных
# ─────────────────────────────────────────────

@dataclass
class SymbolSnapshot:
    symbol_key: str      # наше внутреннее имя, напр. "US30"
    symbol_name: str     # имя у брокера, напр. "US30"
    bid: float
    ask: float
    last: float
    spread: float
    timestamp: datetime


@dataclass
class Candle:
    symbol_key: str
    symbol_name: str
    timeframe: Timeframe
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


# ─────────────────────────────────────────────
# 3. Фейковые данные (заглушки)
# ─────────────────────────────────────────────

def _fake_price(base: float, offset: float) -> float:
    """Временный генератор фейковых цен для отладки."""
    return round(base + offset, 2)


def _fake_symbol_snapshot(symbol_key: str) -> SymbolSnapshot:
    """
    Фейковый snapshot по символу (bid/ask/last/spread).

    Используется:
      - когда CTRADER_ENABLED == 0
      - или когда реальный источник вернул ошибку/None
    """
    symbol_name = WATCHLIST[symbol_key]

    # Простейшая фейковая логика цены
    base_map = {
        "US30": 39000.0,
        "DE40": 18000.0,
        "USTEC": 18000.0,
        "SP500": 5200.0,
        "EURUSD": 1.09,
        "USDJPY": 150.0,
        "USDCHF": 0.90,
        "GBPUSD": 1.26,
        "XAUUSD": 2400.0,
        "BRENT": 80.0,
    }
    base = base_map.get(symbol_key, 100.0)

    last = _fake_price(base, 0.0)
    bid = _fake_price(base, -0.5 if base > 100 else -0.0005)
    ask = _fake_price(base, 0.5 if base > 100 else 0.0005)
    spread = round(ask - bid, 2)

    return SymbolSnapshot(
        symbol_key=symbol_key,
        symbol_name=symbol_name,
        bid=bid,
        ask=ask,
        last=last,
        spread=spread,
        timestamp=datetime.now(timezone.utc),
    )


def _fake_symbol_candles(
    symbol_key: str,
    timeframe: Timeframe,
    limit: int = 50,
) -> List[Candle]:
    """
    Фейковые свечи: лёгкий тренд вверх для отладки.
    """
    symbol_name = WATCHLIST[symbol_key]

    base_snapshot = _fake_symbol_snapshot(symbol_key)
    base_price = base_snapshot.last

    now = datetime.now(timezone.utc)

    tf_to_delta = {
        "M5": timedelta(minutes=5),
        "M15": timedelta(minutes=15),
        "M30": timedelta(minutes=30),
        "H1": timedelta(hours=1),
        "H4": timedelta(hours=4),
        "D1": timedelta(days=1),
    }
    step = tf_to_delta[timeframe]

    candles: List[Candle] = []
    price = base_price - (limit // 2)  # немного в прошлое

    for i in range(limit):
        t = now - step * (limit - 1 - i)
        o = round(price, 2)
        h = round(price + 3, 2)
        l = round(price - 3, 2)
        c = round(price + 1, 2)
        v = 100 + i * 10

        candles.append(
            Candle(
                symbol_key=symbol_key,
                symbol_name=symbol_name,
                timeframe=timeframe,
                time=t,
                open=o,
                high=h,
                low=l,
                close=c,
                volume=v,
            )
        )
        price += 1  # лёгкий тренд вверх

    return candles


# ─────────────────────────────────────────────
# 4. Публичный API: snapshot & candles
# ─────────────────────────────────────────────

def get_symbol_snapshot(symbol_key: str) -> SymbolSnapshot:
    """
    Публичная точка входа:

    - если CTRADER_ENABLED=1 и доступен ctrader_price_source → пытаемся взять
      реальные данные с cTrader;
    - если что-то пошло не так → тихо откатываемся на фейковые данные.
    """
    if symbol_key not in WATCHLIST:
        raise KeyError(f"Unknown symbol_key: {symbol_key}")

    # Путь 1: реальный cTrader
    if CTRADER_ENABLED and get_realtime_snapshot is not None:
        try:
            snap = get_realtime_snapshot(symbol_key)
            if snap is not None:
                return snap
        except Exception as e:
            # Можно здесь писать в system_logs через Discord
            print(f"[market_snapshot] cTrader snapshot error for {symbol_key}: {e}")

    # Путь 2: фейковые данные
    return _fake_symbol_snapshot(symbol_key)


def get_symbol_candles(
    symbol_key: str,
    timeframe: Timeframe,
    limit: int = 50,
) -> List[Candle]:
    """
    Публичная точка входа для свечей:

    - если CTRADER_ENABLED=1 и реализована get_realtime_candles → используем её;
    - иначе → фейковые синтетические свечи.
    """
    if symbol_key not in WATCHLIST:
        raise KeyError(f"Unknown symbol_key: {symbol_key}")
    if timeframe not in CANDLE_TIMEFRAMES:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    # Путь 1: реальные свечи cTrader
    if CTRADER_ENABLED and get_realtime_candles is not None:
        try:
            candles = get_realtime_candles(symbol_key, timeframe, limit=limit)
            if candles:
                return candles
        except Exception as e:
            print(f"[market_snapshot] cTrader candles error for {symbol_key}/{timeframe}: {e}")

    # Путь 2: фейковые свечи
    return _fake_symbol_candles(symbol_key, timeframe, limit=limit)


# ─────────────────────────────────────────────
# 5. Обёртки для всего рынка (FULL Market Snapshot)
# ─────────────────────────────────────────────

def get_full_market_snapshot() -> Dict[str, SymbolSnapshot]:
    """
    Вернуть snapshot по ВСЕМ символам из WATCHLIST.
    """
    return {
        symbol_key: get_symbol_snapshot(symbol_key)
        for symbol_key in WATCHLIST.keys()
    }


def get_full_candles_snapshot(
    timeframes: List[Timeframe] | None = None,
    limit: int = 50,
) -> Dict[str, Dict[Timeframe, List[Candle]]]:
    """
    Вернуть свечи по всем символам и всем таймфреймам.
    """
    if timeframes is None:
        timeframes = CANDLE_TIMEFRAMES

    result: Dict[str, Dict[Timeframe, List[Candle]]] = {}
    for symbol_key in WATCHLIST.keys():
        result[symbol_key] = {}
        for tf in timeframes:
            result[symbol_key][tf] = get_symbol_candles(symbol_key, tf, limit=limit)
    return result
