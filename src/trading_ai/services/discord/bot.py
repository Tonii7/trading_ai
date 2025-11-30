# ───────────────────────────────────────
# Автоконфигурация путей для Windows Service
# ───────────────────────────────────────
import os
import sys

with open("ABSOLUTE_DEBUG.txt", "w", encoding="utf-8") as f:
    f.write("BOT.PY HAS STARTED\n")
    f.write("THIS FILE: " + os.path.abspath(__file__) + "\n")
    f.write("PYTHON EXECUTABLE: " + sys.executable + "\n")
    f.write("WORKING DIR: " + os.getcwd() + "\n")
    f.write("SYS.PATH:\n")
    for p in sys.path:
        f.write(" - " + str(p) + "\n")

import sys
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()

# ───────────────────────────────────────
# Основные импорты
# ───────────────────────────────────────
import os
import asyncio
import traceback
from aiohttp import web
import discord
from discord.ext import commands
from dotenv import load_dotenv


# ───────────────────────────────────────
# Поиск .env (гарантированный правильный)
# ───────────────────────────────────────
env_path = None
for parent in CURRENT_FILE.parents:
    candidate = parent / ".env"
    if candidate.exists() and "src" not in str(candidate.parent):
        env_path = candidate
        break

if not env_path:
    raise FileNotFoundError("❌ Не найден .env в структуре проекта")

load_dotenv(env_path)
print(f"[ENV] ✅ .env загружен из: {env_path}")


DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SERVICE_SECRET = os.getenv("DISCORD_SERVICE_SECRET")

if not DISCORD_BOT_TOKEN:
    raise ValueError("❌ В .env отсутствует DISCORD_BOT_TOKEN")

if not SERVICE_SECRET:
    raise ValueError("❌ В .env отсутствует DISCORD_SERVICE_SECRET")


# ───────────────────────────────────────
# Инициализация Discord Client
# ───────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)


# ───────────────────────────────────────
# Таблица каналов
# ───────────────────────────────────────
CHANNELS = {
    "system_status": 1441722780075950091,
    "system_logs": 1441722949571706970,
    "tasks_queue": 1441723057675702302,

    "market_analyzer": 1441723456801734717,
    "liquidity_maps": 1441723514783531069,
    "technicals_15m": 1441723776256442439,
    "technicals_1h": 1441723821966102660,
    "algo_signals": 1441723860121550943,

    "fred_liquidity": 1441724009921122336,
    "macro_events": 1441724035141472389,
    "etf_flows": 1441724069132243045,

    "agents_output": 1441724268885966878,
    "python_engineer_reports": 1441724312707928085,
    "index_watch": 1441724347763920967,
    "documentation_watcher": 1441724425836691599,

    "commands": 1441724572431810600,
    "interactions": 1441724619726917652,
}


# ───────────────────────────────────────
# Логирование ошибок
# ───────────────────────────────────────
async def log_exception(e: Exception, ctx: str):
    tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
    print(f"[ERROR] ({ctx}) {e}\n{tb}")

    try:
        await send_discord_embed(
            "system_logs",
            f"Ошибка ({ctx})",
            f"```\n{tb}\n```",
            color=0xE74C3C,
        )
    except:
        pass


# ───────────────────────────────────────
# Embed Helper
# ───────────────────────────────────────
async def send_discord_embed(channel_key: str, title: str, description: str, color: int = 0x3498DB):

    channel_id = CHANNELS.get(channel_key)
    if not channel_id:
        print(f"[Discord] ❌ Неизвестный канал: {channel_key}")
        return

    # получаем канал
    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except Exception as e:
            await log_exception(e, f"fetch_channel {channel_id}")
            return

    # Discord ограничивает описание Embed ~4000 символов
    LIMIT = 4000
    if len(description) <= LIMIT:
        embed = discord.Embed(title=title, description=description, color=color)
        await channel.send(embed=embed)
    else:
        parts = [description[i:i + LIMIT] for i in range(0, len(description), LIMIT)]
        total = len(parts)

        for idx, part in enumerate(parts, start=1):
            embed = discord.Embed(
                title=f"{title} (часть {idx}/{total})",
                description=part,
                color=color,
            )
            await channel.send(embed=embed)


# ───────────────────────────────────────
# On Ready
# ───────────────────────────────────────
@bot.event
async def on_ready():
    print(f"[Discord] ✅ Bot connected as {bot.user}")
    await send_discord_embed("system_status", "Discord Bot", "Bot started successfully.")


# ───────────────────────────────────────
# HTTP API
# ───────────────────────────────────────
async def handle_health(_):
    return web.json_response({"status": "ok"})


async def handle_send(request: web.Request):
    # проверка API токена
    auth = request.headers.get("X-API-KEY")
    if auth != SERVICE_SECRET:
        return web.json_response({"status": "unauthorized"}, status=401)

    try:
        data = await request.json()
    except:
        return web.json_response({"status": "error", "error": "invalid_json"}, status=400)

    print(f"[HTTP] Incoming → {data}")

    channel_key = data.get("channel_key")
    title = data.get("title", "")
    description = data.get("description", "")

    try:
        # log входящего сообщения
        await send_discord_embed("system_logs", "Router → Discord", f"```\n{data}\n```")

        # отправка в нужный канал
        await send_discord_embed(channel_key, title, description)

        return web.json_response({"status": "ok"})

    except Exception as e:
        await log_exception(e, "HTTP /send")
        return web.json_response({"status": "error", "error": str(e)}, status=500)


# ───────────────────────────────────────
# Основной запуск
# ───────────────────────────────────────
async def main():
    # HTTP сервер
    app = web.Application()
    app.router.add_get("/health", handle_health)
    app.router.add_post("/send", handle_send)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "127.0.0.1", 8787)
    await site.start()

    print("[Discord HTTP] 🚀 Service started on 127.0.0.1:8787")

    # запуск Discord бота
    await bot.start(DISCORD_BOT_TOKEN)


def run_discord_service():
    asyncio.run(main())


if __name__ == "__main__":
    run_discord_service()
