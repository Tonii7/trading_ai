# ==============================================
# src/trading_ai/reports/full_report.py
# Интегрированный отчёт: техника + макро + агенты
# ==============================================

from __future__ import annotations

import os
import json
from pathlib import Path
from datetime import datetime


# ---- Базовые пути ----

THIS_FILE = Path(__file__).resolve()
REPORTS_DIR = THIS_FILE.parents[3] / "reports"   # .../trading_ai/reports -> parents[3] = root /reports
ROOT_DIR = THIS_FILE.parents[3]                  # корень проекта (там, где .env, reports, src, data)
DATA_DIR = ROOT_DIR / "data"


def _read_text_if_exists(path: Path, title: str) -> str:
    """Читает текстовый файл, если есть. Возвращает HTML-блок."""
    if not path.exists():
        return f"<h3>{title}</h3><p><i>Нет данных ({path})</i></p>"

    with path.open("r", encoding="utf-8") as f:
        content = f.read()

    # оборачиваем в <pre> для сохранения форматирования
    return f"""
    <h3>{title}</h3>
    <pre>{content}</pre>
    """


def _read_fred_block() -> str:
    """Читает data/fred_snapshot.json и формирует HTML-блок с макро."""
    snapshot_path = DATA_DIR / "fred_snapshot.json"
    if not snapshot_path.exists():
        return "<h3>🌍 Macro (FRED)</h3><p><i>Нет данных (запусти FredAgent)</i></p>"

    try:
        with snapshot_path.open("r", encoding="utf-8") as f:
            snap = json.load(f)
    except Exception as e:
        return f"<h3>🌍 Macro (FRED)</h3><p><i>Ошибка чтения fred_snapshot.json: {e}</i></p>"

    ts = snap.get("timestamp", "unknown")
    raw = snap.get("data", {}).get("Raw", {})
    comp = snap.get("data", {}).get("Computed", {})

    lines_raw = []
    for k, v in raw.items():
        lines_raw.append(f"<li><b>{k}</b>: {v}</li>")
    raw_html = "\n".join(lines_raw) or "<li><i>нет данных</i></li>"

    lines_comp = []
    for k, v in comp.items():
        lines_comp.append(f"<li><b>{k}</b>: {v}</li>")
    comp_html = "\n".join(lines_comp) or "<li><i>нет данных</i></li>"

    return f"""
    <h3>🌍 Macro (FRED snapshot)</h3>
    <p><b>Timestamp (UTC):</b> {ts}</p>
    <h4>Raw indicators</h4>
    <ul>
      {raw_html}
    </ul>
    <h4>Computed indicators (MacroFormulas)</h4>
    <ul>
      {comp_html}
    </ul>
    """


def _metrics_glossary_block() -> str:
    """Справочник метрик (описания)."""
    return """
    <h2>📚 Metrics Glossary (словарь метрик)</h2>
    <ul>
      <li><b>Total return</b> — общая доходность за период, в %.</li>
      <li><b>Annual return</b> — годовая приведённая доходность, в %.</li>
      <li><b>Annual volatility</b> — годовая волатильность доходности, в %.</li>
      <li><b>Sharpe ratio</b> — (доходность - безрисковая ставка) / волатильность. Чем выше, тем лучше.</li>
      <li><b>Max drawdown</b> — максимальная просадка от пика до минимума, в %.</li>
      <li><b>Real interest rate</b> — реальная ставка: nominal_rate - inflation.</li>
      <li><b>Yield curve spread</b> — разница доходностей (например, 10Y - Fed Funds). Отрицательная — сигнал стресса/инверсии.</li>
      <li><b>Recession probability</b> — эвристическая оценка вероятности рецессии по спреду кривой доходности.</li>
      <li><b>Money velocity</b> — скорость обращения денег: GDP / M2.</li>
      <li><b>Macro health index</b> — агрегированный показатель “здоровья экономики” на основе real rate и yield spread.</li>
    </ul>
    """


def build_full_market_report(
    market_name: str = "US30 / XAUUSD / SPX500",
    backtest_report_path: Path | None = None,
) -> str:
    """
    Собирает один большой HTML-отчёт:
      - заголовок дня
      - макро из FRED
      - текстовый отчёт агентов (last_report.txt)
      - технич. отчёт (full_chain_report.txt или другой)
      - словарь метрик
    """

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ---- макро блок ----
    fred_block = _read_fred_block()

    # ---- текст от CrewAI агентов ----
    crew_path = ROOT_DIR / "last_report.txt"
    crew_block = _read_text_if_exists(crew_path, "🧠 CrewAI daily report (Supervisor & agents)")

    # ---- технич. отчёт (backtest) ----
    if backtest_report_path is None:
        backtest_report_path = REPORTS_DIR / "full_chain_report.txt"
    backtest_block = _read_text_if_exists(backtest_report_path, "📈 Technical / Backtest report")

    glossary_block = _metrics_glossary_block()

    # ---- финальный HTML ----
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <title>Full Market Report — {market_name}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 20px;
      line-height: 1.5;
      background-color: #0b1020;
      color: #f5f5f5;
    }}
    h1, h2, h3, h4 {{
      color: #ffffff;
    }}
    .container {{
      max-width: 1100px;
      margin: 0 auto;
      background: #111827;
      padding: 20px 30px;
      border-radius: 14px;
      box-shadow: 0 0 30px rgba(0,0,0,0.5);
    }}
    pre {{
      background: #020617;
      padding: 12px 16px;
      border-radius: 10px;
      overflow-x: auto;
      font-size: 13px;
      color: #e5e7eb;
    }}
    ul {{
      margin-left: 20px;
    }}
    .section {{
      margin-bottom: 30px;
      padding-bottom: 10px;
      border-bottom: 1px solid #1f2937;
    }}
    .tagline {{
      color: #9ca3af;
      font-size: 14px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Full Market Report — {market_name}</h1>
    <p class="tagline">Generated at: {now}</p>

    <div class="section">
      {fred_block}
    </div>

    <div class="section">
      {crew_block}
    </div>

    <div class="section">
      {backtest_block}
    </div>

    <div class="section">
      {glossary_block}
    </div>

  </div>
</body>
</html>
"""
    return html


def save_full_market_report(html: str) -> Path:
    """Сохраняет HTML в папку reports и возвращает путь."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_path = REPORTS_DIR / f"full_market_report_{ts}.html"
    with out_path.open("w", encoding="utf-8") as f:
        f.write(html)
    return out_path


if __name__ == "__main__":
    # Тест: просто собрать отчёт и вывести путь
    report_html = build_full_market_report()
    path = save_full_market_report(report_html)
    print(f"✅ Full market report saved to: {path}")
