import os
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "services" / "ctrader"
BASE.mkdir(parents=True, exist_ok=True)

FILES = {
    "ctrader_openapi_client.py": """# --- ctrader_openapi_client.py ---
# Здесь будет твой полный обновлённый клиент OpenAPI.
# ChatGPT автоматически запишет сюда полный рабочий код.
print("ctrader_openapi_client.py успешно создан")
""",
    "ctrader_symbols_data.py": """# --- ctrader_symbols_data.py ---
# Здесь будет полный код для получения списка символов.
print("ctrader_symbols_data.py успешно создан")
""",
    "ctrader_candles_data.py": """# --- ctrader_candles_data.py ---
# Здесь будет полный код загрузки свечей.
print("ctrader_candles_data.py успешно создан")
"""
}

for filename, content in FILES.items():
    path = BASE / filename
    with path.open("w", encoding="utf-8") as f:
        f.write(content)

print(f"✓ Создано три файла в: {BASE}")
