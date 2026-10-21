import asyncio
import os
import time
from pathlib import Path

import asyncpg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from .env")

DIRECT_DATABASE_URL = DATABASE_URL.replace(
    "postgresql+asyncpg://",
    "postgresql://",
    1,
)


async def main() -> None:
    print("\n=== SUPABASE DATABASE CONNECTION TEST ===\n")

    connection = None

    try:
        start = time.perf_counter()

        connection = await asyncpg.connect(DIRECT_DATABASE_URL)

        connection_time = time.perf_counter() - start
        print(f"Connection time: {connection_time:.3f} seconds")

        start = time.perf_counter()
        result = await connection.fetchval("SELECT 1")
        query_time = time.perf_counter() - start

        print(f"SELECT 1:        {query_time:.3f} seconds")
        print(f"Result:           {result}")

        print("\n=== RESULT ===")

        if query_time < 0.2:
            print("Database query is fast.")
        elif query_time < 1:
            print("Database query has some latency.")
        else:
            print("Database query is slow.")

    finally:
        if connection is not None:
            await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
