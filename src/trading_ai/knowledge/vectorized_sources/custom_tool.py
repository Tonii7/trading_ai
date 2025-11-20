import os
import datetime as dt

import yfinance as yf
import feedparser


def get_live_data():
    """Простые котировки по нескольким тикерам (можно расширять)."""
    tickers = {
        "XAUUSD": "GC=F",     # Gold futures
        "US30": "^DJI",       # Dow Jones
        "SPX500": "^GSPC",    # S&P 500
    }

    data = {}
    end = dt.datetime.utcnow()
    start = end - dt.timedelta(days=2)

    for name, code in tickers.items():
        try:
            df = yf.download(code, start=start, end=end, interval="1h", progress=False)
            if df.empty:
                data[name] = None
                continue
            last = df["Close"].iloc[-1]
            prev = df["Close"].iloc[-2] if len(df) > 1 else last
            data[name] = {
                "code": code,
                "close": round(float(last), 2),
                "change": round(float(last - prev), 2),
            }
        except Exception:
            data[name] = None

    return data


def get_news():
    """Читает RSS-ленту (по умолчанию CNBC)."""
    feed_url = os.getenv(
        "NEWS_FEED_URL",
        "https://feeds.cnbc.com/rss/101282959",
    )
    feed = feedparser.parse(feed_url)
    news_items = []
    for entry in feed.entries[:10]:
        news_items.append(
            {
                "title": entry.get("title"),
                "link": entry.get("link"),
                "published": entry.get("published", ""),
            }
        )
    return news_items
