import asyncio
from typing import Any, Dict, List

from src.trading_ai.services.ctrader.ctrader_openapi_client import CTraderClient
from src.trading_ai.services.discord.router import dispatch

# Можно расширять список под твой портфель
SYMBOLS = ["US30", "SPX500", "XAUUSD"]


class CTraderMarketAgent:
    """
    Агент, который:
    - подключается к cTrader,
    - собирает по каждому символу базовый срез рынка,
    - отправляет в Discord через router → маршрут 'market'.
    """

    def __init__(self) -> None:
        self.client = CTraderClient()

    async def _fetch_symbol_snapshot(self, symbol: str) -> str:
        """
        Сбор среза по одному инструменту.
        """
        ticks: List[Dict[str, Any]] = await self.client.get_symbol_ticks(symbol)
        candles: List[Dict[str, Any]] = await self.client.get_symbol_candles(
            symbol, timeframe="M1", count=5
        )
        details: Dict[str, Any] = await self.client.get_symbol_details(symbol)

        last_bid = None
        last_ask = None
        last_price = None

        if ticks:
            last = ticks[-1]
            last_bid = last.get("bid")
            last_ask = last.get("ask")
            last_price = last_bid or last_ask

        spread = None
        if last_bid is not None and last_ask is not None:
            spread = last_ask - last_bid

        # Короткий блок по свечам
        candles_lines = []
        for c in candles[:5]:
            t = c.get("time")
            o = c.get("open")
            h = c.get("high")
            l = c.get("low")
            cl = c.get("close")
            candles_lines.append(f"{t}: O={o}, H={h}, L={l}, C={cl}")

        candles_block = "\n".join(candles_lines)

        text = (
            f"**Symbol:** {symbol}\n"
            f"Last price: {last_price}\n"
            f"Bid: {last_bid}, Ask: {last_ask}, Spread: {spread}\n\n"
            f"**Recent M1 candles (5):**\n{candles_block}\n"
        )

        if details:
            contract_size = details.get("contract_size")
            margin = details.get("margin")
            if contract_size or margin:
                text += "\n**Contract details:**\n"
                if contract_size:
                    text += f"- Contract size: {contract_size}\n"
                if margin:
                    text += f"- Margin: {margin}\n"

        return text

    async def run_once(self) -> None:
        """
        Один проход по всем символам:
        - подключаемся,
        - собираем срез,
        - отправляем в Discord,
        - отключаемся.
        """
        await self.client.connect()

        for symbol in SYMBOLS:
            try:
                snapshot_text = await self._fetch_symbol_snapshot(symbol)
                dispatch("market", snapshot_text, title=f"cTrader Market Snapshot — {symbol}")
            except Exception as e:
                dispatch(
                    "errors",
                    f"cTraderMarketAgent error for {symbol}: {e}",
                    title="cTrader Market Agent Error",
                )

        await self.client.disconnect()

    async def run_loop(self, interval_seconds: int = 60) -> None:
        """
        Непрерывный режим: опрашивает рынок каждые N секунд.
        Можно будет запускать как постоянный фоновый процесс.
        """
        await self.client.connect()

        try:
            while True:
                for symbol in SYMBOLS:
                    try:
                        snapshot_text = await self._fetch_symbol_snapshot(symbol)
                        dispatch(
                            "market",
                            snapshot_text,
                            title=f"cTrader Market Snapshot — {symbol}",
                        )
                    except Exception as e:
                        dispatch(
                            "errors",
                            f"cTraderMarketAgent loop error for {symbol}: {e}",
                            title="cTrader Market Agent Error",
                        )
                await asyncio.sleep(interval_seconds)
        finally:
            await self.client.disconnect()
