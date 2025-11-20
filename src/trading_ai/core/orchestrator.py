"""
orchestrator.py — полный цикл анализа рынка
-------------------------------------------
✅ Объединяет все инструменты системы
✅ Работает с советником (main)
✅ Генерирует краткий отчёт и анализ на русском
✅ Сохраняет JSON и запускает KB Sync
✅ Готов к интеграции со Streamlit или Telegram
"""

import os
import sys
import json
import importlib.util
from datetime import datetime, timezone

# === ДОБАВЛЯЕМ sys.path ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, os.path.join(SRC_DIR, "trading_ai"))

print("🧩 sys.path patched. Current search paths:")
for p in sys.path[:3]:
    print("  ", p)

from trading_ai.tools.custom_tool import get_live_data, get_news

# === ПУТИ ===
REPORTS_DIR = os.path.join(PROJECT_ROOT, "knowledge_base", "reports")
ADVISOR_PATH = os.path.join(PROJECT_ROOT, "knowledge_base", "advisors", "range_breakout_ea.py")

# === ЗАГРУЗКА СОВЕТНИКА ===
def load_python_advisor(path: str):
    """Импортирует советник и вызывает main()."""
    try:
        spec = importlib.util.spec_from_file_location("advisor_module", path)
        advisor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(advisor)
        if hasattr(advisor, "main"):
            return advisor.main()
        else:
            return {"error": "main() function not found in advisor"}
    except Exception as e:
        return {"error": str(e)}

# === ФОРМИРОВАНИЕ КРАТКОГО АНАЛИЗА ===
def summarize_market(live_data: dict, advisor_result: dict) -> str:
    """Создаёт короткое резюме рынка на русском."""
    us30 = live_data.get("US30", {}).get("price", 0)
    sp500 = live_data.get("SP500", {}).get("price", 0)
    nas100 = live_data.get("NAS100", {}).get("price", 0)
    gold = live_data.get("XAUUSD", {}).get("price", 0)
    dxy = live_data.get("DXY", {}).get("price", 0)
    pnl = advisor_result.get("total_pnl", 0)
    win_rate = advisor_result.get("win_rate", 0)

    trend = "восходящий" if us30 > 46000 and sp500 > 6500 else "нейтральный" if win_rate > 40 else "снижающийся"

    return (
        f"📈 Рынок показывает {trend} импульс. "
        f"US30 = {us30}, SP500 = {sp500}, NAS100 = {nas100}. "
        f"DXY = {dxy}, золото = {gold}. "
        f"Советник отработал с винрейтом {win_rate}% и результатом {pnl}$. "
        f"{'Положительная' if pnl > 0 else 'Отрицательная'} динамика за сессию."
    )

# === ОСНОВНОЙ ЦИКЛ ===
def main():
    print("🚀 Запуск полного цикла Trading AI\n")

    # === 1️⃣ Live-данные ===
    live = get_live_data()
    print("📊 Текущие котировки:")
    for k, v in live.items():
        print(f"  {k}: {v['price']} ({v['ticker']})")

    # === 2️⃣ Новости ===
    print("\n📰 Последние новости:")
    news = get_news(limit=3)
    for n in news:
        print(f"  • {n['title']}")

    # === 3️⃣ Советник ===
    print("\n💼 Запуск советника...")
    advisor_result = load_python_advisor(ADVISOR_PATH)
    print("   ✅ Советник отработал.")

    # === 4️⃣ Формируем отчёт ===
    backtest_summary = {
        "инструмент": advisor_result.get("symbol"),
        "сделок": advisor_result.get("total_trades"),
        "прибыль": advisor_result.get("total_pnl"),
        "винрейт": advisor_result.get("win_rate"),
        "комментарий": advisor_result.get("comment_ru"),
    }

    summary_text = summarize_market(live, advisor_result)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary_ru": {
            "рынок": {
                "us30": live.get("US30", {}).get("price"),
                "sp500": live.get("SP500", {}).get("price"),
                "nas100": live.get("NAS100", {}).get("price"),
                "золото": live.get("XAUUSD", {}).get("price"),
                "dxy": live.get("DXY", {}).get("price"),
            },
            "новости": [n["title"] for n in news],
            "бэктест": backtest_summary,
            "анализ": summary_text,
        },
    }

    # === 5️⃣ Сохранение ===
    os.makedirs(REPORTS_DIR, exist_ok=True)
    file_path = os.path.join(REPORTS_DIR, f"daily_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Отчёт сохранён: {file_path}")

    # === 6️⃣ KB Sync ===
    kb_sync_path = os.path.join(PROJECT_ROOT, "src", "trading_ai", "tools", "kb_sync.py")
    print("\n🔄 Обновляем базу знаний...")
    os.system(f"python {kb_sync_path}")

    print("\n✅ Полный цикл завершён успешно!")
    print("Отчёт на русском доступен в knowledge_base/reports.")

if __name__ == "__main__":
    main()
