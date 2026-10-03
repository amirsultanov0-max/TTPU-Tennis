import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env")

DATABASE_URL = DATABASE_URL.replace(
    "postgresql://",
    "postgresql+asyncpg://",
    1,
)


async def test_connection() -> None:
    engine = create_async_engine(DATABASE_URL)

    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            print("✅ Database connection successful:", result.scalar())

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_connection())
