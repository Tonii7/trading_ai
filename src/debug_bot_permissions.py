import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio

# Load .env manually
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN not found in .env")

intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)


@bot.event
async def on_ready():
    print(f"\n[READY] Logged in as {bot.user}\n")
    await run_permission_check()
    await bot.close()


async def run_permission_check():
    print("[CHECK] Listing all channels and bot permissions...\n")

    for guild in bot.guilds:
        print(f"=== SERVER: {guild.name} ===\n")

        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):

                perms = channel.permissions_for(guild.me)

                print(
                    f"{channel.name:<25} → "
                    f"VIEW:{perms.view_channel}  "
                    f"SEND:{perms.send_messages}  "
                    f"EMBED:{perms.embed_links}  "
                    f"HISTORY:{perms.read_message_history}"
                )


async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
