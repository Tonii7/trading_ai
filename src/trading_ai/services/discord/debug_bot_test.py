import asyncio
from trading_ai.services.discord.bot import send_discord_embed

async def main():
    print("[TEST] Running debug_bot_test...")
    try:
        await send_discord_embed(
            "system_status",
            "BOT TEST",
            "Debug test executed successfully."
        )
        print("[TEST] Message sent!")
    except Exception as e:
        print("[TEST ERROR]", e)

if __name__ == "__main__":
    asyncio.run(main())
