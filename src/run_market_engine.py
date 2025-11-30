import os
import asyncio

from trading_ai.agents.market_engine import MarketEngine
from trading_ai.services.discord.bot import run_discord_bot

async def main():
    discord_task = asyncio.create_task(asyncio.to_thread(run_discord_bot))

    engine = MarketEngine()
    engine_task = asyncio.create_task(engine.start())

    await asyncio.gather(discord_task, engine_task)


if __name__ == "__main__":
    asyncio.run(main())
