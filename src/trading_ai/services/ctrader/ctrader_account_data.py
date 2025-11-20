"""
ctrader_account_data.py — минимальный рабочий клиент cTrader Open API (DEMO/LIVE)

Что делает:
- Подключается к PROTOBUF серверу (demo.ctraderapi.com:5035 или live)
- Делает Application Auth по CTRADER_CLIENT_ID / CTRADER_CLIENT_SECRET
- Делает Account Auth по CTRADER_ACCOUNT_ID / CTRADER_ACCESS_TOKEN
- Печатает все входящие сообщения через Protobuf.extract(...)
"""

import os
from dotenv import load_dotenv

from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq,
    ProtoOAAccountAuthReq,
)
from twisted.internet import reactor

# ─────────────────────────────────────────
# 1. Загружаем .env
# ─────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

APP_ID = os.getenv("CTRADER_CLIENT_ID")
APP_SECRET = os.getenv("CTRADER_CLIENT_SECRET")
ACCOUNT_ID = os.getenv("CTRADER_ACCOUNT_ID")
ACCESS_TOKEN = os.getenv("CTRADER_ACCESS_TOKEN")
ENV_MODE = os.getenv("CTRADER_ENV", "demo").lower()  # "demo" или "live"

if not all([APP_ID, APP_SECRET, ACCOUNT_ID, ACCESS_TOKEN]):
    raise RuntimeError(
        "В .env должны быть заданы CTRADER_CLIENT_ID, CTRADER_CLIENT_SECRET, "
        "CTRADER_ACCOUNT_ID, CTRADER_ACCESS_TOKEN"
    )

try:
    ACCOUNT_ID_INT = int(ACCOUNT_ID)
except ValueError:
    raise RuntimeError(f"CTRADER_ACCOUNT_ID должен быть числом, а не '{ACCOUNT_ID}'")

# ─────────────────────────────────────────
# 2. Выбор хоста (DEMO / LIVE)
# ─────────────────────────────────────────
if ENV_MODE == "live":
    HOST = EndPoints.PROTOBUF_LIVE_HOST
    MODE_STR = "LIVE"
else:
    HOST = EndPoints.PROTOBUF_DEMO_HOST
    MODE_STR = "DEMO"

PORT = EndPoints.PROTOBUF_PORT

# ─────────────────────────────────────────
# 3. Инициализация клиента
# ─────────────────────────────────────────
protocol = TcpProtocol  # библиотека ожидает класс протокола, а не экземпляр
client = Client(HOST, PORT, protocol)


# ─────────────────────────────────────────
# 4. Callbacks
# ─────────────────────────────────────────
def on_error(failure):
    print("❌ Message Error:", failure)


def on_account_auth_response(result):
    print("\n✅ Account authenticated!")
    print("   Теперь можно запрашивать символы, свечи, позиции и т.д.")
    # На этом можно остановиться — цель скрипта показать, что авторизация работает.


def on_application_auth_response(result):
    print("\n✅ Application authenticated, делаем AccountAuth...")

    req = ProtoOAAccountAuthReq()
    req.ctidTraderAccountId = ACCOUNT_ID_INT
    req.accessToken = ACCESS_TOKEN

    d = client.send(req)
    d.addCallbacks(on_account_auth_response, on_error)


def connected(cl):
    print(f"\n🔌 Connected to cTrader Open API ({MODE_STR}) {HOST}:{PORT}")
    print("🔑 Отправляем ProtoOAApplicationAuthReq...")

    req = ProtoOAApplicationAuthReq()
    req.clientId = APP_ID
    req.clientSecret = APP_SECRET

    d = client.send(req)
    d.addCallbacks(on_application_auth_response, on_error)


def disconnected(cl, reason):
    print("\n🔌 Disconnected:", reason)
    # Останавливаем Twisted reactor
    reactor.stop()


def on_message_received(cl, message):
    # Здесь мы просто красиво печатаем все, что приходит от сервера
    print("\n📩 Message received:\n", Protobuf.extract(message))


# ─────────────────────────────────────────
# 5. Привязываем callbacks и запускаем
# ─────────────────────────────────────────
client.setConnectedCallback(connected)
client.setDisconnectedCallback(disconnected)
client.setMessageReceivedCallback(on_message_received)

print(f"🌐 Connecting to cTrader {MODE_STR} environment: {HOST}:{PORT} ...")
client.startService()

# Запускаем Twisted event loop
reactor.run()
