"""
ctrader_openapi_client.py — асинхронная обёртка над синхронными функциями cTrader Open API.

Идея:
- market_snapshot.py содержит синхронный код с ctrader_open_api / Twisted.
- здесь мы оборачиваем его в async-интерфейс, который удобно использовать в агентах.
"""

from typing import Any, Dict, List
import asyncio

try:
    from trading_ai.services.ctrader import market_snapshot as _snapshot
    fetch_last_tick = getattr(_snapshot, "fetch_last_tick", None)
    fetch_candles = getattr(_snapshot, "fetch_candles", None)
    fetch_symbol_details = getattr(_snapshot, "fetch_symbol_details", None)
except ImportError:
    _snapshot = None
    fetch_last_tick = None
    fetch_candles = None
    fetch_symbol_details = None


class CTraderClient:
    """
    Асинхронный клиент для работы с данными cTrader.

    ВАЖНО:
    - connect()/disconnect() оставлены для совместимости.
      Если внутри snapshot-функций уже есть своя логика подключения/отключения,
      их можно сделать пустыми или использовать как контекст.
    """

    def __init__(self) -> None:
        self.connected: bool = False

    async def connect(self) -> None:
        """
        Если твой код требует явного открытия соединения — перенеси туда логику.
        Если каждая snapshot-функция сама открывает/закрывает соединение — можно оставить так.
        """
        self.connected = True

    async def disconnect(self) -> None:
        """
        Аналогично connect(): если нужен явный disconnect — реализуй.
        """
        self.connected = False

    async def get_symbol_ticks(self, symbol: str, depth: int = 1) -> List[Dict[str, Any]]:
        """
        Асинхронная обёртка над fetch_last_tick().
        Вызываем синхронный код в отдельном потоке, чтобы не блокировать event loop.
        """
        if fetch_last_tick is None:
            raise RuntimeError("fetch_last_tick не реализован в market_snapshot.py")
        return await asyncio.to_thread(fetch_last_tick, symbol, depth)

    async def get_symbol_candles(
        self,
        symbol: str,
        timeframe: str = "M1",
        count: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Асинхронная обёртка над fetch_candles().
        """
        if fetch_candles is None:
            raise RuntimeError("fetch_candles не реализован в market_snapshot.py")
        return await asyncio.to_thread(fetch_candles, symbol, timeframe, count)

    async def get_symbol_details(self, symbol: str) -> Dict[str, Any]:
        """
        Асинхронная обёртка над fetch_symbol_details().
        """
        if fetch_symbol_details is None:
            raise RuntimeError("fetch_symbol_details не реализован в market_snapshot.py")
        return await asyncio.to_thread(fetch_symbol_details, symbol)


async def _demo() -> None:
    """
    Тестовый запуск для:

        python -m trading_ai.services.ctrader.ctrader_openapi_client
    """
    client = CTraderClient()
    await client.connect()

    print("\n=== CTrader OpenAPI Demo ===")

    try:
        details = await client.get_symbol_details("US30")
        print("US30 details:", details)
    except Exception as e:
        print("Ошибка при получении details:", e)

    try:
        ticks = await client.get_symbol_ticks("US30", depth=1)
        print("US30 ticks:", ticks)
    except Exception as e:
        print("Ошибка при получении ticks:", e)

    try:
        candles = await client.get_symbol_candles("US30", "M1", 3)
        print("US30 candles:", candles)
    except Exception as e:
        print("Ошибка при получении candles:", e)

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(_demo())
