import pytest
from fastapi.testclient import TestClient
import io

from apps.api.main import app

client = TestClient(app)

def test_security_headers_present():
    """Verify that all required security headers are present in responses."""
    response = client.get("/health")
    assert response.status_code == 200
    
    headers = response.headers
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert "max-age=31536000" in headers.get("Strict-Transport-Security", "")
    assert "default-src 'self'" in headers.get("Content-Security-Policy", "")
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_rate_limiting_health_endpoint():
    """Verify that rate limiting returns 429 when limit is exceeded."""
    # Health endpoint is limited to 10/minute
    # We'll make 11 requests
    status_codes = []
    for _ in range(12):
        res = client.get("/health")
        status_codes.append(res.status_code)
    
    # At least one should be 429
    assert 429 in status_codes
    
    # Reset limiter storage so subsequent tests are not blocked
    if hasattr(app.state, "limiter") and hasattr(app.state.limiter, "reset"):
        app.state.limiter.reset()



def test_upload_nfe_size_limit(monkeypatch):
    """Verify that uploading a file larger than 10MB returns 413."""
    from packages.security.dependencies import get_secure_session
    from packages.tenant.rls import set_current_tenant_id
    import uuid
    
    tenant_id = uuid.uuid4()
    
    # Create a dummy large file (> 10MB)
    large_content = b"x" * (10 * 1024 * 1024 + 1024)  # 10MB + 1KB
    file = io.BytesIO(large_content)
    file.name = "large_file.xml"
    
    app.dependency_overrides[get_secure_session] = lambda: None
    from packages.security.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: None
    
    set_current_tenant_id(tenant_id)
    
    response = client.post(
        "/documents/upload-nfe",
        files={"file": ("large_file.xml", file, "text/xml")}
    )
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 413
    assert "exceeds 10MB" in response.json()["detail"]


def test_upload_nfe_invalid_mimetype():
    """Verify that uploading a non-XML file returns 400."""
    from packages.security.dependencies import get_secure_session
    from packages.security.dependencies import get_current_user
    from packages.tenant.rls import set_current_tenant_id
    import uuid
    
    tenant_id = uuid.uuid4()
    app.dependency_overrides[get_secure_session] = lambda: None
    app.dependency_overrides[get_current_user] = lambda: None
    set_current_tenant_id(tenant_id)
    
    content = b"<xml></xml>"
    file = io.BytesIO(content)
    file.name = "test.xml"
    
    response = client.post(
        "/documents/upload-nfe",
        files={"file": ("test.xml", file, "application/pdf")} # Invalid mime
    )
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 400
    assert "File must be XML" in response.json()["detail"]
