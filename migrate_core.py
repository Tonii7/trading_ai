import shutil
from pathlib import Path
import argparse

ROOT = Path(__file__).parent.resolve()
SRC_DIR = ROOT / "src" / "trading_ai"
CORE_DIR = SRC_DIR / "core"

# какие файлы переносим в core
CORE_FILES = [
    "crew.py",
    "main.py",
    "orchestrator.py",
    "memory_status.py",
    "report_viewer.py",
]

def ensure_dirs():
    CORE_DIR.mkdir(exist_ok=True, parents=True)

def move_core_files(dry_run=False):
    for fname in CORE_FILES:
        src = SRC_DIR / fname
        dst = CORE_DIR / fname

        if not src.exists():
            print(f"[skip] {fname} не найден")
            continue

        if dry_run:
            print(f"[DRY-RUN] Переместить {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
        else:
            print(f"[MOVE] {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
            shutil.move(str(src), str(dst))


def rewrite_imports(dry_run=False):
    """
    Обновляем импорты:
    from trading_ai.crew import X
    →
    from trading_ai.core.crew import X
    """

    python_files = list(ROOT.rglob("*.py"))

    replacements = [
        # старый импорт → новый
        ("from trading_ai.crew", "from trading_ai.core.crew"),
        ("import trading_ai.crew", "import trading_ai.core.crew"),

        ("from trading_ai.main", "from trading_ai.core.main"),
        ("import trading_ai.main", "import trading_ai.core.main"),

        ("from trading_ai.orchestrator", "from trading_ai.core.orchestrator"),
        ("import trading_ai.orchestrator", "import trading_ai.core.orchestrator"),

        ("from trading_ai.memory_status", "from trading_ai.core.memory_status"),
        ("import trading_ai.memory_status", "import trading_ai.core.memory_status"),

        ("from trading_ai.report_viewer", "from trading_ai.core.report_viewer"),
        ("import trading_ai.report_viewer", "import trading_ai.core.report_viewer"),
    ]

    for file in python_files:

        if file.name == "migrate_core.py":
            continue

        text = file.read_text(encoding="utf-8")
        new_text = text

        for old, new in replacements:
            new_text = new_text.replace(old, new)

        if new_text != text:
            if dry_run:
                print(f"[DRY-RUN] Обновить импорты в {file.relative_to(ROOT)}")
            else:
                print(f"[UPDATE] Обновляю импорты в {file.relative_to(ROOT)}")
                file.write_text(new_text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Перенос ядра trading_ai в src/trading_ai/core/")
    parser.add_argument("--apply", action="store_true", help="Применить изменения")
    args = parser.parse_args()

    dry_run = not args.apply

    print(f"ROOT: {ROOT}")
    print(f"Режим: {'DRY-RUN' if dry_run else 'APPLY'}")
    print("-" * 50)

    ensure_dirs()
    move_core_files(dry_run=dry_run)
    rewrite_imports(dry_run=dry_run)

    print("-" * 50)
    print("ГОТОВО. Если всё ок в DRY-RUN → запусти с --apply")


if __name__ == "__main__":
    main()
