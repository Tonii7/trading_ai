"""
ctrader_connector.py — заглушка под реальный cTrader Open API коннектор
----------------------------------------------------------------------
⚠ Важно:
    Этот файл аккуратно работает с токенами, но НЕ ходит за котировками,
    потому что для этого нужен WebSocket + официальный Open API SDK
    или точные примеры из документации/Playground.

    Сейчас его задача — не ломать проект и дать понятную точку расширения.
"""

import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from typing import Optional
import pandas as pd

# Загружаем .env из корня проекта
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)


class CTraderConnector:
    def __init__(self):
        self.client_id = os.getenv("CTRADER_CLIENT_ID")
        self.client_secret = os.getenv("CTRADER_CLIENT_SECRET")
        self.access_token = os.getenv("CTRADER_ACCESS_TOKEN")
        self.refresh_token = os.getenv("CTRADER_REFRESH_TOKEN")
        self.account_id = os.getenv("CTRADER_ACCOUNT_ID")

        missing = [
            name
            for name, value in {
                "CTRADER_CLIENT_ID": self.client_id,
                "CTRADER_CLIENT_SECRET": self.client_secret,
                "CTRADER_ACCESS_TOKEN": self.access_token,
                "CTRADER_REFRESH_TOKEN": self.refresh_token,
                "CTRADER_ACCOUNT_ID": self.account_id,
            }.items()
            if not value
        ]
        if missing:
            raise ValueError(f"❌ Отсутствуют CTRADER_* параметры в .env: {missing}")

        self.last_refresh = datetime.now(timezone.utc)

        print("=== CTraderConnector initialized ===")
        print(f"  ACCOUNT_ID: {self.account_id}")
        print("  (⚠️ Маркет-данные пока не реализованы — см. комментарии в коде.)")

    # ──────────────────────────────────────────────
    # Заглушка для обновления токена
    # ──────────────────────────────────────────────
    def ensure_token_valid(self):
        """
        Проверка «срока жизни» токена.
        Здесь нет реального запроса к OAuth-серверу, только место под будущую логику.
        """
        if datetime.now(timezone.utc) - self.last_refresh > timedelta(minutes=55):
            print("♻️ (Заглушка) Тут должен быть refresh_access_token() для cTrader Open API.")
            # Здесь в будущем можно реализовать реальный запрос к OAuth-endpoint
            self.last_refresh = datetime.now(timezone.utc)

    # ──────────────────────────────────────────────
    # Заглушка для списка символов
    # ──────────────────────────────────────────────
    def get_symbol_list(self) -> list[dict]:
        """
        В реальном коннекторе этот метод должен ходить в Open API (WebSocket/SDK)
        и возвращать список доступных символов для данного account_id.

        Пока возвращаем пустой список и печатаем понятное сообщение.
        """
        print("⚠️ get_symbol_list() пока не реализован (нужен WebSocket/SDK).")
        return []

    def get_symbol_id(self, symbol_name: str) -> Optional[int]:
        """
        В реальном коннекторе — поиск symbolId по имени из списка символов.
        Сейчас просто сообщает, что не реализовано.
        """
        print(f"⚠️ get_symbol_id('{symbol_name}') пока не реализован.")
        return None

    # ──────────────────────────────────────────────
    # Заглушка для исторических данных
    # ──────────────────────────────────────────────
    def get_historical_data(self, symbol: str, timeframe: str = "M15", bars: int = 500) -> pd.DataFrame:
        """
        В реальном варианте:
            — через Open API (WebSocket + proto/JSON) получить свечи для symbol,
            — вернуть DataFrame: time, open, high, low, close, volume.

        Сейчас — заглушка, которая:
            — выводит предупреждение,
            — возвращает ПУСТОЙ DataFrame, чтобы не падали остальные части системы.
        """
        print(f"⚠️ get_historical_data('{symbol}', timeframe='{timeframe}', bars={bars}) не реализован.")
        print("   Нужно подключать официальный cTrader Open API SDK или реализовать WebSocket-клиент.")
        return pd.DataFrame()


# Небольшая диагностика при прямом запуске
if __name__ == "__main__":
    connector = CTraderConnector()
    df = connector.get_historical_data("US30", timeframe="M15", bars=50)
    print(df.head())
