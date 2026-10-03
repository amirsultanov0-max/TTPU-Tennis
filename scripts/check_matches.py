import asyncio

from sqlalchemy import select

from database.database import AsyncSessionLocal
from database.models import Match


async def main() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Match).order_by(Match.id.asc())
        )

        matches = result.scalars().all()

        if not matches:
            print("❌ No matches found.")
            return

        print(f"🎾 Matches found: {len(matches)}")

        for match in matches:
            print()
            print(f"Match ID: {match.id}")
            print(f"Status: {match.status}")
            print(f"Player 1 ID: {match.player_one_id}")
            print(f"Player 2 ID: {match.player_two_id}")
            print(f"Scheduled at: {match.scheduled_at}")
            print(
                "Reminder sent at:",
                match.result_reminder_sent_at,
            )


if __name__ == "__main__":
    asyncio.run(main())