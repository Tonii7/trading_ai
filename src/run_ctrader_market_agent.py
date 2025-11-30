import asyncio

from src.trading_ai.agents.ctrader_market_agent import CTraderMarketAgent
from src.trading_ai.services.discord.bot import bot, DISCORD_BOT_TOKEN

async def start_discord_bot():
    """Запуск Discord бота в отдельной задаче."""
    await bot.start(DISCORD_BOT_TOKEN)

async def main():
    # 1. Запускаем Discord-бота как фоновую задачу
    bot_task = asyncio.create_task(start_discord_bot())

    # 2. Ждём, пока бот полностью загрузится
    while not bot.is_ready():
        await asyncio.sleep(0.5)

    print("[Runner] Discord bot is fully READY.")

    # 3. Ждём ещё немного для полной прогрузки кеша
    await asyncio.sleep(2)

    # 4. Запускаем агента
    agent = CTraderMarketAgent()
    await agent.run_once()

    # 5. Даем Discord время отправить сообщения
    await asyncio.sleep(3)

    # Опционально можно завершать бота:
    # await bot.close()
    # bot_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
