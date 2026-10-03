import asyncio
import time

import asyncpg


# Paste your Supabase DIRECT connection URI between the quotes.
DIRECT_DATABASE_URL = "postgresql://postgres:TTPUTennis2026ByAmirbek@db.sxigrtlojmvimxtwkcvj.supabase.co:5432/postgres"

async def main() -> None:
    print("\n=== SUPABASE DIRECT CONNECTION TEST ===\n")

    start = time.perf_counter()

    connection = await asyncpg.connect(
        DIRECT_DATABASE_URL
    )

    connection_time = time.perf_counter() - start

    print(
        f"Connection time: {connection_time:.3f} seconds"
    )

    start = time.perf_counter()

    result = await connection.fetchval(
        "SELECT 1"
    )

    query_time = time.perf_counter() - start

    print(
        f"SELECT 1:        {query_time:.3f} seconds"
    )

    print(
        f"Result:           {result}"
    )

    await connection.close()

    print("\n=== RESULT ===")

    if query_time < 0.2:
        print(
            "Direct connection is fast."
        )
    elif query_time < 1:
        print(
            "Direct connection has some latency."
        )
    else:
        print(
            "Direct connection is still slow."
        )


if __name__ == "__main__":
    asyncio.run(main())