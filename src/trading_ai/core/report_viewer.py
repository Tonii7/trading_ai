"""
report_viewer.py — Streamlit-дашборд для просмотра отчётов Trading AI
--------------------------------------------------------------------
✅ Отображает последние отчёты (daily_report_*.json)
✅ Визуализирует котировки и прибыль советника
✅ Показывает последние новости и краткий анализ
"""

import os
import json
import pandas as pd
import streamlit as st
from datetime import datetime

# === ПУТИ ===
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
REPORTS_DIR = os.path.join(PROJECT_ROOT, "knowledge_base", "reports")

# === ЗАГРУЗКА ОТЧЁТОВ ===
def load_reports():
    files = sorted(
        [f for f in os.listdir(REPORTS_DIR) if f.startswith("daily_report_") and f.endswith(".json")],
        reverse=True
    )
    reports = []
    for f in files:
        try:
            with open(os.path.join(REPORTS_DIR, f), "r", encoding="utf-8") as rf:
                data = json.load(rf)
                reports.append((f, data))
        except Exception as e:
            st.warning(f"Не удалось загрузить {f}: {e}")
    return reports

# === UI ===
st.set_page_config(page_title="Trading AI Dashboard", page_icon="📊", layout="wide")
st.title("📈 Trading AI — Dashboard Отчётов")

reports = load_reports()
if not reports:
    st.error("Нет отчётов в knowledge_base/reports. Сначала запусти orchestrator.py.")
    st.stop()

# === Селектор отчёта ===
file_names = [r[0] for r in reports]
selected = st.selectbox("Выбери отчёт:", file_names)
report = dict(reports[file_names.index(selected)][1])

summary = report.get("summary_ru", {})
market = summary.get("рынок", {})
backtest = summary.get("бэктест", {})
news = summary.get("новости", [])
analysis = summary.get("анализ", "Нет анализа")

# === Отображение ===
st.header("🧭 Рыночный обзор")
cols = st.columns(5)
cols[0].metric("US30", market.get("us30"))
cols[1].metric("S&P 500", market.get("sp500"))
cols[2].metric("NASDAQ 100", market.get("nas100"))
cols[3].metric("DXY", market.get("dxy"))
cols[4].metric("Золото", market.get("золото"))

st.markdown("---")
st.subheader("💼 Результаты советника")
st.json(backtest)

st.markdown("---")
st.subheader("📰 Последние новости")
for n in news:
    st.write(f"• {n}")

st.markdown("---")
st.subheader("📊 Краткий анализ")
st.success(analysis)

# === Визуализация прибыли (если доступна) ===
if backtest.get("прибыль") is not None:
    pnl_data = pd.DataFrame({
        "Время": [datetime.fromisoformat(report["timestamp"])],
        "PnL": [backtest.get("прибыль")]
    })
    st.line_chart(pnl_data.set_index("Время"))

st.markdown("---")
st.caption(f"Обновлено: {report['timestamp']}")
