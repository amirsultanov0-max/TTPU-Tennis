import asyncio
from datetime import datetime, timedelta, timezone

from database.database import AsyncSessionLocal
from database.models import Match


async def main() -> None:
    async with AsyncSessionLocal() as session:
        match = Match(
            player_one_id=1,
            player_two_id=5,
            status="scheduled",
            scheduled_at=(
                datetime.now(timezone.utc)
                - timedelta(hours=3)
            ),
            result_reminder_sent_at=None,
        )

        session.add(match)

        await session.commit()
        await session.refresh(match)

        print("✅ Test match created.")
        print(f"   Match ID: {match.id}")
        print(f"   Player 1 ID: {match.player_one_id}")
        print(f"   Player 2 ID: {match.player_two_id}")
        print(f"   Status: {match.status}")
        print(f"   Scheduled at: {match.scheduled_at}")
        print(
            "   Reminder sent at:",
            match.result_reminder_sent_at,
        )


if __name__ == "__main__":
    asyncio.run(main())