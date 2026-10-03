import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from database.database import AsyncSessionLocal
from database.models import Match
from services.matches import (
    accept_schedule_request,
    create_schedule_request,
    get_pending_schedule_requests,
)


async def main() -> None:

    # =========================
    # FIND UNSCHEDULED MATCH
    # =========================

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(Match)
            .where(
                Match.status == "awaiting_schedule"
            )
            .order_by(
                Match.id
            )
        )

        match = result.scalars().first()

    if not match:
        print(
            "❌ No match is currently waiting "
            "for a schedule."
        )
        return

    print(
        f"🎾 Match found: "
        f"id={match.id}"
    )

    print(
        f"   Player 1 ID: "
        f"{match.player_one_id}"
    )

    print(
        f"   Player 2 ID: "
        f"{match.player_two_id}"
    )

    print(
        f"   Status: "
        f"{match.status}"
    )

    # =========================
    # PROPOSE DATE/TIME
    # =========================

    proposed_at = datetime(
        2026,
        10,
        5,
        18,
        0,
        tzinfo=timezone.utc,
    )

    schedule_request = await create_schedule_request(
        match_id=match.id,
        requested_by_id=match.player_one_id,
        proposed_at=proposed_at,
    )

    print(
        f"📅 Schedule request created: "
        f"id={schedule_request.id}"
    )

    print(
        f"   Proposed time: "
        f"{schedule_request.proposed_at}"
    )

    print(
        f"   Status: "
        f"{schedule_request.status}"
    )

    # =========================
    # CHECK PENDING REQUEST
    # =========================

    pending_requests = await get_pending_schedule_requests(
        user_id=match.player_two_id,
    )

    print(
        f"📨 Pending requests for player "
        f"{match.player_two_id}: "
        f"{len(pending_requests)}"
    )

    # =========================
    # ACCEPT REQUEST
    # =========================

    accepted_request = await accept_schedule_request(
        request_id=schedule_request.id,
        user_id=match.player_two_id,
    )

    print(
        f"✅ Schedule request accepted: "
        f"id={accepted_request.id}"
    )

    # =========================
    # VERIFY MATCH
    # =========================

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(Match)
            .where(
                Match.id == match.id
            )
        )

        updated_match = result.scalar_one()

    print(
        f"🎾 Match status: "
        f"{updated_match.status}"
    )

    print(
        f"📅 Match scheduled at: "
        f"{updated_match.scheduled_at}"
    )

    # =========================
    # FINAL CHECK
    # =========================

    if (
        updated_match.status == "scheduled"
        and updated_match.scheduled_at == proposed_at
    ):
        print()
        print("✅ SCHEDULING TEST PASSED")
    else:
        print()
        print("❌ SCHEDULING TEST FAILED")


if __name__ == "__main__":
    asyncio.run(main())