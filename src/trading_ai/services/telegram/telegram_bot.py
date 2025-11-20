import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from trading_ai.core.crew import TradingAi

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

crew = TradingAi()

logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands=['start'])
async def welcome(message: types.Message):
    await message.answer("🤖 Привет, Eldar! Trading AI готов к работе.\n\n"
                         "Доступные команды:\n"
                         "/market — рыночный анализ\n"
                         "/macro — макро\n"
                         "/signals — торговые сигналы\n"
                         "/report — полный дневной отчёт\n"
                         "/run — прогнать весь CrewAI")


@dp.message_handler(commands=['market'])
async def market(message: types.Message):
    result = crew.agents["market_analyzer"].run()
    await message.answer(f"📊 *Рыночный анализ:*\n\n{result}", parse_mode="Markdown")


@dp.message_handler(commands=['macro'])
async def macro(message: types.Message):
    result = crew.agents["macro_intelligence_analyst"].run()
    await message.answer(f"🧠 *Макро-анализ:*\n\n{result}", parse_mode="Markdown")


@dp.message_handler(commands=['signals'])
async def signals(message: types.Message):
    result = crew.agents["signal_generator"].run()
    await message.answer(f"🎯 *Торговые сигналы:*\n\n{result}", parse_mode="Markdown")


@dp.message_handler(commands=['report'])
async def report(message: types.Message):
    final = crew.run()
    await message.answer(f"📘 *Full Report:*\n\n{final}", parse_mode="Markdown")


@dp.message_handler(commands=['run'])
async def run_all(message: types.Message):
    final = crew.run()
    await message.answer(f"🚀 *CrewAI Completed:*\n\n{final}", parse_mode="Markdown")


def start_bot():
    executor.start_polling(dp, skip_updates=True)
