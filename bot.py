import asyncio
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from bot.handlers.registration import router as registration_router
from bot.handlers.start import router as start_router


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env")


dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(registration_router)


async def main() -> None:
    """Start the Telegram bot."""

    bot = Bot(token=BOT_TOKEN)

    print("🎾 TTPU Tennis bot is running...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
