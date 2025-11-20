import json
import re
from typing import Dict, Any


def parse_tradingview_email(subject: str, body: str) -> Dict[str, Any]:
    """Парсинг письма от TradingView. Поддерживает JSON и текст."""
    subject = subject or ""
    body = body or ""

    # Пробуем прочитать JSON
    try:
        data = json.loads(body)
        return {
            "raw_subject": subject,
            "raw_body": body,
            "symbol": data.get("symbol") or data.get("ticker"),
            "direction": data.get("direction") or data.get("side"),
            "price": data.get("price"),
            "time": data.get("time"),
            "strategy": data.get("strategy"),
            "extra": data,
        }
    except:
        pass

    # Если не JSON, вытаскиваем символ + направление
    symbol = None
    dir_ = None

    m1 = re.search(r"(US30|XAUUSD|SPX500|NAS100|DE40|[A-Z]{3,10})", body)
    if m1:
        symbol = m1.group(1)

    m2 = re.search(r"\b(BUY|SELL|LONG|SHORT)\b", body, flags=re.IGNORECASE)
    if m2:
        dir_ = m2.group(1).upper()

    return {
        "raw_subject": subject,
        "raw_body": body,
        "symbol": symbol,
        "direction": dir_,
        "price": None,
        "time": None,
        "strategy": None,
        "extra": {"fallback": True},
    }
