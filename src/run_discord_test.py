import asyncio
from src.trading_ai.services.discord.bot import bot, DISCORD_BOT_TOKEN
from src.trading_ai.services.discord.router import dispatch

async def main():
    asyncio.create_task(bot.start(DISCORD_BOT_TOKEN))

    await asyncio.sleep(3)

    dispatch("liquidity_maps", "Тестовое сообщение", "Liquidity Test")

    await asyncio.sleep(3)

asyncio.run(main())
