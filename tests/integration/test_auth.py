import pytest
from packages.security.rbac import has_permission

def test_admin_permissions():
    assert has_permission("admin", "inventory.close") is True
    assert has_permission("admin", "recipes.publish") is True
    
def test_manager_permissions():
    assert has_permission("manager", "inventory.close") is False
    assert has_permission("manager", "inventory.count") is True
    
def test_viewer_permissions():
    assert has_permission("viewer", "inventory.count") is False
    assert has_permission("viewer", "inventory.read") is True
    assert has_permission("viewer", "purchasing.approve") is False

from packages.security.auth import decode_jwt, TokenPayload
import jwt
import os

def test_jwt_decode():
    secret = os.environ.get("JWT_SECRET", "dummy_secret_for_development_32_bytes_long_min!")
    alg = os.environ.get("JWT_ALGORITHM", "HS256")
    
    # Create valid token
    valid_token = jwt.encode({"sub": "user-123"}, secret, algorithm=alg)
    payload = decode_jwt(valid_token)
    assert payload.sub == "user-123"
    
    # Invalid token
    with pytest.raises(ValueError):
        decode_jwt("invalid.token.here")

import uuid
from fastapi.testclient import TestClient
from sqlalchemy.future import select

from apps.api.main import app
from packages.security.models import AppUser
from packages.security.password import hash_password, verify_password

client = TestClient(app)

def test_login_success():
    response = client.post("/auth/login", json={
        "email": "admin@ksfoodops.local",
        "password": "Admin@123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@ksfoodops.local"
    assert len(data["tenants"]) > 0

def test_login_wrong_password():
    response = client.post("/auth/login", json={
        "email": "admin@ksfoodops.local",
        "password": "WrongPassword123"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

def test_login_nonexistent_email():
    response = client.post("/auth/login", json={
        "email": "nonexistent@ksfoodops.local",
        "password": "Admin@123!"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

@pytest.mark.asyncio
async def test_login_disabled_user():
    from packages.tenant.database import async_session_maker
    disabled_email = "disabled@ksfoodops.local"
    
    async with async_session_maker() as db_session:
        # Ensure disabled user exists
        result = await db_session.execute(select(AppUser).where(AppUser.email == disabled_email))
        disabled_user = result.scalar_one_or_none()
        
        if not disabled_user:
            hashed = hash_password("Admin@123!")
            disabled_user = AppUser(
                id=uuid.uuid4(),
                email=disabled_email,
                password_hash=hashed,
                full_name="Disabled User",
                is_active=False
            )
            db_session.add(disabled_user)
            await db_session.commit()

    response = client.post("/auth/login", json={
        "email": disabled_email,
        "password": "Admin@123!"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Account disabled"

def test_me_with_valid_token():
    # Login first to get token
    login_resp = client.post("/auth/login", json={
        "email": "admin@ksfoodops.local",
        "password": "Admin@123!"
    })
    token = login_resp.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "admin@ksfoodops.local"

def test_me_without_token():
    response = client.get("/auth/me")
    assert response.status_code in (401, 422)

def test_password_hashing():
    plain = "TestPass123!"
    hashed = hash_password(plain)
    assert plain != hashed
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPass", hashed) is False
