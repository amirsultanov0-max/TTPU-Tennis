from sqlalchemy import select

from database.database import AsyncSessionLocal
from database.models import User


async def get_rankings(
    limit: int = 10,
) -> list[User]:
    """
    Get the current tennis rankings.

    Players are ordered by:
    1. Ranking points, highest first.
    2. Wins, highest first.
    3. Name, alphabetically.
    """

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(User)
            .order_by(
                User.ranking_points.desc(),
                User.wins.desc(),
                User.first_name.asc(),
                User.last_name.asc(),
            )
            .limit(limit)
        )

        return list(result.scalars().all())


async def get_total_players() -> int:
    """
    Get the total number of registered tennis players.
    """

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(User.id)
        )

        return len(result.scalars().all())


async def get_player_rank(user_id: int) -> tuple[int, int]:
    """
    Get a player's current ranking position and total number of players.

    The ranking order matches get_rankings().
    """

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(User)
            .order_by(
                User.ranking_points.desc(),
                User.wins.desc(),
                User.first_name.asc(),
                User.last_name.asc(),
            )
        )

        players = list(result.scalars().all())

    for position, player in enumerate(players, start=1):
        if player.id == user_id:
            return position, len(players)

    return 0, len(players)
