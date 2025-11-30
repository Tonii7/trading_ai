from pathlib import Path
from typing import Any, Dict
import yaml

from trading_ai.services.discord.discord_sender import send_discord_embed_via_service

CURRENT_FILE = Path(__file__).resolve()
TRADING_AI_DIR = CURRENT_FILE.parents[2]
CONFIG_PATH = TRADING_AI_DIR / "config" / "output_routes.yaml"

if not CONFIG_PATH.exists():
    raise FileNotFoundError(f"❌ output_routes.yaml не найден: {CONFIG_PATH}")

with CONFIG_PATH.open("r", encoding="utf-8") as f:
    data = yaml.safe_load(f) or {}

ROUTES: Dict[str, Dict[str, Any]] = data.get("routes", {})

print(f"[Router] Loaded routes from {CONFIG_PATH}")


def dispatch(route_key: str, title: str, content: str) -> None:

    route_cfg = ROUTES.get(route_key)
    if not route_cfg:
        print(f"[Router] ❌ Unknown route: {route_key}")
        return

    discord_channel_key = route_cfg.get("discord")
    if not discord_channel_key:
        print(f"[Router] ❌ No discord mapping for route: {route_key}")
        return

    send_discord_embed_via_service(discord_channel_key, title, content)
