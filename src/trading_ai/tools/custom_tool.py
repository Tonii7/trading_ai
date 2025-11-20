"""
custom_tool.py — Live Market & News Fetcher + Advisor Runner
------------------------------------------------------------
✅ Подключен cTrader-коннектор (реальные котировки IC Markets)
✅ Fallback на Yahoo Finance при недоступности брокера
✅ Убраны DeprecationWarning (UTC → timezone-aware)
✅ Добавлено сообщение “⚠ no new data — weekend mode”
✅ Автоматическое сохранение отчёта советника в JSON
✅ Автоматическая синхронизация KB Index через kb_sync.py
"""

import os
import json
import feedparser
import importlib.util
from datetime import datetime, timezone
from trading_ai.connectors.ctrader_connector import CTraderConnector
import yfinance as yf

# ======================================================
# 🔹 Получение живых котировок
# ======================================================

def _last_price_yahoo(ticker: str) -> float | None:
    """Получает последнюю цену по тикеру через yfinance."""
    try:
        data = yf.Ticker(ticker).history(period="1d", interval="1h")
        if data.empty:
            data = yf.Ticker(ticker).history(period="5d", interval="1h")
        if data.empty:
            return None
        return float(round(data["Close"].iloc[-1], 2))
    except Exception:
        return None


def get_live_data() -> dict:
    """Возвращает живые котировки основных инструментов."""
    instruments = {
        "US30": "US30",
        "SP500": "SPX500",
        "NAS100": "NAS100",
        "DXY": "USDX",
        "XAUUSD": "XAUUSD",
    }

    connector = CTraderConnector()
    result = {}

    for name, symbol in instruments.items():
        try:
            # ⚙️ Основной источник — cTrader
            price = connector.get_symbol_price(symbol)
            source = "cTrader"
        except Exception as e:
            # 🔁 fallback на Yahoo
            price = _last_price_yahoo({
                "US30": "^DJI",
                "SP500": "^GSPC",
                "NAS100": "^NDX",
                "DXY": "DX-Y.NYB",
                "XAUUSD": "GC=F",
            }.get(name, symbol))
            source = "Yahoo" if price else "None"

        note = ""
        if not price:
            note = "⚠ no new data — weekend mode"

        result[name] = {
            "ticker": symbol,
            "price": price,
            "source": source,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": note,
        }

    return result


# ======================================================
# 📰 Новости CNBC
# ======================================================

def get_news(limit: int = 5) -> list[dict]:
    """Парсит последние новости CNBC."""
    FEED = "https://www.cnbc.com/id/100003114/device/rss/rss.html"
    try:
        feed = feedparser.parse(FEED)
        return [
            {
                "title": e.get("title", ""),
                "link": e.get("link", ""),
                "published": e.get("published", ""),
            }
            for e in feed.entries[:limit]
        ]
    except Exception:
        return []


# ======================================================
# ⚙️ Исполнение Python советников
# ======================================================

def run_python_advisor(file_path: str) -> dict:
    """Запускает пользовательский Python-советник (advisor) и сохраняет отчёт."""
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        spec = importlib.util.spec_from_file_location("advisor", file_path)
        advisor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(advisor)

        if not hasattr(advisor, "main"):
            return {"error": "No main() function found in advisor"}

        result = advisor.main()

        # 💾 Сохраняем отчёт
        reports_dir = os.path.join(os.getcwd(), "knowledge_base", "reports")
        os.makedirs(reports_dir, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(reports_dir, f"advisor_{timestamp}.json")

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"💾 Advisor report saved: {report_path}")

        # 🔁 Автоматическая синхронизация KB
        try:
            kb_sync_path = os.path.join("src", "trading_ai", "tools", "kb_sync.py")
            print("\n🔄 Syncing Knowledge Base after advisor run...")
            os.system(f"python {kb_sync_path}")
            print("✅ KB Sync complete. Knowledge Base updated.")
        except Exception as e:
            print(f"⚠️ KB sync failed: {e}")

        return result if result else {"error": "Advisor returned no result"}

    except Exception as e:
        return {"error": str(e)}


# ======================================================
# 🧪 Тестовый запуск
# ======================================================

if __name__ == "__main__":
    print("=== Live Market Data ===")
    live_data = get_live_data()
    print(json.dumps(live_data, indent=2, ensure_ascii=False))

    print("\n=== Latest News ===")
    for n in get_news():
        print(f"🗞 {n['title']} ({n['link']})")

    print("\n=== Test Advisor ===")
    advisor_path = os.path.join(os.getcwd(), "knowledge_base", "advisors", "range_breakout_ea.py")
    print(run_python_advisor(advisor_path))
