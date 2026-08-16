import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
import sys
import os
import asyncio
import uuid

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from packages.tenant.database import OWNER_DATABASE_URL, DATABASE_URL, async_session_maker

from sqlalchemy.pool import NullPool

# Use main database for tests (tests run against main dev DB)
test_owner_engine = create_async_engine(OWNER_DATABASE_URL, echo=False, poolclass=NullPool)
test_app_engine = create_async_engine(DATABASE_URL, echo=False, poolclass=NullPool)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=test_app_engine, class_=AsyncSession
)

OwnerSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=test_owner_engine, class_=AsyncSession
)

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
def tenant_id():
    """Return a fixed test tenant UUID (string form)."""
    return "00000000-0000-0000-0000-000000000001"


@pytest_asyncio.fixture
async def owner_session(tenant_id):
    """
    Owner session for test setup (bypasses RLS).

    Ensures the dummy tenant and test user membership exist before any test
    that uses the owner_session fixture, so foreign-key constraints on
    tenant_id are satisfied and the API's membership check passes.
    """
    async with OwnerSessionLocal() as session:
        # Upsert tenant
        await session.execute(
            text("""
                INSERT INTO tenants (id, name)
                VALUES (:id, 'Test Tenant')
                ON CONFLICT (id) DO NOTHING
            """),
            {"id": tenant_id}
        )
        # Upsert membership so get_secure_session passes (no unique constraint
        # exists on (tenant_id, user_id), so we guard with a SELECT first)
        existing = await session.execute(
            text("""
                SELECT id FROM tenant_memberships
                WHERE tenant_id = :tenant_id AND user_id = 'test-user-123'
                LIMIT 1
            """),
            {"tenant_id": tenant_id}
        )
        if existing.fetchone() is None:
            await session.execute(
                text("""
                    INSERT INTO tenant_memberships (id, tenant_id, user_id, role)
                    VALUES (:id, :tenant_id, 'test-user-123', 'admin')
                """),
                {"id": str(uuid.uuid4()), "tenant_id": tenant_id}
            )
        await session.commit()
        yield session


@pytest_asyncio.fixture
async def async_client(tenant_id):
    """Async HTTPX client wired directly to the ASGI app (no mock overrides)."""
    from httpx import AsyncClient, ASGITransport
    from apps.api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client


@pytest.fixture
def auth_headers(tenant_id):
    """JWT auth headers for the test user in the test tenant."""
    import jwt
    from datetime import datetime, timedelta, timezone

    JWT_SECRET = os.environ.get("JWT_SECRET", "dummy_secret_for_development_32_bytes_long_min!")
    JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

    payload = {
        "sub": "test-user-123",
        "email": "test@ksfoodops.local",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": tenant_id
    }


@pytest_asyncio.fixture
async def db_session():
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def test_db():
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def admin_user(test_db, tenant_id):
    # Mocking admin_user to return None as it's not strictly used in tests directly
    return None
