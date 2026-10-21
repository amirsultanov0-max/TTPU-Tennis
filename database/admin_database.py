import os
import ssl
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

load_dotenv()

MIGRATION_DATABASE_URL = os.getenv("MIGRATION_DATABASE_URL")

if not MIGRATION_DATABASE_URL:
    raise ValueError(
        "MIGRATION_DATABASE_URL is not set in .env. "
        "Add the privileged database connection before using this module."
    )

MIGRATION_DATABASE_URL = MIGRATION_DATABASE_URL.replace(
    "postgresql+asyncpg://",
    "postgresql://",
    1,
).replace(
    "postgresql://",
    "postgresql+asyncpg://",
    1,
)

CA_CERT_PATH = (
    Path(__file__).resolve().parent.parent
    / "certs"
    / "prod-ca-2021.crt"
)

ssl_context = ssl.create_default_context(cafile=str(CA_CERT_PATH))

admin_engine = create_async_engine(
    MIGRATION_DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"ssl": ssl_context},
)

AdminSessionLocal = async_sessionmaker(
    bind=admin_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
