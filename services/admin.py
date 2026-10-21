from sqlalchemy import func, select

from database.database import AsyncSessionLocal
from database.models import AdminRole, Match, User


async def get_admin_overview(telegram_id: int) -> dict | None:
    """
    Return dashboard statistics for an active admin.
    Return None if the Telegram account has no active admin role.
    """

    async with AsyncSessionLocal() as session:
        admin_result = await session.execute(
            select(AdminRole).where(
                AdminRole.telegram_id == telegram_id,
                AdminRole.is_active.is_(True),
            )
        )
        admin = admin_result.scalar_one_or_none()

        if admin is None:
            return None

        async def count_rows(model, *conditions) -> int:
            result = await session.execute(
                select(func.count()).select_from(model).where(*conditions)
            )
            return int(result.scalar_one())

        return {
            "role": admin.role,
            "players": await count_rows(User),
            "matches": await count_rows(Match),
            "awaiting_schedule": await count_rows(
                Match, Match.status == "awaiting_schedule"
            ),
            "scheduled": await count_rows(
                Match, Match.status == "scheduled"
            ),
            "completed": await count_rows(
                Match, Match.status == "completed"
            ),
            "pending_results": await count_rows(
                Match, Match.result_status == "pending_confirmation"
            ),
        }


async def get_admin_players(
    telegram_id: int,
    page: int = 0,
    page_size: int = 5,
) -> dict | None:
    """Return one page of players for an active admin."""

    from database.models import Group

    page = max(0, page)
    page_size = max(1, page_size)

    async with AsyncSessionLocal() as session:
        admin_result = await session.execute(
            select(AdminRole.id).where(
                AdminRole.telegram_id == telegram_id,
                AdminRole.is_active.is_(True),
            )
        )
        if admin_result.scalar_one_or_none() is None:
            return None

        total_result = await session.execute(
            select(func.count()).select_from(User)
        )
        total = int(total_result.scalar_one())

        players_result = await session.execute(
            select(User)
            .order_by(User.first_name.asc(), User.last_name.asc(), User.id.asc())
            .offset(page * page_size)
            .limit(page_size)
        )

        return {
            "players": list(players_result.scalars().all()),
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": max(1, (total + page_size - 1) // page_size),
        }


async def get_admin_player(
    telegram_id: int,
    player_id: int,
) -> dict | None:
    """Return a player's profile only to an active admin."""

    from database.models import Group

    async with AsyncSessionLocal() as session:
        admin_result = await session.execute(
            select(AdminRole.id).where(
                AdminRole.telegram_id == telegram_id,
                AdminRole.is_active.is_(True),
            )
        )
        if admin_result.scalar_one_or_none() is None:
            return None

        result = await session.execute(
            select(User, Group)
            .join(Group, User.group_id == Group.id)
            .where(User.id == player_id)
        )
        row = result.one_or_none()

        if row is None:
            return {"not_found": True}

        player, group = row
        return {
            "player": player,
            "group": group,
        }


async def is_active_admin(telegram_id: int) -> bool:
    """Check whether a Telegram account has an active admin role."""

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AdminRole.id).where(
                AdminRole.telegram_id == telegram_id,
                AdminRole.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none() is not None
