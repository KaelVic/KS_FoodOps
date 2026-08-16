import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

import sys
from sqlalchemy.pool import NullPool

# Fallback to sqlite if no DB url provided for easy initial local testing, 
# although we MUST use postgres for RLS
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql+asyncpg://ksfoodops_app:app_password@localhost:5433/ks_foodops"
)

# Owner URL used for migrations
OWNER_DATABASE_URL = os.environ.get(
    "OWNER_DATABASE_URL",
    "postgresql+asyncpg://ks_owner:ks_password@localhost:5433/ks_foodops"
)

if "pytest" in sys.modules or os.environ.get("PYTEST_CURRENT_TEST"):
    engine = create_async_engine(DATABASE_URL, echo=False, poolclass=NullPool)
else:
    engine = create_async_engine(
        DATABASE_URL, 
        echo=False,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=10,
        max_overflow=20
    )

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to provide a database session.
    RLS tenant injection is handled by the higher-level auth dependency.
    """
    async with async_session_maker() as session:
        yield session
