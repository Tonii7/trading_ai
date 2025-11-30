"""
market_engine.py — FULL Market Engine v1 + Candle Engine

Задачи:
- собрать срез рынка по ключевым инструментам (WATCHLIST)
- собрать свечи по всем нужным таймфреймам (CANDLE_TIMEFRAMES)
- отправить аккуратный отчёт в Discord через router.dispatch(...)
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from textwrap import shorten
from typing import Dict, List

from trading_ai.services.ctrader.market_snapshot import (
    WATCHLIST,
    CANDLE_TIMEFRAMES,
    SymbolSnapshot,
    Candle,
    get_full_market_snapshot,
    get_full_candles_snapshot,
)
from trading_ai.services.discord.router import dispatch


class MarketEngine:
    """
    FULL Market Engine v1:
    - собирает snapshot по всем инструментам из WATCHLIST
    - собирает свечи по всем TF из CANDLE_TIMEFRAMES
    - шлёт в Discord по маршрутам:
        - market_snapshot → market_analyzer
        - market_candles  → technicals_15m
        - engine_logs     → system_logs
        - errors          → system_logs
    """

    def __init__(self) -> None:
        self.snapshot_route = "market_snapshot"
        self.candles_route = "market_candles"
        self.engine_logs_route = "engine_logs"
        self.errors_route = "errors"

    # ─────────────────────────────────────────
    # Форматирование snapshot
    # ─────────────────────────────────────────
    @staticmethod
    def _format_snapshot_line(s: SymbolSnapshot) -> str:
        ts = s.timestamp.strftime("%H:%M:%S")
        return (
            f"{s.symbol_key:<7} | "
            f"Bid: {s.bid:<10} Ask: {s.ask:<10} "
            f"Last: {s.last:<10} Spread: {s.spread:<8} "
            f"({ts} UTC)"
        )

    def build_snapshot_report(self, snapshots: Dict[str, SymbolSnapshot]) -> str:
        lines: List[str] = ["**FULL Market Snapshot v1**", ""]
        for key in WATCHLIST.keys():
            s = snapshots[key]
            lines.append(self._format_snapshot_line(s))
        return "\n".join(lines)

    # ─────────────────────────────────────────
    # Форматирование свечей
    # ─────────────────────────────────────────
    @staticmethod
    def _format_candle_block(symbol_key: str, tf: str, candles: List[Candle]) -> str:
        """
        Берём последнюю свечу (и предыдущую для изменения).
        """
        if not candles:
            return f"**{symbol_key} {tf}** — нет данных"

        last = candles[-1]
        prev = candles[-2] if len(candles) > 1 else None

        change = ""
        if prev:
            diff = last.close - prev.close
            pct = (diff / prev.close) * 100 if prev.close else 0
            sign = "+" if diff >= 0 else "-"
            change = f" ({sign}{abs(diff):.2f}, {sign}{abs(pct):.2f}%)"

        t = last.time.strftime("%Y-%m-%d %H:%M")
        return (
            f"**{symbol_key} {tf}** [{t} UTC]\n"
            f" O: {last.open:.2f}  H: {last.high:.2f}  "
            f"L: {last.low:.2f}  C: {last.close:.2f}{change}\n"
        )

    def build_candles_report(
        self,
        candles: Dict[str, Dict[str, List[Candle]]],
    ) -> str:
        lines: List[str] = ["**Candle Engine v1 — M5/M15/M30/H1/H4/D1**", ""]
        for symbol_key in WATCHLIST.keys():
            lines.append(f"__{symbol_key}__")
            for tf in CANDLE_TIMEFRAMES:
                block = self._format_candle_block(
                    symbol_key, tf, candles[symbol_key][tf]
                )
                # слегка режем длину каждой строки, чтобы итоговый текст не был гигантским
                lines.append(shorten(block, width=400, placeholder=" ."))
            lines.append("")  # пустая строка между инструментами
        return "\n".join(lines)

    # ─────────────────────────────────────────
    # Основные методы
    # ─────────────────────────────────────────
    async def run_once(self) -> None:
        """
        Один цикл:
        - забирает snapshot рынка
        - забирает свечи
        - отправляет всё в Discord
        """
        # 1. Snapshot
        try:
            snapshots = await asyncio.to_thread(get_full_market_snapshot)
            snapshot_msg = self.build_snapshot_report(snapshots)
            dispatch(self.snapshot_route, "Full Market Snapshot v1", snapshot_msg)
        except Exception as e:  # noqa
            dispatch(self.errors_route, "Snapshot Engine Error", str(e))

        # 2. Candles
        try:
            candles = await asyncio.to_thread(get_full_candles_snapshot)
            candles_msg = self.build_candles_report(candles)
            dispatch(self.candles_route, "Candle Engine v1", candles_msg)
        except Exception as e:  # noqa
            dispatch(self.errors_route, "Candle Engine Error", str(e))

    async def run_forever(self, interval_seconds: int = 300) -> None:
        """
        Бесконечный цикл (по умолчанию раз в 5 минут).
        """
        while True:
            started = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            dispatch(
                self.engine_logs_route,
                "Engine Tick",
                f"Engine executed at {started} UTC",
            )
            try:
                await self.run_once()
            except Exception as e:  # noqa
                dispatch(self.errors_route, "MarketEngine Fatal Error", str(e))
            await asyncio.sleep(interval_seconds)
