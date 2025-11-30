import os
from dotenv import load_dotenv

from ctrader_open_api import Client, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *
from ctrader_open_api.protobuf import Protobuf

from twisted.internet import reactor

# ─────────────────────────────────────────────
# ГЛОБАЛЬНЫЙ ПУТЬ К .ENV (корень проекта)
# ─────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

if not os.path.exists(ENV_PATH):
    raise ValueError(f"❌ Не найден .env в корне проекта: {ENV_PATH}")

load_dotenv(ENV_PATH)
print(f"⚙️ Loaded .env from: {ENV_PATH}")

# ─────────────────────────────────────────────
# ENV ПАРАМЕТРЫ
# ─────────────────────────────────────────────
APP_ID = os.getenv("CTRADER_CLIENT_ID")
APP_SECRET = os.getenv("CTRADER_CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("CTRADER_ACCESS_TOKEN")
TRADER_ACCOUNT_ID = int(os.getenv("CTRADER_ACCOUNT_ID", "0"))

if not all([APP_ID, APP_SECRET, ACCESS_TOKEN]):
    raise ValueError("❌ В .env отсутствуют CTRADER_CLIENT_ID / SECRET / TOKEN")

# ─────────────────────────────────────────────
# Подключение
# ─────────────────────────────────────────────
HOST = EndPoints.PROTOBUF_DEMO_HOST
PORT = EndPoints.PROTOBUF_PORT

protocol = TcpProtocol
client = Client(HOST, PORT, protocol)

ALL_SYMBOLS = []


def on_message(client_obj, message, *args):

    if message.payloadType == ProtoOAPayloadType.Value("PROTO_OA_APPLICATION_AUTH_RES"):
        print("🔐 Application authenticated → sending AccountAuth...")
        acc = ProtoOAAccountAuthReq()
        acc.ctidTraderAccountId = TRADER_ACCOUNT_ID
        acc.accessToken = ACCESS_TOKEN
        client_obj.send(acc)

    elif message.payloadType == ProtoOAPayloadType.Value("PROTO_OA_ACCOUNT_AUTH_RES"):
        print("🔑 Account authenticated → requesting ALL symbols...")
        req = ProtoOASymbolsListReq()
        req.ctidTraderAccountId = TRADER_ACCOUNT_ID
        client_obj.send(req)

    elif message.payloadType == ProtoOAPayloadType.Value("PROTO_OA_SYMBOLS_LIST_RES"):
        res = Protobuf.extract(message)
        symbols = res.symbol
        print(f"📊 Получено символов: {len(symbols)}")

        names = sorted({s.symbolName for s in symbols})
        ALL_SYMBOLS.extend(names)

        print("\n=== 📜 СПИСОК ВСЕХ SYMBOL_NAME ===")
        for name in names:
            print(name)

        out_path = os.path.join(PROJECT_ROOT, "symbols_list.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            for name in names:
                f.write(name + "\n")

        print(f"\n💾 Symbols saved → {out_path}")

        client_obj.stopService()
        reactor.stop()


def on_connected(client_obj, *args):
    print("🔌 Connected → Sending ApplicationAuth...")
    req = ProtoOAApplicationAuthReq()
    req.clientId = APP_ID
    req.clientSecret = APP_SECRET
    client_obj.send(req)


def on_disconnected(client_obj, reason=None, *args):
    print(f"🔌 Disconnected: {reason}")


client.setConnectedCallback(on_connected)
client.setDisconnectedCallback(on_disconnected)
client.setMessageReceivedCallback(on_message)

client.startService()
reactor.run()
