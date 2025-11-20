import argparse
import shutil
from pathlib import Path
import os

# -------------------------------
# Настройки
# -------------------------------

ROOT = Path(__file__).parent.resolve()

# Файлы в корне, которые переносим в services/ctrader
CTRADER_ROOT_FILES = [
    "ctrader_account_data.py",
    "ctrader_account_info.py",
    "ctrader_candles_data.py",
    "ctrader_openapi_client.py",
    "ctrader_symbols_data.py",
    "ctrader_symbol_details.py",
    "get_ctrader_token.py",
    "inspect_ctrader_client.py",
]

# Дашборды в корне -> dashboards
DASHBOARD_ROOT_FILES = [
    "dashboard_crewai.py",
    "dashboard_main.py",
    "dashboard_reports.py",
]

# Пайплайны в корне -> pipelines
PIPELINE_ROOT_FILES = [
    "agent_data_pipeline.py",
    "pipeline.py",
]

# Папка с кодом для векторизации
KB_CODE_DIR = ROOT / "knowledge_base" / "code"
VECTORIZED_TARGET_DIR = ROOT / "src" / "trading_ai" / "knowledge" / "vectorized_sources"


# -------------------------------
# Вспомогательные функции
# -------------------------------

def ensure_dirs():
    """Создаём нужные директории, если их ещё нет."""
    (ROOT / "src" / "trading_ai" / "services" / "ctrader").mkdir(parents=True, exist_ok=True)
    (ROOT / "src" / "trading_ai" / "services" / "gmail").mkdir(parents=True, exist_ok=True)
    (ROOT / "src" / "trading_ai" / "services" / "telegram").mkdir(parents=True, exist_ok=True)
    (ROOT / "src" / "trading_ai" / "services" / "tradingview").mkdir(parents=True, exist_ok=True)
    (ROOT / "src" / "trading_ai" / "dashboards").mkdir(parents=True, exist_ok=True)
    (ROOT / "src" / "trading_ai" / "pipelines").mkdir(parents=True, exist_ok=True)
    (ROOT / "src" / "trading_ai" / "knowledge").mkdir(parents=True, exist_ok=True)
    VECTORIZED_TARGET_DIR.mkdir(parents=True, exist_ok=True)


def move_file(src_rel: str, dst_rel: str, dry_run: bool):
    src = ROOT / src_rel
    dst = ROOT / dst_rel

    if not src.exists():
        print(f"[skip] {src_rel} не найден")
        return

    dst.parent.mkdir(parents=True, exist_ok=True)

    if dry_run:
        print(f"[DRY-RUN] Переместить {src_rel} -> {dst_rel}")
    else:
        print(f"[MOVE] {src_rel} -> {dst_rel}")
        shutil.move(str(src), str(dst))


