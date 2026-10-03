import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from database.database import AsyncSessionLocal
from database.models import Match


async def main() -> None:
    """
    Find a scheduled match and move its scheduled time
    into the past so the reminder scheduler can detect it.
    """

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Match)
            .where(
                Match.status == "scheduled",
                Match.scheduled_at.is_not(None),
            )
            .order_by(Match.id.asc())
        )

        match = result.scalars().first()

        if not match:
            print("❌ No scheduled match found.")
            return

        match.scheduled_at = (
            datetime.now(timezone.utc)
            - timedelta(hours=3)
        )

        match.result_reminder_sent_at = None

        await session.commit()

        print("✅ Test match prepared.")
        print(f"   Match ID: {match.id}")
        print(f"   Scheduled at: {match.scheduled_at}")
        print("   Reminder threshold: 2 hours")
        print("   Scheduler should detect it on its next check.")


if __name__ == "__main__":
    asyncio.run(main())