import argparse
import asyncio

from sqlalchemy import select

from database.admin_database import AdminSessionLocal, admin_engine
from database.models import User
from services.elo import rebuild_all_ratings


async def main(apply_changes: bool) -> None:
    async with AdminSessionLocal() as session:
        try:
            users_result = await session.execute(select(User))
            user_count = len(users_result.scalars().all())

            included_matches = await rebuild_all_ratings(session)

            if apply_changes:
                await session.commit()
                print("Elo rebuild committed successfully.")
            else:
                await session.rollback()
                print("Dry run only. No rating changes were committed.")

            print(f"Players processed: {user_count}")
            print(f"Confirmed matches included: {included_matches}")

            if not apply_changes:
                print(
                    "If these counts look reasonable, run again with --apply "
                    "to save the rebuilt ratings."
                )
        except Exception:
            await session.rollback()
            raise


async def run_and_dispose() -> None:
    parser = argparse.ArgumentParser(
        description="Rebuild player Elo ratings from confirmed match history."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Commit the recalculated Elo ratings to the database.",
    )
    args = parser.parse_args()

    try:
        await main(args.apply)
    finally:
        await admin_engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_and_dispose())
