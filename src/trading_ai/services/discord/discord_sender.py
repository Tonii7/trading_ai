import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# ─────────────────────────────────────────
# Загрузка .env так же, как в bot.py
# ─────────────────────────────────────────

CURRENT_FILE = Path(__file__).resolve()

env_path = None
for parent in CURRENT_FILE.parents:
    if (parent / ".env").exists():
        env_path = parent / ".env"
        break

if env_path:
    load_dotenv(env_path)
else:
    print("⚠️ Router: .env NOT FOUND")

DISCORD_SERVICE_URL = "http://127.0.0.1:8787/send"
SERVICE_SECRET = os.getenv("DISCORD_SERVICE_SECRET")

print("SECRET FROM ENV:", SERVICE_SECRET)


# ─────────────────────────────────────────
# Отправка сообщения через локальный HTTP сервис
# ─────────────────────────────────────────

def send_discord_embed_via_service(channel_key: str, title: str, content: str):
    if not SERVICE_SECRET:
        print("[Router → Discord] ❌ В .env нет DISCORD_SERVICE_SECRET")
        return

    payload = {
        "channel_key": channel_key,
        "title": title,
        "description": content,
    }

    headers = {
        "X-API-KEY": SERVICE_SECRET
    }

    try:
        resp = requests.post(DISCORD_SERVICE_URL, json=payload, headers=headers, timeout=5)

        if resp.status_code == 200:
            print(f"[Router → Discord] OK → {channel_key}")
        else:
            print(f"[Router → Discord] ❌ HTTP {resp.status_code}: {resp.text}")

    except Exception as e:
        print(f"[Router → Discord] ❌ Ошибка отправки: {e}")
