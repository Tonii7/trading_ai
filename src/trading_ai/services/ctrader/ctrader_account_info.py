"""
ctrader_account_info.py — cTrader REST v2 account info
------------------------------------------------------
Получает данные о балансе, equity, марже и позициях.
Работает с теми же токенами из .env.
"""

import os
import requests
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

ACCESS_TOKEN = os.getenv("CTRADER_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("CTRADER_ACCOUNT_ID")

if not ACCESS_TOKEN or not ACCOUNT_ID:
    raise ValueError("❌ В .env отсутствует CTRADER_ACCESS_TOKEN или CTRADER_ACCOUNT_ID")

BASE_URL = "https://connect.spotware.com/api/v2"
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

print(f"🔗 Checking account {ACCOUNT_ID} via Spotware Connect v2...\n")

# --- Get account info ---
account_url = f"{BASE_URL}/accounts/{ACCOUNT_ID}"
r = requests.get(account_url, headers=HEADERS)

if r.status_code == 200:
    data = r.json()
    print("✅ Account Info:")
    pprint(data)
else:
    print(f"❌ Ошибка {r.status_code}: {r.text}")

# --- Try get trading info if available ---
positions_url = f"{BASE_URL}/accounts/{ACCOUNT_ID}/positions"
r2 = requests.get(positions_url, headers=HEADERS)

print("\n📊 Positions:")
if r2.status_code == 200:
    pprint(r2.json())
else:
    print(f"⚠️ Ошибка позиций: {r2.status_code}")
