import asyncio
import time

from services.users import get_user_by_telegram_id
from services.matches import get_matches_for_user


TELEGRAM_ID = 6031032702


async def main() -> None:
    print("\n=== DATABASE PERFORMANCE TEST ===\n")

    # ---------------------------------------------------------
    # USER LOOKUP
    # ---------------------------------------------------------

    start = time.perf_counter()

    user = await get_user_by_telegram_id(
        TELEGRAM_ID
    )

    user_time = time.perf_counter() - start

    print(
        f"User lookup:     {user_time:.3f} seconds"
    )

    if not user:
        print(
            "\nUser not found."
        )
        return

    print(
        f"Database user ID: {user.id}"
    )

    # ---------------------------------------------------------
    # MATCH LOOKUP
    # ---------------------------------------------------------

    start = time.perf_counter()

    matches = await get_matches_for_user(
        user.id
    )

    matches_time = time.perf_counter() - start

    print(
        f"Matches lookup:   {matches_time:.3f} seconds"
    )

    print(
        f"Matches found:    {len(matches)}"
    )

    # ---------------------------------------------------------
    # TOTAL
    # ---------------------------------------------------------

    total_time = user_time + matches_time

    print(
        f"\nTotal DB time:    "
        f"{total_time:.3f} seconds"
    )

    print("\n=== RESULT ===")

    if user_time < 0.2 and matches_time < 0.2:
        print(
            "Database queries are fast."
        )
        print(
            "The delay is probably elsewhere."
        )

    elif user_time > 1 or matches_time > 1:
        print(
            "Database access is slow."
        )
        print(
            "We should investigate PostgreSQL "
            "connection/network latency."
        )

    else:
        print(
            "Database is somewhat slow."
        )


if __name__ == "__main__":
    asyncio.run(main())