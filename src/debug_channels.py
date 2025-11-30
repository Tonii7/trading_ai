import asyncio
from src.trading_ai.services.discord.bot import bot, DISCORD_BOT_TOKEN

@bot.event
async def on_ready():
    print(f"[DEBUG] Connected as: {bot.user}")
    print("[DEBUG] Listing available channels:")

    for guild in bot.guilds:
        print(f"\nGuild: {guild.name} (ID: {guild.id})")
        for channel in guild.channels:
            print(f" - {channel.name} (ID: {channel.id})")

    await bot.close()

bot.run(DISCORD_BOT_TOKEN)
