import asyncio

from sqlalchemy import select

from database.database import AsyncSessionLocal
from database.models import User


async def main():
    async with AsyncSessionLocal() as session:
        result = await session.scalar(
            select(User).where(User.student_id == "U18042")
        )

        if result:
            print("User exists:")
            print("ID:", result.id)
            print("Name:", result.first_name, result.last_name)
            print("Student ID:", result.student_id)
            print("Telegram ID:", result.telegram_id)
        else:
            print("User not found.")


asyncio.run(main())
