# dashboard.py (заменить существующий файл целиком)
import streamlit as st
import os
import subprocess
import datetime
from pathlib import Path

# Импорты инструментов твоего проекта
# (предполагается, что venv активирован и путь корректен)
from src.trading_ai.tools.custom_tool import get_live_data, get_news

st.set_page_config(page_title="Trading AI Dashboard", layout="wide")
st.title("📊 Trading AI Dashboard")

# ----------------- SIDEBAR -----------------
st.sidebar.header("⚙️ Controls")

# Run CrewAI button (launch background process)
if "crew_process" not in st.session_state:
    st.session_state.crew_process = None
if "crew_last_started" not in st.session_state:
    st.session_state.crew_last_started = None

run_now = st.sidebar.button("▶️ Run CrewAI now")
refresh = st.sidebar.button("🔁 Refresh data")
auto_minutes = st.sidebar.number_input("Auto refresh (minutes)", min_value=0, max_value=60, value=5)

# If user clicked Run CrewAI -> spawn background process
if run_now:
    # spawn CrewAI as a background process; do not block Streamlit
    try:
        # use python -m to ensure module imports work
        p = subprocess.Popen(
            ["python", "-m", "src.trading_ai.main"],
            cwd=os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        st.session_state.crew_process = p
        st.session_state.crew_last_started = datetime.datetime.utcnow().isoformat()
        st.sidebar.success("CrewAI started (background).")
    except Exception as e:
        st.sidebar.error(f"Failed to start CrewAI: {e}")

# Show process status (if any)
if st.session_state.get("crew_process"):
    proc = st.session_state.crew_process
    if proc.poll() is None:
        st.sidebar.info("CrewAI status: running")
    else:
        st.sidebar.info("CrewAI status: finished")
        # optionally read stdout/stderr
        try:
            out, err = proc.communicate(timeout=0.1)
            if out:
                st.sidebar.text("CrewAI stdout:")
                st.sidebar.code(out.decode(errors="ignore")[:1000])
            if err:
                st.sidebar.text("CrewAI stderr:")
                st.sidebar.code(err.decode(errors="ignore")[:1000])
        except Exception:
            pass

if st.session_state.get("crew_last_started"):
    st.sidebar.caption(f"Last started (UTC): {st.session_state.crew_last_started}")

st.sidebar.caption("Use 'Run CrewAI now' to start agents and generate a new report.\nUse 'Refresh data' to re-fetch market data and news.")


# ----------------- DATA FETCH / CACHE -----------------
# caching: use a TTL driven by auto_minutes (0 -> no cache)
ttl = 60 * auto_minutes if auto_minutes > 0 else 0

@st.cache_data(ttl=ttl)
def cached_market_and_news():
    market = {}
    news = []
    try:
        market = get_live_data()
    except Exception as e:
        market = {}
    try:
        news = get_news()
    except Exception:
        news = []
    return market, news

# If user clicked Refresh -> clear cache and re-fetch
if refresh:
    st.cache_data.clear()
    market_data, news = cached_market_and_news()
else:
    market_data, news = cached_market_and_news()

# ----------------- LAYOUT -----------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 Market prices (live)")
    if market_data:
        # show a last-updated timestamp if available (take first symbol timestamp)
        timestamps = []
        for k, v in market_data.items():
            if v and isinstance(v, dict) and v.get("timestamp"):
                try:
                    # try to normalize timestamp if possible
                    timestamps.append(v.get("timestamp"))
                except Exception:
                    pass
        if timestamps:
            st.caption(f"Data timestamps (example): {timestamps[:3]}")
        # display metrics
        for name, val in market_data.items():
            if not val:
                st.write(f"**{name}** — Нет данных")
                continue
            # val expected: {"timestamp": "...", "close": 1234.56}
            price = val.get("close")
            ts = val.get("timestamp")
            if price is None:
                st.write(f"**{name}** — Нет данных")
            else:
                # format price nicely
                try:
                    price_str = f"{float(price):,.2f}"
                except Exception:
                    price_str = str(price)
                st.metric(label=name, value=price_str, delta=None)
                if ts:
                    st.caption(f"Timestamp: {ts}")

    else:
        st.info("Нет данных рынка. Убедись, что get_live_data() возвращает актуальные котировки.")

with col2:
    st.subheader("📰 Latest headlines")
    if news:
        for n in news:
            title = n.get("title") if isinstance(n, dict) else str(n)
            link = n.get("link") if isinstance(n, dict) else None
            if link:
                st.write("•", f"[{title}]({link})")
            else:
                st.write("•", title)
    else:
        st.info("Нет новостей.")

# ----------------- CrewAI report -----------------
st.divider()
st.subheader("📄 Last CrewAI Report")

report_path = os.path.join(os.getcwd(), "last_report.txt")
if os.path.exists(report_path):
    with open(report_path, "r", encoding="utf-8") as f:
        report_text = f.read()
    st.text_area("Latest report", value=report_text, height=300)
else:
    st.info("Пока нет отчёта. Нажми 'Run CrewAI now' или запусти agents вручную.")

st.caption(f"Dashboard updated: {datetime.datetime.utcnow().isoformat()} UTC")
