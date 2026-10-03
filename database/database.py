import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set in .env"
    )


DATABASE_URL = DATABASE_URL.replace(
    "postgresql://",
    "postgresql+asyncpg://",
    1,
)


engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=False,
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def warm_up_database() -> None:
    """
    Establish and warm a database connection.

    This is called once when the bot starts so that the first
    user interaction does not have to pay the initial database
    connection/setup latency.
    """

    async with engine.connect() as connection:
        await connection.execute(
            text("SELECT 1")
        )