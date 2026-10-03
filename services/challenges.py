from sqlalchemy import or_, select

from database.database import AsyncSessionLocal
from database.models import Challenge, Match, User


ACTIVE_MATCH_STATUSES = (
    "awaiting_schedule",
    "scheduled",
)


async def create_challenge(
    challenger_id: int,
    opponent_id: int,
) -> Challenge:
    """
    Create a new challenge between two players.
    """

    if challenger_id == opponent_id:
        raise ValueError(
            "You cannot challenge yourself."
        )

    async with AsyncSessionLocal() as session:

        challenger = await session.get(
            User,
            challenger_id,
        )

        opponent = await session.get(
            User,
            opponent_id,
        )

        if not challenger:
            raise ValueError(
                "Challenger not found."
            )

        if not opponent:
            raise ValueError(
                "Opponent not found."
            )

        # Check for an existing pending challenge
        # in either direction.
        result = await session.execute(
            select(Challenge)
            .where(
                (
                    (Challenge.challenger_id == challenger_id)
                    & (Challenge.opponent_id == opponent_id)
                )
                |
                (
                    (Challenge.challenger_id == opponent_id)
                    & (Challenge.opponent_id == challenger_id)
                )
            )
            .where(
                Challenge.status == "pending"
            )
        )

        existing_challenge = result.scalar_one_or_none()

        if existing_challenge:
            raise ValueError(
                "There is already a pending challenge "
                "between these players."
            )

        # Prevent a new challenge when the players
        # already have an active match.
        result = await session.execute(
            select(Match)
            .where(
                Match.status.in_(ACTIVE_MATCH_STATUSES),
                or_(
                    (
                        (Match.player_one_id == challenger_id)
                        & (Match.player_two_id == opponent_id)
                    ),
                    (
                        (Match.player_one_id == opponent_id)
                        & (Match.player_two_id == challenger_id)
                    ),
                ),
            )
        )

        existing_match = result.scalar_one_or_none()

        if existing_match:
            raise ValueError(
                "These players already have an active match."
            )

        challenge = Challenge(
            challenger_id=challenger_id,
            opponent_id=opponent_id,
            status="pending",
        )

        session.add(challenge)

        await session.commit()

        await session.refresh(challenge)

        return challenge


async def get_pending_challenges(
    user_id: int,
) -> list[Challenge]:
    """
    Get all pending challenges received by a player.
    """

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(Challenge)
            .where(
                Challenge.opponent_id == user_id,
                Challenge.status == "pending",
            )
            .order_by(
                Challenge.created_at.desc()
            )
        )

        return list(result.scalars().all())


async def accept_challenge(
    challenge_id: int,
    user_id: int,
) -> tuple[Challenge, Match]:
    """
    Accept a challenge and create the corresponding match.

    Both operations happen inside the same database transaction.
    """

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(Challenge)
            .where(
                Challenge.id == challenge_id,
                Challenge.opponent_id == user_id,
                Challenge.status == "pending",
            )
        )

        challenge = result.scalar_one_or_none()

        if not challenge:
            raise ValueError(
                "Challenge not found or no longer pending."
            )

        # Make sure the players do not already have
        # an active match.
        result = await session.execute(
            select(Match)
            .where(
                Match.status.in_(ACTIVE_MATCH_STATUSES),
                or_(
                    (
                        (Match.player_one_id == challenge.challenger_id)
                        & (
                            Match.player_two_id
                            == challenge.opponent_id
                        )
                    ),
                    (
                        (Match.player_one_id == challenge.opponent_id)
                        & (
                            Match.player_two_id
                            == challenge.challenger_id
                        )
                    ),
                ),
            )
        )

        existing_match = result.scalar_one_or_none()

        if existing_match:
            raise ValueError(
                "These players already have an active match."
            )

        # Create the match before committing.
        match = Match(
            player_one_id=challenge.challenger_id,
            player_two_id=challenge.opponent_id,
            status="awaiting_schedule",
        )

        session.add(match)

        # Mark the challenge as accepted.
        challenge.status = "accepted"

        # Both changes are committed together.
        await session.commit()

        await session.refresh(challenge)
        await session.refresh(match)

        return challenge, match


async def reject_challenge(
    challenge_id: int,
    user_id: int,
) -> Challenge:
    """
    Reject a challenge.

    Only the challenged opponent can reject it.
    """

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(Challenge)
            .where(
                Challenge.id == challenge_id,
                Challenge.opponent_id == user_id,
                Challenge.status == "pending",
            )
        )

        challenge = result.scalar_one_or_none()

        if not challenge:
            raise ValueError(
                "Challenge not found or no longer pending."
            )

        challenge.status = "rejected"

        await session.commit()

        await session.refresh(challenge)

        return challenge