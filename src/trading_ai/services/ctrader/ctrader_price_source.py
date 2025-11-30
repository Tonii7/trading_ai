"""
ctrader_price_source.py — каркас полного модуля cTrader для Market Engine

Задачи:
- подключение к cTrader Open API (через библиотеку ctrader-open-api или JSON WebSocket)
- получение:
  - актуальных bid/ask/last по символу
  - исторических/живых свечей (trendbars) по символу и таймфрейму
- конвертация в внутренние датаклассы из market_snapshot.py

ВНИМАНИЕ:
- Этот файл сделан как архитектурный каркас.
- Конкретные вызовы к cTrader Open API (ProtoOASubscribeSpotsReq,
  ProtoOAGetTrendbarsReq и т.п.) нужно будет дописать по официальной
  документации Spotware: https://help.ctrader.com/open-api/symbol-data/
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Импортируем модели из market_snapshot
from trading_ai.services.ctrader.market_snapshot import (
    SymbolSnapshot,
    Candle,
    Timeframe,
    WATCHLIST,
)

# Если используешь library ctrader-open-api, раскомментируй:
# from ctrader_open_api import Client, EndPoints, TcpProtocol
# from ctrader_open_api.messages.OpenApiMessages_pb2 import (
#     ProtoOASubscribeSpotsReq,
#     ProtoOAGetTrendbarsReq,
# )
# from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import ProtoOAPayloadType
# from ctrader_open_api.messages.OpenApiModelMessages_pb2 import ProtoOATrendbarPeriod

# ─────────────────────────────────────────────
# 0. Конфигурация cTrader
# ─────────────────────────────────────────────

@dataclass
class CTraderConfig:
    host: str                 # DEMO/LIVE endpoint
    port: int
    app_id: str               # clientId приложения
    app_secret: str           # clientSecret
    access_token: str         # OAuth accessToken
    account_id: int           # ctidTraderAccountId

    @classmethod
    def from_env(cls) -> "CTraderConfig":
        """
        Читает настройки из .env.

        Обязательные переменные:
        - CTRADER_APP_ID
        - CTRADER_APP_SECRET
        - CTRADER_ACCESS_TOKEN
        - CTRADER_ACCOUNT_ID
        - CTRADER_ENV  ("DEMO" или "LIVE")

        Порт почти всегда EndPoints.PROTOBUF_PORT, но можно вынести явно.
        """
        env = os.getenv("CTRADER_ENV", "DEMO").upper()

        # Если используешь EndPoints из ctrader-open-api:
        # if env == "LIVE":
        #     host = EndPoints.PROTOBUF_LIVE_HOST
        # else:
        #     host = EndPoints.PROTOBUF_DEMO_HOST

        # Чтобы не тащить EndPoints сюда, зададим строками:
        if env == "LIVE":
            host = "prime-datapath.ctrader.com"
        else:
            host = "demo-datapath.ctrader.com"

        port = int(os.getenv("CTRADER_PORT", "5035"))

        return cls(
            host=host,
            port=port,
            app_id=os.environ["CTRADER_APP_ID"],
            app_secret=os.environ["CTRADER_APP_SECRET"],
            access_token=os.environ["CTRADER_ACCESS_TOKEN"],
            account_id=int(os.environ["CTRADER_ACCOUNT_ID"]),
        )


# ─────────────────────────────────────────────
# 1. Файловый кэш (промежуточное решение)
# ─────────────────────────────────────────────

"""
Идея:

Чтобы не тащить внутрь CrewAI/Tg/Discord всю сложность Twisted/WebSocket,
делаем отдельный "ценовой демон" на cTrader, который:

- подключается к Open API
- подписывается на нужные символы
- при каждом ProtoOASpotEvent/Trendbar обновляет JSON-файл с последними
  ценами и свечами.

А Market Engine читает УЖЕ ГОТОВЫЙ JSON и строит SymbolSnapshot/Candle.

