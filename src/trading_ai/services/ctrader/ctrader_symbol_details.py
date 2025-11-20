"""
ctrader_symbol_details.py — подробные параметры инструмента US30 через cTrader Open API (TCP)
--------------------------------------------------------------------------------------------
✅ ApplicationAuth + AccountAuth
✅ Находим US30 в списке символов
✅ Делаем ProtoOASymbolByIdReq по найденному symbolId
✅ Печатаем ВСЕ поля символа (через ListFields), чтобы ничего не ломалось из-за версий протобуфа
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
# 1. ENV
# ─────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

APP_ID = os.getenv("CTRADER_CLIENT_ID")
APP_SECRET = os.getenv("CTRADER_CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("CTRADER_ACCESS_TOKEN")
TRADER_ACCOUNT_ID = 45192511  # твой ctidTraderAccountId

if not all([APP_ID, APP_SECRET, ACCESS_TOKEN]):
    raise ValueError("❌ В .env должны быть CTRADER_CLIENT_ID, CTRADER_CLIENT_SECRET, CTRADER_ACCESS_TOKEN")

# ─────────────────────────────────────────────
# 2. Подключение
# ─────────────────────────────────────────────
HOST = EndPoints.PROTOBUF_DEMO_HOST
PORT = EndPoints.PROTOBUF_PORT

print(f"🌐 Connecting to cTrader DEMO environment: {HOST}:{PORT} ...")

protocol = TcpProtocol
client = Client(HOST, PORT, protocol)

# будем сюда положим найденный symbolId
TARGET_SYMBOL_NAME = "US30"
found_symbol_id = None


# ─────────────────────────────────────────────
# 3. Обработчик сообщений
# ─────────────────────────────────────────────
def on_message(client_obj, message, *args):
    global found_symbol_id

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

    # 3.3 Ответ со списком символов
    elif message.payloadType == ProtoOAPayloadType.Value("PROTO_OA_SYMBOLS_LIST_RES"):
        res = Protobuf.extract(message)
        symbols = res.symbol
        print(f"📊 Получено символов: {len(symbols)}. Ищем {TARGET_SYMBOL_NAME} ...")

        for s in symbols:
            if s.symbolName == TARGET_SYMBOL_NAME:
                found_symbol_id = s.symbolId
                print(f"✅ Найден символ: {TARGET_SYMBOL_NAME} (ID={found_symbol_id}) — запрашиваем детали...")

                # ВАЖНО: symbolId — repeated → используем append()
                req = ProtoOASymbolByIdReq()
                req.ctidTraderAccountId = TRADER_ACCOUNT_ID
                req.symbolId.append(found_symbol_id)

                client_obj.send(req)
                break
        else:
            print(f"❌ Символ {TARGET_SYMBOL_NAME} не найден в списке.")
            client_obj.stopService()
            reactor.stop()

    # 3.4 Ответ с деталями символа
    elif message.payloadType == ProtoOAPayloadType.Value("PROTO_OA_SYMBOL_BY_ID_RES"):
        res = Protobuf.extract(message)

        if not res.symbol:
            print("❌ В ответе SYMBOL_BY_ID_RES нет symbol[]")
        else:
            symbol = res.symbol[0]
            print(f"\n📌 Полное описание символа {TARGET_SYMBOL_NAME} (ID={symbol.symbolId}):\n")

            # Печатаем ВСЕ поля безопасно, без угадывания имён
            for desc, value in symbol.ListFields():
                print(f"{desc.name}: {value}")

        print("\n✅ Детали символа получены. Останавливаем соединение.")
        client_obj.stopService()
        reactor.stop()

    else:
        # Для отладки можно раскомментировать:
        # print(f"ℹ️ Необработанный payloadType: {message.payloadType}")
        pass


# ─────────────────────────────────────────────
# 4. Callbacks подключения
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
# 5. Запуск
# ─────────────────────────────────────────────
client.setConnectedCallback(on_connected)
client.setDisconnectedCallback(on_disconnected)
client.setMessageReceivedCallback(on_message)

client.startService()
reactor.run()
