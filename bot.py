import asyncio
import os

from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from bot.handlers.matches import router as matches_router
from bot.handlers.menu import router as menu_router
from bot.handlers.rankings import router as rankings_router
from bot.handlers.registration import router as registration_router
from bot.handlers.scheduling import router as scheduling_router
from bot.handlers.start import router as start_router
from bot.tasks.result_reminders import send_result_reminders
from database.database import warm_up_database


load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN is not set in .env"
    )


dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(registration_router)
dp.include_router(menu_router)
dp.include_router(rankings_router)
dp.include_router(matches_router)
dp.include_router(scheduling_router)


async def main() -> None:
    """
    Start the TTPU Tennis bot.
    """

    bot = Bot(token=BOT_TOKEN)

    scheduler = AsyncIOScheduler()

    print("🎾 Starting TTPU Tennis bot...")

    print("🔌 Warming up database connection...")

    try:
        await warm_up_database()
    except Exception as error:
        print(
            "❌ Database connection failed during startup."
        )
        print(f"   Error: {error}")

        await bot.session.close()
        raise

    print("✅ Database connection ready.")

    scheduler.add_job(
        send_result_reminders,
        "interval",
        minutes=5,
        args=[bot],
        id="result_reminders",
        replace_existing=True,
    )

    scheduler.start()

    print("⏰ Result reminder scheduler started.")
    print("   Checking every 5 minutes.")

    print("🎾 TTPU Tennis bot is running...")

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())