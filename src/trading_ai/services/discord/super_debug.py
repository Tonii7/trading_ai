import os
import discord
import asyncio
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# ВЫЧИСЛЯЕМ ПУТЬ К КОРНЮ ПРОЕКТА CORRECTLY
# super_debug.py лежит глубоко:
# trading_ai/src/trading_ai/services/discord/super_debug.py
#
# Чтобы попасть в trading_ai/, нужно подняться НА 4 УРОВНЯ ВВЕРХ.
# ─────────────────────────────────────────────

CURRENT_FILE = os.path.abspath(__file__)
LEVEL_1 = os.path.dirname(CURRENT_FILE)              # .../discord
LEVEL_2 = os.path.dirname(LEVEL_1)                   # .../services
LEVEL_3 = os.path.dirname(LEVEL_2)                   # .../trading_ai
LEVEL_4 = os.path.dirname(LEVEL_3)                   # .../src
PROJECT_ROOT = os.path.dirname(LEVEL_4)             # .../trading_ai  ← нужный корень!

ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

print(f"[DEBUG] CURRENT_FILE = {CURRENT_FILE}")
print(f"[DEBUG] PROJECT_ROOT = {PROJECT_ROOT}")
print(f"[DEBUG] ENV_PATH     = {ENV_PATH}")

# ─────────────────────────────────────────────
# ПРОВЕРКА НАЛИЧИЯ .env
# ─────────────────────────────────────────────

if not os.path.exists(ENV_PATH):
    raise FileNotFoundError(
        f"❌ .env НЕ НАЙДЕН по пути:\n{ENV_PATH}\n"
        f"Ожидался здесь, т.к. это корень проекта."
    )

loaded = load_dotenv(ENV_PATH)
print(f"[DEBUG] load_dotenv returned: {loaded}")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
print(f"[DEBUG] Loaded DISCORD_BOT_TOKEN = {repr(DISCORD_BOT_TOKEN)}")

if not DISCORD_BOT_TOKEN:
    raise ValueError("❌ DISCORD_BOT_TOKEN отсутствует в .env")


# ─────────────────────────────────────────────
# Discord
# ─────────────────────────────────────────────

intents = discord.Intents.default()
client = discord.Client(intents=intents)

TARGET_CHANNEL = 1441722780075950091  # system_status


@client.event
async def on_ready():
    print(f"[READY] Logged in as {client.user}")

    ch = client.get_channel(TARGET_CHANNEL)
    if ch is None:
        try:
            ch = await client.fetch_channel(TARGET_CHANNEL)
            print(f"[OK] fetch_channel: {TARGET_CHANNEL}")
        except Exception as e:
            print(f"[FAIL] Cannot fetch channel: {e}")
            await client.close()
            return

    perms = ch.permissions_for(ch.guild.me)
    print(
        "[PERMISSIONS]",
        f"VIEW:{perms.view_channel} SEND:{perms.send_messages} "
        f"EMBED:{perms.embed_links} HISTORY:{perms.read_message_history}"
    )

    try:
        embed = discord.Embed(
            title="Super Debug",
            description="Test message OK",
            color=0x00ff00,
        )
        await ch.send(embed=embed)
        print("[OK] Message sent!")
    except Exception as e:
        print("[FAIL] Cannot send:", e)

    await client.close()


if __name__ == "__main__":
    client.run(DISCORD_BOT_TOKEN)
