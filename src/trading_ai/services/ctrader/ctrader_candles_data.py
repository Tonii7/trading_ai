"""
ctrader_candles_data.py — загрузка исторических свечей US30 с нескольких таймфреймов
------------------------------------------------------------------------------------
✅ TCP через официальный пакет ctrader_open_api
✅ ApplicationAuth + AccountAuth
✅ Авто-поиск символа US30 по имени
✅ Запрос ProtoOAGetTrendbarsReq с fromTimestamp и toTimestamp
✅ Сохранение каждой серии свечей в отдельный CSV: US30_M5_candles.csv и т.д.
"""

import os
import time
import csv
from collections import defaultdict
from datetime import datetime, timezone
from dotenv import load_dotenv

from ctrader_open_api import Client, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import *  # noqa
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *  # noqa
from ctrader_open_api.protobuf import Protobuf

from twisted.internet import reactor

# ─────────────────────────────────────────────
# 1. ENV и базовые настройки
# ─────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

APP_ID = os.getenv("CTRADER_CLIENT_ID")
APP_SECRET = os.getenv("CTRADER_CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("CTRADER_ACCESS_TOKEN")
TRADER_ACCOUNT_ID = 45192511

TARGET_SYMBOL_NAME = os.getenv("CTRADER_SYMBOL_NAME", "US30")
DEFAULT_TFS = os.getenv("CTRADER_TFS", "M5,M15,M30,H1,H4,D1").split(",")
DEFAULT_COUNT_PER_TF = int(os.getenv("CTRADER_TREND_COUNT", "500"))

if not all([APP_ID, APP_SECRET, ACCESS_TOKEN]):
    raise ValueError("❌ В .env должны быть CTRADER_CLIENT_ID, CTRADER_CLIENT_SECRET, CTRADER_ACCESS_TOKEN")

HOST = EndPoints.PROTOBUF_DEMO_HOST
PORT = EndPoints.PROTOBUF_PORT

print(f"🌐 Connecting to cTrader DEMO environment: {HOST}:{PORT} ...")

protocol = TcpProtocol
client = Client(HOST, PORT, protocol)

# ─────────────────────────────────────────────
# 2. Глобальные переменные
# ─────────────────────────────────────────────
symbol_id = None
symbol_name_found = None
candles_by_tf = defaultdict(list)
requested_tfs = set()
received_tfs = set()

# ─────────────────────────────────────────────
# 3. Вспомогательные функции
# ─────────────────────────────────────────────
def find_target_symbol(symbols, target_name: str):
    target_up = target_name.upper()
    exact = [s for s in symbols if s.symbolName.upper() == target_up]
    if exact:
        return exact[0]
    partial = [s for s in symbols if target_up in s.symbolName.upper()]
    return partial[0] if partial else None


def tf_to_enum(tf: str) -> int:
    tf = tf.strip().upper()
    return ProtoOATrendbarPeriod.Value(tf)


def enum_to_tf_name(period_enum_val: int) -> str:
    return ProtoOATrendbarPeriod.Name(period_enum_val)


def send_trend_request_for_tf(client_obj, tf: str):
    """
    Отправляем ProtoOAGetTrendbarsReq c обязательными полями fromTimestamp и toTimestamp
    """
    global symbol_id, requested_tfs

    if symbol_id is None:
        print("⚠️ symbol_id не определён, пропускаем.")
        return

    tf = tf.strip().upper()
    period_enum = tf_to_enum(tf)
    now_ms = int(time.time() * 1000)

    # Длительность одной свечи
    ms_per_candle = {
        "M1": 60_000,
        "M5": 5 * 60_000,
        "M15": 15 * 60_000,
        "M30": 30 * 60_000,
        "H1": 60 * 60_000,
        "H4": 4 * 60 * 60_000,
        "D1": 24 * 60 * 60_000,
    }.get(tf, 60_000)

    from_ms = now_ms - (DEFAULT_COUNT_PER_TF * ms_per_candle)

    req = ProtoOAGetTrendbarsReq()
    req.ctidTraderAccountId = TRADER_ACCOUNT_ID
    req.symbolId = symbol_id
    req.period = period_enum
    req.fromTimestamp = int(from_ms)
    req.toTimestamp = int(now_ms)
    req.count = DEFAULT_COUNT_PER_TF

    requested_tfs.add(tf)
    print(f"📨 Запрашиваем свечи: {tf} | {datetime.fromtimestamp(from_ms/1000).strftime('%Y-%m-%d %H:%M')} → "
          f"{datetime.fromtimestamp(now_ms/1000).strftime('%Y-%m-%d %H:%M')}")
    client_obj.send(req)


def save_candles_to_csv(symbol_name: str, tf: str, candles: list):
    if not candles:
        print(f"⚠️ Нет данных свечей для {symbol_name} {tf}")
        return

    safe_symbol = symbol_name.replace("/", "_")
    filename = f"{safe_symbol}_{tf}_candles.csv"
    path = os.path.join(BASE_DIR, filename)

    fieldnames = ["timestamp_ms", "timestamp_iso", "open", "high", "low", "close", "volume"]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in candles:
            writer.writerow(row)

    print(f"💾 Saved {len(candles)} candles → {filename}")


def maybe_finish_and_exit(client_obj):
    if received_tfs >= requested_tfs:
        print("\n✅ Все запрошенные ТФ обработаны, сохраняем CSV...\n")
        for tf in sorted(received_tfs):
            save_candles_to_csv(symbol_name_found or TARGET_SYMBOL_NAME, tf, candles_by_tf[tf])
        print("✅ Готово. Останавливаем соединение.")
        client_obj.stopService()
        reactor.stop()

# ─────────────────────────────────────────────
# 4. Обработчики событий
# ─────────────────────────────────────────────
def on_message(client_obj, message, *args):
    global symbol_id, symbol_name_found, received_tfs

    if message.payloadType == ProtoOAPayloadType.Value("PROTO_OA_APPLICATION_AUTH_RES"):
        print("✅ Application authenticated, отправляем AccountAuth...")
        acc_auth = ProtoOAAccountAuthReq()
        acc_auth.ctidTraderAccountId = TRADER_ACCOUNT_ID
        acc_auth.accessToken = ACCESS_TOKEN
        client_obj.send(acc_auth)

    elif message.payloadType == ProtoOAPayloadType.Value("PROTO_OA_ACCOUNT_AUTH_RES"):
        print("✅ Account authenticated, запрашиваем список символов...")
        sym_req = ProtoOASymbolsListReq()
        sym_req.ctidTraderAccountId = TRADER_ACCOUNT_ID
        client_obj.send(sym_req)

    elif message.payloadType == ProtoOAPayloadType.Value("PROTO_OA_SYMBOLS_LIST_RES"):
        res = Protobuf.extract(message)
        target = find_target_symbol(res.symbol, TARGET_SYMBOL_NAME)
        if not target:
            print(f"❌ Не найден символ {TARGET_SYMBOL_NAME}")
            reactor.stop()
            return
        symbol_id = target.symbolId
        symbol_name_found = target.symbolName
        print(f"✅ Найден символ: symbolId={symbol_id}, symbolName={symbol_name_found}")
        for tf in DEFAULT_TFS:
            send_trend_request_for_tf(client_obj, tf)

    elif message.payloadType == ProtoOAPayloadType.Value("PROTO_OA_GET_TRENDBARS_RES"):
        res = Protobuf.extract(message)
        tf_name = enum_to_tf_name(res.period).upper()
        trendbars = list(res.trendbar)
        print(f"📈 Получено свечей: {len(trendbars)} для {tf_name}")

        for tb in trendbars:
            ts = getattr(tb, "utcTimestamp", getattr(tb, "timestamp", None))
            ts_iso = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat() if ts else None
            candles_by_tf[tf_name].append({
                "timestamp_ms": ts,
                "timestamp_iso": ts_iso,
                "open": getattr(tb, "openPrice", None),
                "high": getattr(tb, "highPrice", None),
                "low": getattr(tb, "lowPrice", None),
                "close": getattr(tb, "closePrice", None),
                "volume": getattr(tb, "volume", None),
            })
        received_tfs.add(tf_name)
        maybe_finish_and_exit(client_obj)


def on_connected(client_obj, *args):
    print("🔌 Connected to cTrader Open API (DEMO)")
    print("🔑 Отправляем ProtoOAApplicationAuthReq...")
    app_auth = ProtoOAApplicationAuthReq()
    app_auth.clientId = APP_ID
    app_auth.clientSecret = APP_SECRET
    client_obj.send(app_auth)


def on_disconnected(client_obj, reason=None, *args):
    print(f"🔌 Disconnected from cTrader. Reason: {reason}")


# ─────────────────────────────────────────────
# 5. Запуск
# ─────────────────────────────────────────────
client.setConnectedCallback(on_connected)
client.setDisconnectedCallback(on_disconnected)
client.setMessageReceivedCallback(on_message)

client.startService()
reactor.run()
