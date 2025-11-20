"""
ctrader_openapi_client.py — минимальный клиент cTrader Open API (OpenApiPy)
---------------------------------------------------------------------------
✅ Использует официальный пакет: ctrader-open-api
✅ Делает ApplicationAuth по CLIENT_ID / CLIENT_SECRET
✅ Подключается к demo или live (по переменной CTRADER_ENV)
✅ Печатает ВСЕ входящие сообщения, чтобы увидеть, что связь есть
"""

import os
from dotenv import load_dotenv

from ctrader_open_api import Client, TcpProtocol, Protobuf, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import ProtoOAApplicationAuthReq
from twisted.internet import reactor

# ─────────────────────────────────────────────
# 1. Загружаем .env
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

CLIENT_ID = os.getenv("CTRADER_CLIENT_ID")
CLIENT_SECRET = os.getenv("CTRADER_CLIENT_SECRET")
ENV_MODE = os.getenv("CTRADER_ENV", "demo").lower()  # "demo" или "live"


if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("❌ В .env должны быть CTRADER_CLIENT_ID и CTRADER_CLIENT_SECRET")

# ─────────────────────────────────────────────
# 2. Выбор хоста (demo/live)
# ─────────────────────────────────────────────
if ENV_MODE == "live":
    host = EndPoints.PROTOBUF_LIVE_HOST
    print("ℹ️ Режим: LIVE")
else:
    host = EndPoints.PROTOBUF_DEMO_HOST
    print("ℹ️ Режим: DEMO")

port = EndPoints.PROTOBUF_PORT

# ─────────────────────────────────────────────
# 3. Создаём клиента
# ─────────────────────────────────────────────
client = Client(host, port, TcpProtocol)


def on_error(failure):
    print("❌ Message Error:", failure)


def on_connected(cli):
    """
    Коллбек, вызывается при установлении TCP-соединения.
    Здесь делаем ApplicationAuth.
    """
    print(f"✅ Connected to cTrader Open API: {host}:{port}")

    req = ProtoOAApplicationAuthReq()
    req.clientId = CLIENT_ID
    req.clientSecret = CLIENT_SECRET

    print("📨 Sending ProtoOAApplicationAuthReq ...")
    d = cli.send(req)
    d.addErrback(on_error)


def on_disconnected(cli, reason):
    print("⚠️ Disconnected:", reason)


def on_message(cli, message):
    """
    Универсальный коллбек — печатает ВСЕ приходящие сообщения.
    Это нужно, чтобы увидеть ApplicationAuthRes и прочие ответы.
    """
    decoded = Protobuf.extract(message)
    print("📩 Message received:")
    print(decoded)


# Вешаем коллбеки
client.setConnectedCallback(on_connected)
client.setDisconnectedCallback(on_disconnected)
client.setMessageReceivedCallback(on_message)

# ─────────────────────────────────────────────
# 4. Стартуем сервис
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print(f"🔌 Connecting to {host}:{port} (ENV={ENV_MODE}) ...")
    client.startService()
    reactor.run()
