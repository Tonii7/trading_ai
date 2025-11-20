import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

API = f"https://api.telegram.org/bot{TOKEN}/sendMessage"


def send_telegram_message(text: str):
    if not TOKEN or not CHAT_ID:
        print("⚠️ Telegram credentials missing")
        return

    try:
        requests.post(API, data={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        })
    except Exception as e:
        print("⚠️ Telegram send error:", e)
