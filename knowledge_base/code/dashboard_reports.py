import json
import os
import streamlit as st
import pandas as pd
from datetime import datetime

from src.trading_ai.analytics.report_definitions import METRIC_DEFINITIONS

REPORTS_DIR = "reports"
HISTORY_PATH = os.path.join(REPORTS_DIR, "history.json")

st.set_page_config(page_title="Trading Strategy Dashboard", layout="wide")

st.title("📊 Trading AI — Strategy Dashboard")
st.markdown("Аналитика стратегий и отчёты Eldar Capital AI Research")

# ---------- 1️⃣ Проверяем наличие отчётов ----------
if not os.path.exists(HISTORY_PATH):
    st.warning("⚠️ Пока нет сохранённых отчётов. Запусти compare_strategies.py, чтобы создать первый отчёт.")
    st.stop()

with open(HISTORY_PATH, "r", encoding="utf-8") as f:
    history = json.load(f)

# ---------- 2️⃣ Выбор отчёта ----------
options = [f"{i+1}. {h['timestamp']} — {', '.join(h['strategies'])}" for i, h in enumerate(history)]
choice = st.selectbox("Выбери отчёт:", options)
idx = int(choice.split(".")[0]) - 1
report = history[idx]

st.markdown(f"### 🗓️ Отчёт от {report['timestamp']}")
st.markdown(f"**Стратегии:** {', '.join(report['strategies'])}")

# ---------- 3️⃣ Таблица результатов ----------
results_df = pd.DataFrame(report["results"])
st.subheader("📈 Результаты стратегий")
st.dataframe(results_df, use_container_width=True)

# ---------- 4️⃣ Метрики ----------
st.subheader("📘 Определения метрик")
for metric, desc in METRIC_DEFINITIONS.items():
    st.markdown(f"- **{metric}:** {desc}")

# ---------- 5️⃣ Просмотр отчёта ----------
if "html" in report["report_paths"] and os.path.exists(report["report_paths"]["html"]):
    st.subheader("🌐 Просмотр HTML-отчёта")
    with open(report["report_paths"]["html"], "r", encoding="utf-8") as f:
        html_content = f.read()
    st.components.v1.html(html_content, height=600, scrolling=True)
else:
    st.info("HTML-отчёт не найден для этого отчёта.")

# ---------- 6️⃣ PNG график ----------
if "png" in report["report_paths"] and os.path.exists(report["report_paths"]["png"]):
    st.subheader("🖼️ График Equity Curves")
    st.image(report["report_paths"]["png"], caption="Equity Curves", use_column_width=True)
