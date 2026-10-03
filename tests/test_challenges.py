import asyncio

from sqlalchemy import select

from database.database import AsyncSessionLocal
from database.models import User
from services.challenges import (
    accept_challenge,
    create_challenge,
    get_pending_challenges,
)


async def main() -> None:

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(User)
            .order_by(User.id)
        )

        users = list(result.scalars().all())

    print(f"👥 Users found: {len(users)}")

    if len(users) < 2:
        print(
            "❌ Need at least 2 registered users "
            "to test challenges."
        )
        return

    player_one = users[0]
    player_two = users[1]

    print(
        f"🎾 Testing: "
        f"{player_one.first_name} vs "
        f"{player_two.first_name}"
    )

    # Create challenge.
    challenge = await create_challenge(
        challenger_id=player_one.id,
        opponent_id=player_two.id,
    )

    print(
        f"✅ Challenge created: "
        f"id={challenge.id}, "
        f"status={challenge.status}"
    )

    # Check pending challenges.
    pending = await get_pending_challenges(
        user_id=player_two.id,
    )

    print(
        f"📨 Pending challenges for "
        f"{player_two.first_name}: {len(pending)}"
    )

    # Accept challenge and create match.
    accepted_challenge, match = await accept_challenge(
        challenge_id=challenge.id,
        user_id=player_two.id,
    )

    print(
        f"✅ Challenge accepted: "
        f"id={accepted_challenge.id}, "
        f"status={accepted_challenge.status}"
    )

    print(
        f"🎾 Match created: "
        f"id={match.id}, "
        f"status={match.status}"
    )


if __name__ == "__main__":
    asyncio.run(main())