def copy_kb_code(dry_run: bool):
    """Копируем файлы из knowledge_base/code в src/trading_ai/knowledge/vectorized_sources."""
    if not KB_CODE_DIR.exists():
        print(f"[skip] Папка {KB_CODE_DIR} не найдена, пропускаю перенос vectoized_sources")
        return

    for item in KB_CODE_DIR.iterdir():
        if item.is_file() and item.suffix == ".py":
            dst = VECTORIZED_TARGET_DIR / item.name
            if dry_run:
                print(f"[DRY-RUN] Скопировать {item.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
            else:
                print(f"[COPY] {item.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
                shutil.copy2(str(item), str(dst))


def rewrite_imports(dry_run: bool):
    """
    Обновляем импорты для перенесённых модулей.
    Делаем очень аккуратно: смотрим только на строки, которые НАЧИНАЮТСЯ с нужных import/from.
    """

    # Модули, которые уехали в services/ctrader
    ctrader_modules = [
        "ctrader_account_data",
        "ctrader_account_info",
        "ctrader_candles_data",
        "ctrader_openapi_client",
        "ctrader_symbols_data",
        "ctrader_symbol_details",
        "get_ctrader_token",
        "inspect_ctrader_client",
    ]

    # Дашборды
    dashboard_modules = [
        "dashboard_crewai",
        "dashboard_main",
        "dashboard_reports",
    ]

    # Пайплайны
    pipeline_modules = [
        "agent_data_pipeline",
        "pipeline",
    ]

    python_files = list(ROOT.rglob("*.py"))

    for file_path in python_files:
        # Не трогаем миграционный скрипт
        if file_path.name == "migrate_project.py":
            continue

        rel = file_path.relative_to(ROOT)
        text = file_path.read_text(encoding="utf-8")

        lines = text.splitlines()
        changed = False
        new_lines = []

        for line in lines:
            stripped = line.lstrip()

            # --- cTrader modules ---
            for mod in ctrader_modules:
                # import ctrader_account_info
                if stripped.startswith(f"import {mod}"):
                    new_line = line.replace(f"import {mod}",
                                            f"from trading_ai.services.ctrader import {mod}")
                    if new_line != line:
                        changed = True
                        line = new_line

                # from ctrader_account_info import X
                if stripped.startswith(f"from {mod} import "):
                    new_line = line.replace(f"from {mod} import ",
                                            f"from trading_ai.services.ctrader.{mod} import ")
                    if new_line != line:
                        changed = True
                        line = new_line

            # --- dashboards ---
            for mod in dashboard_modules:
                if stripped.startswith(f"import {mod}"):
                    new_line = line.replace(f"import {mod}",
                                            f"from trading_ai.dashboards import {mod}")
                    if new_line != line:
                        changed = True
                        line = new_line

                if stripped.startswith(f"from {mod} import "):
                    new_line = line.replace(f"from {mod} import ",
                                            f"from trading_ai.dashboards.{mod} import ")
                    if new_line != line:
                        changed = True
                        line = new_line

            # --- pipelines ---
            for mod in pipeline_modules:
                if stripped.startswith(f"import {mod}"):
                    new_line = line.replace(f"import {mod}",
                                            f"from trading_ai.pipelines import {mod}")
                    if new_line != line:
                        changed = True
                        line = new_line

                if stripped.startswith(f"from {mod} import "):
                    new_line = line.replace(f"from {mod} import ",
                                            f"from trading_ai.pipelines.{mod} import ")
                    if new_line != line:
                        changed = True
                        line = new_line

            new_lines.append(line)

        if changed:
            if dry_run:
                print(f"[DRY-RUN] Обновить импорты в {rel}")
            else:
                print(f"[UPDATE] Обновляем импорты в {rel}")
                file_path.write_text("\n".join(new_lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Миграция структуры проекта trading_ai")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Выполнить реальные изменения (по умолчанию только dry-run)",
    )
    args = parser.parse_args()

    dry_run = not args.apply

    print(f"ROOT: {ROOT}")
    print(f"Режим: {'DRY-RUN (только показ действий)' if dry_run else 'APPLY (выполняем изменения)'}")
    print("-" * 60)

    ensure_dirs()

    # 1) Перенос cTrader файлов
    for fname in CTRADER_ROOT_FILES:
        move_file(fname, f"src/trading_ai/services/ctrader/{fname}", dry_run=dry_run)

    # 2) Перенос dashboards
    for fname in DASHBOARD_ROOT_FILES:
        move_file(fname, f"src/trading_ai/dashboards/{fname}", dry_run=dry_run)

    # 3) Перенос pipelines
    for fname in PIPELINE_ROOT_FILES:
        move_file(fname, f"src/trading_ai/pipelines/{fname}", dry_run=dry_run)

    # 4) Копирование кода для векторизации
    copy_kb_code(dry_run=dry_run)

    # 5) Обновление импортов
    rewrite_imports(dry_run=dry_run)

    print("-" * 60)
    print("Готово. Если всё ок в DRY-RUN — запусти ещё раз с флагом --apply.")


if __name__ == "__main__":
    main()
