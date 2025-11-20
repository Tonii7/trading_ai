# -*- coding: utf-8 -*-
"""
kb_sync.py — удобный запуск синхронизации базы знаний:
1) при необходимости копирует последний отчёт в knowledge_base/reports/
2) пересобирает векторный индекс (вызывает kb_index.build_index)
"""

import os
import shutil
import datetime
import sys

# --- пути такие же, как в kb_index/kb_search ---

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))      # .../src/trading_ai/tools
TRADING_AI_DIR = os.path.dirname(TOOLS_DIR)                 # .../src/trading_ai
SRC_DIR = os.path.dirname(TRADING_AI_DIR)                   # .../src
PROJECT_ROOT = os.path.dirname(SRC_DIR)                     # .../trading_ai

KNOWLEDGE_BASE_DIR = os.path.join(PROJECT_ROOT, "knowledge_base")
REPORTS_IN_KB_DIR = os.path.join(KNOWLEDGE_BASE_DIR, "reports")
LAST_REPORT_PATH = os.path.join(PROJECT_ROOT, "last_report.txt")

# чтобы импортировать trading_ai.tools.kb_index
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

try:
    from trading_ai.tools.kb_index import build_index
except Exception as e:
    print("❌ Cannot import build_index from trading_ai.tools.kb_index:", e)
    sys.exit(1)


def sync_last_report_into_kb():
    """Кладём last_report.txt в knowledge_base/reports с датой в имени."""
    if not os.path.exists(LAST_REPORT_PATH):
        print("ℹ️ last_report.txt not found, skipping report sync.")
        return

    os.makedirs(REPORTS_IN_KB_DIR, exist_ok=True)

    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    target_name = f"report_{date_str}.txt"
    target_path = os.path.join(REPORTS_IN_KB_DIR, target_name)

    shutil.copy2(LAST_REPORT_PATH, target_path)
    print(f"💾 last_report.txt copied into knowledge_base/reports as {target_name}")


def main():
    print("🔄 KB Sync started")
    print("  PROJECT_ROOT:", PROJECT_ROOT)
    print("  KNOWLEDGE_BASE_DIR:", KNOWLEDGE_BASE_DIR)

    # 1) синхронизируем последний отчёт
    sync_last_report_into_kb()

    # 2) пересобираем индекс
    print("🧠 Rebuilding vector index via kb_index.build_index() ...")
    build_index()
    print("✅ KB Sync completed")


if __name__ == "__main__":
    main()
