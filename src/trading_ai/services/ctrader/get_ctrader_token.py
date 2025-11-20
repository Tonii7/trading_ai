"""
get_ctrader_token.py — Playground-compatible version
---------------------------------------------------
Работает с https://connect.spotware.com/apps/18533/playground
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CTRADER_CLIENT_ID")
CLIENT_SECRET = os.getenv("CTRADER_CLIENT_SECRET")
REDIRECT_URI = os.getenv("CTRADER_REDIRECT_URI")

print("\n🔑 Вставь authorization_code из URL (после ?code=):")
AUTH_CODE = input("CODE: ").strip()

url = "https://connect.spotware.com/api/v2/oauth/token"  # ключевой момент
data = {
    "grant_type": "authorization_code",
    "code": AUTH_CODE,
    "redirect_uri": REDIRECT_URI,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
}

print("\n⏳ Получаем токены...")
r = requests.post(url, data=data)
print("Status:", r.status_code)
print("Raw:", r.text)

if r.status_code == 200:
    tokens = r.json()
    access = tokens.get("access_token")
    refresh = tokens.get("refresh_token")

    with open(".env", "r", encoding="utf-8") as f:
        lines = f.readlines()

    def upsert(k, v):
        for i, line in enumerate(lines):
            if line.startswith(k + "="):
                lines[i] = f"{k}={v}\n"
                return
        lines.append(f"{k}={v}\n")

    upsert("CTRADER_ACCESS_TOKEN", access)
    upsert("CTRADER_REFRESH_TOKEN", refresh)

    with open(".env", "w", encoding="utf-8") as f:
        f.writelines(lines)

    print("\n✅ Токены успешно записаны в .env")
    print("Access token:", access[:20], "...")
else:
    print("\n❌ Ошибка при получении токена. Проверь redirect_uri и code.")
