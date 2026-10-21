import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import func, select

from database.admin_database import AdminSessionLocal, admin_engine
from database.models import AdminRole


async def main() -> None:
    load_dotenv()

    telegram_id_raw = os.getenv("SUPERADMIN_TELEGRAM_ID", "").strip()

    if not telegram_id_raw:
        raise SystemExit(
            "SUPERADMIN_TELEGRAM_ID is missing from .env. "
            "Add your own Telegram numeric ID before running this script."
        )

    try:
        telegram_id = int(telegram_id_raw)
        if telegram_id <= 0:
            raise ValueError
    except ValueError:
        raise SystemExit("SUPERADMIN_TELEGRAM_ID must be a positive integer.")

    async with AdminSessionLocal() as session:
        async with session.begin():
            # Serialize bootstrap attempts so two simultaneous runs cannot
            # both observe an empty table and create different first admins.
            await session.execute(
                select(func.pg_advisory_xact_lock(73762912))
            )

            existing_count = await session.scalar(
                select(func.count()).select_from(AdminRole)
            )

            if existing_count:
                print(
                    "Bootstrap refused: admin records already exist. "
                    "No records were changed."
                )
                return

            session.add(
                AdminRole(
                    telegram_id=telegram_id,
                    role="superadmin",
                    is_active=True,
                    granted_by_telegram_id=None,
                )
            )

    print(f"Initial superadmin created for Telegram ID {telegram_id}.")


async def run_and_dispose() -> None:
    try:
        await main()
    finally:
        await admin_engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_and_dispose())
