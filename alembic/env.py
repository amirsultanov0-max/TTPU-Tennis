import asyncio
import os
import ssl
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from database.models import Base


load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

CA_CERT_PATH = (
    Path(__file__).resolve().parent.parent
    / "certs"
    / "prod-ca-2021.crt"
)


def get_database_url() -> str:
    """Get the privileged database URL reserved for migrations."""
    database_url = os.getenv("MIGRATION_DATABASE_URL")

    if not database_url:
        raise ValueError(
            "MIGRATION_DATABASE_URL is not set in .env. "
            "Migrations must use the privileged database connection."
        )

    return database_url.replace(
        "postgresql+asyncpg://",
        "postgresql://",
        1,
    ).replace(
        "postgresql://",
        "postgresql+asyncpg://",
        1,
    )


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Run migrations using an active database connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations using the privileged connection and verified TLS."""
    configuration = config.get_section(
        config.config_ini_section,
        {},
    )

    configuration["sqlalchemy.url"] = get_database_url()

    ssl_context = ssl.create_default_context(cafile=str(CA_CERT_PATH))

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"ssl": ssl_context},
    )

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
