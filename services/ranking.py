from sqlalchemy import func, select

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
            select(func.count())
            .select_from(User)
        )

        return result.scalar_one()


async def get_player_rank(user_id: int) -> tuple[int, int]:
    """
    Get a player's current ranking position and total number of players.

    The ranking order matches get_rankings().
    """

    ranking_order = [
        User.ranking_points.desc(),
        User.wins.desc(),
        User.first_name.asc(),
        User.last_name.asc(),
    ]

    ranked_players = (
        select(
            User.id,
            func.row_number().over(
                order_by=ranking_order
            ).label("rank"),
            func.count().over().label("total_players"),
        )
        .subquery()
    )

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(
                ranked_players.c.rank,
                ranked_players.c.total_players,
            )
            .where(ranked_players.c.id == user_id)
        )

        player_rank = result.one_or_none()

        if player_rank is None:
            total_result = await session.execute(
                select(func.count())
                .select_from(User)
            )
            return 0, int(total_result.scalar_one())

    return int(player_rank.rank), int(player_rank.total_players)
