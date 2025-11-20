"""
🔍 cTrader Diagnostic Tool
------------------------------------------
Проверяет корректность подключения и токенов.
1️⃣ Проверяет переменные из .env
2️⃣ Пробует обновить токен
3️⃣ Загружает 10 свечей US30 с cTrader
"""

import os
import sys
from dotenv import load_dotenv

# === Добавляем пути вручную ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
PROJECT_ROOT = os.path.abspath(os.path.join(SRC_DIR, ".."))
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, os.path.join(SRC_DIR, "trading_ai"))

print("🧩 sys.path patched:")
for p in sys.path[:3]:
    print("  ", p)

# === Загружаем переменные ===
from trading_ai.connectors.ctrader_connector import CTraderConnector

print("\n🔹 Проверка .env файла...")
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))

keys = [
    "CTRADER_CLIENT_ID",
    "CTRADER_CLIENT_SECRET",
    "CTRADER_REDIRECT_URI",
    "CTRADER_ACCOUNT_ID",
    "CTRADER_ACCESS_TOKEN",
    "CTRADER_REFRESH_TOKEN"
]

missing = []
for key in keys:
    value = os.getenv(key)
    if not value:
        print(f"❌ {key} — отсутствует")
        missing.append(key)
    else:
        print(f"✅ {key} — найден")

if missing:
    print("\n⚠️ Отсутствуют ключевые переменные, проверь .env!")
    sys.exit(1)

# === Проверка обновления токена ===
print("\n♻️ Проверка обновления токена...")
try:
    connector = CTraderConnector()
    token_data = connector.refresh_access_token()
    print("✅ Токен успешно обновлён.")
    print("   Новый access_token:", token_data.get("access_token", "")[:30] + "...")
except Exception as e:
    print(f"❌ Ошибка при обновлении токена: {e}")

# === Проверка загрузки данных ===
print("\n📈 Проверка загрузки свечей...")
try:
    df = connector.get_historical_data(symbol="US30", timeframe="M15", bars=10)
    if df.empty:
        print("⚠️ Свечи не получены — возможно, неверный account_id или токен.")
    else:
        print("✅ Данные получены успешно:")
        print(df.head())
except Exception as e:
    print(f"❌ Ошибка получения данных: {e}")

print("\n✅ Диагностика завершена.")
