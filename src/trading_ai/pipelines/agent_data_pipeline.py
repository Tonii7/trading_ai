"""
agent_data_pipeline.py — единый центр данных для CrewAI агентов
---------------------------------------------------------------
✅ Загружает данные от:
   - ctrader_symbol_details.py  (Meta Agent)
   - ctrader_candles_data.py    (Data Agent)
✅ Объединяет и векторизует данные в один DataFrame
✅ Готовит JSON/CSV для CrewAI, Telegram, ML и визуализации
"""

import os
import json
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────────
# 1. Пути
# ─────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data_pipeline")
os.makedirs(DATA_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# 2. Загрузка CSV свечей
# ─────────────────────────────────────────────
def load_candle_data(symbol="US30"):
    """
    Загружает все CSV с данными свечей по разным таймфреймам.
    """
    frames = []
    for tf in ["M5", "M15", "M30", "H1", "H4", "D1"]:
        path = os.path.join(BASE_DIR, f"{symbol}_{tf}_candles.csv")
        if not os.path.exists(path):
            print(f"⚠️ Нет данных для {tf}")
            continue

        df = pd.read_csv(path)
        df["tf"] = tf
        frames.append(df)

    if not frames:
        raise FileNotFoundError("❌ Нет файлов свечей. Сначала запусти ctrader_candles_data.py")

    combined = pd.concat(frames, ignore_index=True)
    print(f"✅ Загружено {len(combined)} строк свечей по всем ТФ.")
    return combined


# ─────────────────────────────────────────────
# 3. Загрузка метаданных символа
# ─────────────────────────────────────────────
def load_symbol_meta(symbol="US30"):
    """
    Загружает метаданные символа из JSON.
    """
    meta_path = os.path.join(BASE_DIR, f"{symbol}_meta.json")

    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        print(f"✅ Загрузка метаданных {symbol} из {meta_path}")
        return meta
    else:
        print("⚠️ Метаданные не найдены, создаём временную заглушку.")
        return {
            "symbol": symbol,
            "lotSize": 100,
            "swapLong": -111.91,
            "swapShort": -1.42,
            "leverageId": 1019,
            "timezone": "America/Chicago"
        }


# ─────────────────────────────────────────────
# 4. Формирование сводного DataFrame
# ─────────────────────────────────────────────
def build_dataset(symbol="US30"):
    candles = load_candle_data(symbol)
    meta = load_symbol_meta(symbol)

    # Пример базовых инженерных фич
    candles["body_size"] = abs(candles["close"] - candles["open"])
    candles["upper_shadow"] = candles["high"] - candles[["close", "open"]].max(axis=1)
    candles["lower_shadow"] = candles[["close", "open"]].min(axis=1) - candles["low"]
    candles["range"] = candles["high"] - candles["low"]

    # Привязка метаданных к свечам
    for k, v in meta.items():
        candles[k] = v

    # Сохраняем результат
    output_path = os.path.join(DATA_DIR, f"{symbol}_combined_dataset.csv")
    candles.to_csv(output_path, index=False)
    print(f"💾 Dataset сохранён: {output_path}")

    return candles


# ─────────────────────────────────────────────
# 5. Экспорт JSON для CrewAI агентов
# ─────────────────────────────────────────────
def export_for_agents(df, symbol="US30"):
    """
    Формирует лёгкий JSON-файл с актуальными фичами для CrewAI Data/Meta Agents.
    """
    export = {
        "symbol": symbol,
        "records": len(df),
        "updated": datetime.now().isoformat(),
        "preview": df.head(5).to_dict(orient="records"),
        "columns": list(df.columns)
    }

    export_path = os.path.join(DATA_DIR, f"{symbol}_crew_feed.json")
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(export, f, ensure_ascii=False, indent=2)

    print(f"🤖 CrewAI JSON экспортирован → {export_path}")


# ─────────────────────────────────────────────
# 6. Основной запуск
# ─────────────────────────────────────────────
if __name__ == "__main__":
    symbol = "US30"
    df = build_dataset(symbol)
    export_for_agents(df, symbol)
    print("✅ Полный цикл Data → Meta → CrewAI завершён.")