Так мы разделяем:
- сложный асинхронный слой cTrader
- и простой синхронный слой CrewAI/Discord.
"""

DATA_DIR = Path(os.getenv("TRADING_AI_DATA_DIR", ".")) / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SPOTS_JSON = DATA_DIR / "ctrader_spots.json"
CANDLES_JSON = DATA_DIR / "ctrader_candles.json"


def _load_json(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


# ─────────────────────────────────────────────
# 2. Публичный API для market_snapshot.py
# ─────────────────────────────────────────────

def get_realtime_snapshot(symbol_key: str) -> Optional[SymbolSnapshot]:
    """
    Возвращает актуальный snapshot из JSON-кэша,
    который обновляется отдельным cTrader-демоном.

    Формат SPOTS_JSON:
    {
      "US30": {
        "symbol_name": "US30",
        "bid": 39012.5,
        "ask": 39013.0,
        "last": 39012.5,
        "timestamp": "2025-11-29T12:34:56.789123+00:00"
      },
      ...
    }
    """
    spots = _load_json(SPOTS_JSON)
    row = spots.get(symbol_key)
    if not row:
        return None

    try:
        ts = datetime.fromisoformat(row["timestamp"])
    except Exception:
        ts = datetime.now(timezone.utc)

    return SymbolSnapshot(
        symbol_key=symbol_key,
        symbol_name=row.get("symbol_name", WATCHLIST[symbol_key]),
        bid=float(row["bid"]),
        ask=float(row["ask"]),
        last=float(row["last"]),
        spread=round(float(row["ask"]) - float(row["bid"]), 2),
        timestamp=ts,
    )


def get_realtime_candles(
    symbol_key: str,
    timeframe: Timeframe,
    limit: int = 50,
) -> List[Candle]:
    """
    Возвращает свечи из JSON-кэша, которые обновляет cTrader-демон.

    Формат CANDLES_JSON:
    {
      "US30": {
        "M15": [
          {
            "time": "2025-11-29T12:30:00+00:00",
            "open": 39000.0,
            "high": 39010.0,
            "low": 38990.0,
            "close": 39005.0,
            "volume": 1234.0
          },
          ...
        ]
      },
      ...
    }
    """
    store = _load_json(CANDLES_JSON)
    sym_block = store.get(symbol_key, {})
    tf_block = sym_block.get(timeframe, [])
    result: List[Candle] = []

    for row in tf_block[-limit:]:
        try:
            t = datetime.fromisoformat(row["time"])
        except Exception:
            t = datetime.now(timezone.utc)
        result.append(
            Candle(
                symbol_key=symbol_key,
                symbol_name=WATCHLIST[symbol_key],
                timeframe=timeframe,
                time=t,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row.get("volume", 0.0)),
            )
        )

    return result


# ─────────────────────────────────────────────
# 3. TODO: сам cTrader-демон (live-интеграция)
# ─────────────────────────────────────────────

"""
Здесь должна жить логика:

- создать Client(…)
- подключиться к демо/лайв хосту
- пройти:
    ProtoOAApplicationAuthReq  (app_id/app_secret)
    ProtoOAAccountAuthReq      (access_token, account_id)
- получить список символов (ProtoOASymbolsListReq) → маппинг symbol_name → symbol_id
- подписаться:
    ProtoOASubscribeSpotsReq          (для bid/ask/last)
    ProtoOASubscribeLiveTrendbarReq   (для лайв свечей)

- в onMessage / обработчике ProtoOASpotEvent:
    * пересчитать bid/ask/last из "relative" в цену (делим на 100000, округляем по digits)
    * обновить dict latest_spots
    * сохранить latest_spots в SPOTS_JSON через _save_json

- в обработчике ProtoOAGetTrendbarsRes / live trendbars:
    * аналогично пересчитать O/H/L/C из relative формата (см. docs)
    * обновить latest_candles
    * сохранить latest_candles в CANDLES_JSON

Пример Python-обработки исторических свечей есть в официальной документации
("Attain symbol data" → блок Python с ProtoOAGetTrendbarsReq / onHistoricalTrendbarsReceived).
Там показан расчёт реальных цен из относительных значений.
"""


def run_ctrader_daemon() -> None:
    """
    Заготовка точки входа для отдельного процесса cTrader-демона.

    План:
    - прочитать конфиг: cfg = CTraderConfig.from_env()
    - создать Client / WebSocket
    - запустить подключение и цикл обработки
    - внутри обработчиков постоянно обновлять SPOTS_JSON и CANDLES_JSON

    Сейчас функция — заглушка, чтобы не ломать импорт.
    """
    print("[ctrader_price_source] TODO: реализовать run_ctrader_daemon() с реальным подключением к cTrader.")
    print("Смотри комментарии в этом файле и официальную документацию Open API.")
    

if __name__ == "__main__":
    # При запуске:
    #   python -m trading_ai.services.ctrader.ctrader_price_source
    # можно будет поднимать отдельный демон.
    run_ctrader_daemon()
