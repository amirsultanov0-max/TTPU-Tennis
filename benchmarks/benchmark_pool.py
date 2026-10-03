import asyncio
import time

from sqlalchemy import text

from database.database import AsyncSessionLocal


async def run_query(number: int) -> None:
    start = time.perf_counter()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT 1")
        )

        result.scalar()

    elapsed = time.perf_counter() - start

    print(
        f"Query {number}: {elapsed:.3f} seconds"
    )


async def main() -> None:
    print("\n=== SQLALCHEMY POOL TEST ===\n")

    for number in range(1, 6):
        await run_query(number)

    print("\n=== RESULT ===")


if __name__ == "__main__":
    asyncio.run(main())