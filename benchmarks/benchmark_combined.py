import asyncio
import time

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from database.database import AsyncSessionLocal
from database.models import Match, User


TELEGRAM_ID = 6031032702


async def main() -> None:
    print("\n=== COMBINED SESSION TEST ===\n")

    start = time.perf_counter()

    async with AsyncSessionLocal() as session:
        # 1. Find user
        result = await session.execute(
            select(User)
            .where(
                User.telegram_id == TELEGRAM_ID
            )
        )

        user = result.scalar_one_or_none()

        if not user:
            print("User not found.")
            return

        user_time = time.perf_counter() - start

        print(
            f"User lookup:     {user_time:.3f} seconds"
        )

        # 2. Find matches using the SAME session
        matches_start = time.perf_counter()

        result = await session.execute(
            select(Match)
            .options(
                selectinload(Match.player_one),
                selectinload(Match.player_two),
            )
            .where(
                or_(
                    Match.player_one_id == user.id,
                    Match.player_two_id == user.id,
                )
            )
            .order_by(
                Match.created_at.desc()
            )
        )

        matches = list(result.scalars().all())

        matches_time = time.perf_counter() - matches_start

        print(
            f"Matches lookup:   "
            f"{matches_time:.3f} seconds"
        )

        print(
            f"Matches found:    {len(matches)}"
        )

    total_time = time.perf_counter() - start

    print(
        f"\nTotal DB time:    {total_time:.3f} seconds"
    )

    print("\n=== RESULT ===")


if __name__ == "__main__":
    asyncio.run(main())