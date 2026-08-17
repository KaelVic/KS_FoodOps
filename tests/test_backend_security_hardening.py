import pytest
import pyotp
import uuid
import defusedxml.ElementTree as ET
from fastapi.testclient import TestClient
from apps.api.main import app
from packages.security.ssrf import is_safe_url
from packages.security.models import AppUser
from packages.security.password import hash_password
from sqlalchemy.future import select

client = TestClient(app)

def test_cors_configuration():
    """Validates that CORS rejects unauthorized origins and returns allowed origins correctly."""
    # Test allowed origin
    res = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"

    # Test unauthorized origin
    res_unauth = client.options(
        "/health",
        headers={
            "Origin": "https://malicious-attacker-domain.evil.com",
            "Access-Control-Request-Method": "GET"
        }
    )
    # Origin is not in the allowed list, so access-control-allow-origin should NOT match the evil origin
    assert res_unauth.headers.get("access-control-allow-origin") != "https://malicious-attacker-domain.evil.com"


def test_defusedxml_xxe_protection():
    """Validates that defusedxml blocks XML External Entity (XXE) and entity expansion attacks."""
    # Malicious XXE Payload attempting to resolve an external/local entity
    malicious_xxe_xml = """<?xml version="1.0" encoding="ISO-8859-1"?>
    <!DOCTYPE foo [  
      <!ELEMENT foo ANY >
      <!ENTITY xxe SYSTEM "file:///etc/passwd" >]>
    <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
      <NFe>
        <infNFe>
          <emit><xNome>&xxe;</xNome></emit>
        </infNFe>
      </NFe>
    </nfeProc>
    """
    
    # defusedxml should raise DTDForbidden / EntitiesForbidden when entity expansion is attempted
    with pytest.raises(Exception):
        ET.fromstring(malicious_xxe_xml)


def test_pos_webhook_authentication():
    """Validates that POS webhooks reject requests without valid X-Webhook-Secret."""
    payload = {"order_id": "123", "items": []}
    
    # Request without secret
    res_no_secret = client.post(
        "/integrations/webhook/ifood",
        json=payload,
        headers={"X-Tenant-ID": str(uuid.uuid4())}
    )
    assert res_no_secret.status_code == 401
    assert "Invalid or missing X-Webhook-Secret" in res_no_secret.json()["detail"]

    # Request with invalid secret
    res_bad_secret = client.post(
        "/integrations/webhook/ifood",
        json=payload,
        headers={
            "X-Tenant-ID": str(uuid.uuid4()),
            "X-Webhook-Secret": "invalid_secret_value"
        }
    )
    assert res_bad_secret.status_code == 401

    # Request with valid secret
    res_valid = client.post(
        "/integrations/webhook/ifood",
        json=payload,
        headers={
            "X-Tenant-ID": str(uuid.uuid4()),
            "X-Webhook-Secret": "ksfoodops_pos_webhook_secret_key_default"
        }
    )
    # 202 Accepted because valid secret + valid system
    assert res_valid.status_code == 202
    assert "Processing asynchronously" in res_valid.json()["message"]


def test_ssrf_validator():
    """Validates SSRF protection against internal cloud IPs, localhost, and private CIDR ranges."""
    # Unsafe URLs
    assert is_safe_url("http://169.254.169.254/latest/meta-data/")[0] is False
    assert is_safe_url("http://127.0.0.1:8000/api")[0] is False
    assert is_safe_url("http://localhost:5433")[0] is False
    assert is_safe_url("http://10.0.0.1/admin")[0] is False
    assert is_safe_url("http://192.168.1.1/router")[0] is False
    assert is_safe_url("http://172.16.0.5:8080")[0] is False
    assert is_safe_url("ftp://example.com")[0] is False
    assert is_safe_url("file:///etc/passwd")[0] is False

    # Safe Public URLs
    assert is_safe_url("https://api.github.com")[0] is True
    assert is_safe_url("https://www.google.com")[0] is True


@pytest.mark.asyncio
async def test_two_factor_authentication_flow(db_session):
    """Validates the full 2FA lifecycle: Setup -> Enable -> Login Challenge -> Disable."""
    # 1. Create test user
    email = f"user_2fa_{uuid.uuid4().hex[:8]}@example.com"
    plain_password = "SecurePassword123!"
    user = AppUser(
        email=email,
        password_hash=hash_password(plain_password),
        full_name="2FA Test User",
        is_active=True,
        is_2fa_enabled=False
    )
    db_session.add(user)
    await db_session.commit()

    # 2. Login without 2FA (standard flow)
    login_res = client.post("/auth/login", json={"email": email, "password": plain_password})
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["requires_2fa"] is False
    token = login_data["access_token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # 3. Setup 2FA
    setup_res = client.post("/auth/2fa/setup", headers=auth_header)
    assert setup_res.status_code == 200
    setup_data = setup_res.json()
    totp_secret = setup_data["secret"]
    assert "otpauth_url" in setup_data
    assert totp_secret is not None

    # 4. Enable 2FA with invalid code (should fail)
    bad_enable_res = client.post("/auth/2fa/enable", json={"code": "000000"}, headers=auth_header)
    assert bad_enable_res.status_code == 400

    # 5. Enable 2FA with valid TOTP code
    totp = pyotp.TOTP(totp_secret)
    valid_code = totp.now()
    enable_res = client.post("/auth/2fa/enable", json={"code": valid_code}, headers=auth_header)
    assert enable_res.status_code == 200
    assert enable_res.json()["success"] is True

    # 6. Login with 2FA enabled -> should return requires_2fa=True and temp_token
    login_2fa_res = client.post("/auth/login", json={"email": email, "password": plain_password})
    assert login_2fa_res.status_code == 200
    login_2fa_data = login_2fa_res.json()
    assert login_2fa_data["requires_2fa"] is True
    assert login_2fa_data["access_token"] is None
    temp_token = login_2fa_data["temp_token"]
    assert temp_token is not None

    # 7. Challenge with invalid code (should fail)
    bad_challenge_res = client.post("/auth/2fa/challenge", json={"temp_token": temp_token, "code": "999999"})
    assert bad_challenge_res.status_code == 401

    # 8. Challenge with valid code (should succeed and return access token)
    valid_challenge_code = totp.now()
    challenge_res = client.post("/auth/2fa/challenge", json={"temp_token": temp_token, "code": valid_challenge_code})
    assert challenge_res.status_code == 200
    challenge_data = challenge_res.json()
    assert challenge_data["requires_2fa"] is False
    assert challenge_data["access_token"] is not None
    assert challenge_data["user"]["is_2fa_enabled"] is True

    # 9. Disable 2FA
    new_token = challenge_data["access_token"]
    new_auth_header = {"Authorization": f"Bearer {new_token}"}
    disable_code = totp.now()
    disable_res = client.post(
        "/auth/2fa/disable",
        json={"password": plain_password, "code": disable_code},
        headers=new_auth_header
    )
    assert disable_res.status_code == 200
    assert disable_res.json()["success"] is True

    # 10. Login after 2FA disabled -> standard login
    login_post_disable = client.post("/auth/login", json={"email": email, "password": plain_password})
    assert login_post_disable.status_code == 200
    assert login_post_disable.json()["requires_2fa"] is False
    assert login_post_disable.json()["access_token"] is not None
