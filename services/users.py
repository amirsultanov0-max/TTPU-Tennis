from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.database import AsyncSessionLocal
from database.models import User, Group


async def get_or_create_group(
    session,
    group_name: str,
) -> Group:
    """
    Find an existing group or create a new one.
    """

    result = await session.execute(
        select(Group).where(
            Group.name == group_name
        )
    )

    group = result.scalar_one_or_none()

    if group:
        return group

    group = Group(
        name=group_name,
        is_active=True,
    )

    session.add(group)

    await session.flush()

    return group


async def get_user_by_telegram_id(
    telegram_id: int,
) -> User | None:
    """
    Get a user profile by Telegram ID.
    """

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(User)
            .options(
                selectinload(User.group)
            )
            .where(
                User.telegram_id == telegram_id
            )
        )

        return result.scalar_one_or_none()


async def get_user_by_student_id(
    student_id: str,
) -> User | None:
    """
    Get a user profile by university student ID.
    """

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(User)
            .options(
                selectinload(User.group)
            )
            .where(
                User.student_id == student_id
            )
        )

        return result.scalar_one_or_none()


async def create_user(
    telegram_id: int,
    telegram_username: str | None,
    first_name: str,
    last_name: str,
    group_name: str,
    student_id: str,
    phone: str | None,
) -> User:
    """
    Create a new tennis player profile.

    Telegram ID and Student ID must both be unique.
    """

    async with AsyncSessionLocal() as session:

        try:

            # ==================================================
            # CHECK TELEGRAM ID
            # ==================================================

            result = await session.execute(
                select(User).where(
                    User.telegram_id == telegram_id
                )
            )

            existing_user = result.scalar_one_or_none()

            if existing_user:
                raise ValueError(
                    "This Telegram account is already registered."
                )

            # ==================================================
            # CHECK STUDENT ID
            # ==================================================

            result = await session.execute(
                select(User).where(
                    User.student_id == student_id
                )
            )

            existing_student = result.scalar_one_or_none()

            if existing_student:
                raise ValueError(
                    "This student ID is already registered.\n\n"
                    "Please check your student ID and try again."
                )

            # ==================================================
            # GET OR CREATE GROUP
            # ==================================================

            group = await get_or_create_group(
                session,
                group_name,
            )

            # ==================================================
            # CREATE PLAYER
            # ==================================================

            new_user = User(
                telegram_id=telegram_id,
                telegram_username=telegram_username,
                first_name=first_name,
                last_name=last_name,
                group_id=group.id,
                student_id=student_id,
                phone=phone,
                ranking_points=0,
                wins=0,
                losses=0,
            )

            session.add(new_user)

            await session.commit()

            # ==================================================
            # LOAD USER WITH GROUP
            # ==================================================

            result = await session.execute(
                select(User)
                .options(
                    selectinload(User.group)
                )
                .where(
                    User.id == new_user.id
                )
            )

            return result.scalar_one()

        except Exception:
            await session.rollback()
            raise