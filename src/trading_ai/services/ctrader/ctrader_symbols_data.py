"""
ctrader_symbols_data.py — получение списка символов через cTrader Open API (TCP)
-------------------------------------------------------------------------------
✅ Использует официальный пакет ctrader_open_api (TCP, а не HTTP)
✅ Делает ApplicationAuth + AccountAuth
✅ Запрашивает список символов (ProtoOASymbolsListReq)
✅ Печатает symbolId, symbolName и базовую информацию
"""

import os
from dotenv import load_dotenv

from ctrader_open_api import Client, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *  # noqa
from ctrader_open_api.messages.OpenApiMessages_pb2 import *       # noqa
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *  # noqa
from ctrader_open_api.protobuf import Protobuf

from twisted.internet import reactor

# ─────────────────────────────────────────────
# 1. Загружаем ENV
# ─────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

APP_ID = os.getenv("CTRADER_CLIENT_ID")
APP_SECRET = os.getenv("CTRADER_CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("CTRADER_ACCESS_TOKEN")

# ⚙️ Укажи реальный ctidTraderAccountId
TRADER_ACCOUNT_ID = 45192511

if not all([APP_ID, APP_SECRET, ACCESS_TOKEN]):
    raise ValueError("❌ В .env должны быть CTRADER_CLIENT_ID, CTRADER_CLIENT_SECRET, CTRADER_ACCESS_TOKEN")

# ─────────────────────────────────────────────
# 2. Подключение к DEMO endpoint
# ─────────────────────────────────────────────
HOST = EndPoints.PROTOBUF_DEMO_HOST   # demo.ctraderapi.com
PORT = EndPoints.PROTOBUF_PORT        # 5035 по умолчанию

print(f"🌐 Connecting to cTrader DEMO environment: {HOST}:{PORT} ...")

protocol = TcpProtocol
client = Client(HOST, PORT, protocol)


# ─────────────────────────────────────────────
# 3. Обработчик входящих сообщений
# ─────────────────────────────────────────────
def on_message(client_obj, message, *args):
    """
    message — это ProtoMessage с полем payloadType и бинарным payload.
    """
    # 3.1 ApplicationAuth
    if message.payloadType == ProtoOAPayloadType.Value("PROTO_OA_APPLICATION_AUTH_RES"):
        print("✅ Application authenticated, отправляем AccountAuth...")

        acc_auth = ProtoOAAccountAuthReq()
        acc_auth.ctidTraderAccountId = TRADER_ACCOUNT_ID
        acc_auth.accessToken = ACCESS_TOKEN
        client_obj.send(acc_auth)

    # 3.2 AccountAuth
    elif message.payloadType == ProtoOAPayloadType.Value("PROTO_OA_ACCOUNT_AUTH_RES"):
        print("✅ Account authenticated, запрашиваем список символов...")

        sym_req = ProtoOASymbolsListReq()
        sym_req.ctidTraderAccountId = TRADER_ACCOUNT_ID
        client_obj.send(sym_req)

    # 3.3 SymbolsListRes
    elif message.payloadType == ProtoOAPayloadType.Value("PROTO_OA_SYMBOLS_LIST_RES"):
        # 🧩 Правильный способ декодировать ответ
        res = Protobuf.extract(message)
        symbols = res.symbol

        print(f"\n📊 Получено символов: {len(symbols)}\n")
        for s in symbols[:50]:  # безопасный вывод первых 50
            print(
                f"ID={getattr(s, 'symbolId', '?')} | "
                f"name={getattr(s, 'symbolName', '?')} | "
                f"baseAssetId={getattr(s, 'baseAssetId', '?')} | "
                f"quoteAssetId={getattr(s, 'quoteAssetId', '?')} | "
                f"pipPosition={getattr(s, 'pipPosition', '?')} | "
                f"minTradeVolume={getattr(s, 'minTradeVolume', '?')} | "
                f"description={getattr(s, 'description', '')[:40]}"
            )

        print("\n✅ Symbols list received. Останавливаем соединение.")
        client_obj.stopService()
        reactor.stop()

    else:
        print(f"ℹ️ Необработанный тип payload: {message.payloadType}")


# ─────────────────────────────────────────────
# 4. Callback на подключение/отключение
# ─────────────────────────────────────────────
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
# 5. Запуск клиента
# ─────────────────────────────────────────────
client.setConnectedCallback(on_connected)
client.setDisconnectedCallback(on_disconnected)
client.setMessageReceivedCallback(on_message)

client.startService()
reactor.run()
