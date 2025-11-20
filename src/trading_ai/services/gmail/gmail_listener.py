import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE_DIR))

import os
import base64
import time
from email.header import decode_header

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from trading_ai.core.crew import TradingAi
from trading_ai.services.telegram.telegram_bot import bot, TELEGRAM_CHAT_ID


# ---------------------------------------------------------
# Конфигурация
# ---------------------------------------------------------
GMAIL_TOKEN = os.path.join(os.path.dirname(__file__), "token.json")
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


# Инициализация CrewAI
crew = TradingAi()


# ---------------------------------------------------------
# Декодирование письма
# ---------------------------------------------------------
def decode_message(msg):
    """
    Корректно декодирует любые письма TradingView
    """
    payload = msg["payload"]

    # 1) Письмо бывает без parts → берём напрямую body
    if "parts" not in payload:
        data = payload["body"].get("data", "")
        return base64.urlsafe_b64decode(data).decode("utf-8")

    # 2) Если parts есть
    for part in payload["parts"]:
        body = part["body"]
        data = body.get("data")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8")

    return "(empty message)"


# ---------------------------------------------------------
# Парсер TradingView темы
# ---------------------------------------------------------
def extract_subject(headers):
    for h in headers:
        if h["name"].lower() == "subject":
            value, enc = decode_header(h["value"])[0]
            if isinstance(value, bytes):
                return value.decode(enc or "utf-8")
            return value
    return ""


# ---------------------------------------------------------
# Основной слушатель Gmail
# ---------------------------------------------------------
def listen_gmail(interval=10):
    """
    Постоянно слушает входящие Gmail → ищет TradingView → отправляет в CrewAI → результат в Telegram
    """
    print("📡 Gmail listener started...")

    # Загружаем токен Google
    creds = Credentials.from_authorized_user_file(GMAIL_TOKEN, GMAIL_SCOPES)
    service = build("gmail", "v1", credentials=creds)

    last_msg_id = None

    while True:
        try:
            # Берём письма из INBOX
            results = service.users().messages().list(
                userId="me",
                labelIds=["INBOX"],
                maxResults=5,
            ).execute()

            messages = results.get("messages", [])
            if not messages:
                time.sleep(interval)
                continue

            newest = messages[0]["id"]

            if newest != last_msg_id:
                msg = service.users().messages().get(
                    userId="me",
                    id=newest,
                    format="full"
                ).execute()

                headers = msg["payload"]["headers"]
                subject = extract_subject(headers)

                sender = next(
                    (h["value"] for h in headers if h["name"].lower() == "from"),
                    ""
                )

                # Простое условие — письмо от TradingView
                if "tradingview" in sender.lower() or "alert" in subject.lower():
                    body_text = decode_message(msg)

                    print("\n⚡ TradingView alert detected!")
                    print("Subject:", subject)

                    # Отправляем в CrewAI → агент сигналов
                    result = crew.agents["signal_generator"].run(input=body_text)

                    # Отправляем в Telegram
                    bot.loop.create_task(
                        bot.send_message(
                            TELEGRAM_CHAT_ID,
                            f"📨 *TradingView Signal*\n\n*Subject:* {subject}\n\n{result}",
                            parse_mode="Markdown"
                        )
                    )

                last_msg_id = newest

        except Exception as e:
            print("❌ Gmail Listener Error:", e)

        time.sleep(interval)
