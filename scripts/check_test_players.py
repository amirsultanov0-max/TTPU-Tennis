import asyncio

from sqlalchemy import select

from database.database import AsyncSessionLocal
from database.models import User


async def main() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User)
            .where(User.id.in_([1, 5]))
            .order_by(User.id.asc())
        )

        users = result.scalars().all()

        if not users:
            print("❌ No test players found.")
            return

        print(f"👥 Test players found: {len(users)}")

        for user in users:
            print()
            print(f"User ID: {user.id}")
            print(f"Name: {user.first_name} {user.last_name}")
            print(f"Telegram ID: {user.telegram_id}")
            print(f"Student ID: {user.student_id}")


if __name__ == "__main__":
    asyncio.run(main())