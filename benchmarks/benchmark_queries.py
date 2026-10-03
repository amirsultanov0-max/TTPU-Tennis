import asyncio
import time

from sqlalchemy import select

from database.database import AsyncSessionLocal
from database.models import User


TELEGRAM_ID = 6031032702


async def main() -> None:
    print("\n=== USER QUERY BREAKDOWN ===\n")

    async with AsyncSessionLocal() as session:
        start = time.perf_counter()

        result = await session.execute(
            select(User).where(
                User.telegram_id == TELEGRAM_ID
            )
        )

        user = result.scalar_one_or_none()

        user_query_time = time.perf_counter() - start

        print(
            f"User query only:       "
            f"{user_query_time:.3f} seconds"
        )

        if not user:
            print("User not found.")
            return

        print(f"User ID:                {user.id}")

        start = time.perf_counter()

        result = await session.execute(
            select(User).where(
                User.id == user.id
            )
        )

        result.scalar_one_or_none()

        second_query_time = time.perf_counter() - start

        print(
            f"Second simple query:    "
            f"{second_query_time:.3f} seconds"
        )

    print("\n=== RESULT ===")


if __name__ == "__main__":
    asyncio.run(main())