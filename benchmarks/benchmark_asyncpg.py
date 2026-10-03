import asyncio
import os
import time

import asyncpg

from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


async def main() -> None:
    print("\n=== RAW ASYNCPG CONNECTION REUSE TEST ===\n")

    if not DATABASE_URL:
        print("DATABASE_URL is not set.")
        return

    start = time.perf_counter()

    connection = await asyncpg.connect(
        DATABASE_URL
    )

    connection_time = time.perf_counter() - start

    print(
        f"Connection time: {connection_time:.3f} seconds"
    )

    for number in range(1, 4):
        start = time.perf_counter()

        result = await connection.fetchval(
            "SELECT 1"
        )

        query_time = time.perf_counter() - start

        print(
            f"Query {number}:      "
            f"{query_time:.3f} seconds "
            f"(result={result})"
        )

    await connection.close()

    print("\n=== RESULT ===")


if __name__ == "__main__":
    asyncio.run(main())