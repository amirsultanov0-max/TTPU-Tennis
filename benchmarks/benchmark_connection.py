import asyncio
import time

from sqlalchemy import text

from database.database import AsyncSessionLocal


async def main() -> None:
    print("\n=== DATABASE CONNECTION TEST ===\n")

    start = time.perf_counter()

    async with AsyncSessionLocal() as session:
        connection_time = time.perf_counter() - start

        print(
            f"Session creation: {connection_time:.3f} seconds"
        )

        start = time.perf_counter()

        result = await session.execute(
            text("SELECT 1")
        )

        query_time = time.perf_counter() - start

        print(
            f"SELECT 1:         {query_time:.3f} seconds"
        )

        print(
            f"Result:            {result.scalar()}"
        )

    total_time = connection_time + query_time

    print(
        f"\nTotal:             {total_time:.3f} seconds"
    )

    print("\n=== RESULT ===")

    if total_time < 0.2:
        print(
            "Database connection is fast."
        )

    elif total_time < 1:
        print(
            "Database connection has noticeable latency."
        )

    else:
        print(
            "Database connection is very slow."
        )


if __name__ == "__main__":
    asyncio.run(main())