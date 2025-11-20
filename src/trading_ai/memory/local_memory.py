# ===========================================================
# local_memory.py — простая независимая реализация памяти агентов
# ===========================================================
import os
import json
from datetime import datetime


class LocalMemory:
    """Файловая память агента (без crewai зависимостей)."""

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def add(self, key: str, value: str):
        """Добавить запись в память"""
        data = self._load()
        data[key] = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get(self, key: str):
        """Получить запись"""
        data = self._load()
        return data.get(key, {}).get("value")

    def all(self):
        """Все записи"""
        return self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
