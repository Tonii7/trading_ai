import streamlit as st
from pathlib import Path

# ---------- НАСТРОЙКА ----------
st.set_page_config(page_title="Eldar Trading AI Dashboard", layout="wide")

st.title("💼 Eldar Trading AI — Unified Dashboard")
st.sidebar.title("📍 Навигация")

# ---------- ВКЛАДКИ ----------
page = st.sidebar.radio(
    "Выбери модуль:",
    [
        "📊 CrewAI Dashboard",
        "📈 Strategy Reports",
    ],
)

# ---------- ПЕРЕКЛЮЧЕНИЕ ----------
if page == "📊 CrewAI Dashboard":
    st.info("🔁 Загружается CrewAI панель...")
    dashboard_path = Path("dashboard_crewai.py")
    if dashboard_path.exists():
        with open(dashboard_path, "r", encoding="utf-8") as f:
            code = f.read()
        exec(code, globals())
    else:
        st.error("Файл dashboard_crewai.py не найден.")

elif page == "📈 Strategy Reports":
    st.info("📂 Загружается панель стратегий...")
    dashboard_path = Path("dashboard_reports.py")
    if dashboard_path.exists():
        with open(dashboard_path, "r", encoding="utf-8") as f:
            code = f.read()
        exec(code, globals())
    else:
        st.error("Файл dashboard_reports.py не найден.")
