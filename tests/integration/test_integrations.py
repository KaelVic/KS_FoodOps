import pytest
import json
import hmac
import hashlib
from packages.integrations.webhooks import WebhookValidator

def test_webhook_signature_verification():
    payload = {"event": "order_created", "order_id": "123"}
    payload_bytes = json.dumps(payload).encode('utf-8')
    secret = "my_super_secret_webhook_key"
    
    # Generate valid signature
    valid_signature = hmac.new(
        key=secret.encode('utf-8'),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Test valid
    assert WebhookValidator.verify_signature(payload_bytes, secret, valid_signature) is True
    
    # Test invalid signature
    assert WebhookValidator.verify_signature(payload_bytes, secret, "invalid_signature") is False
    
    # Test invalid secret
    assert WebhookValidator.verify_signature(payload_bytes, "wrong_secret", valid_signature) is False
    
    # Test empty secret or signature
    assert WebhookValidator.verify_signature(payload_bytes, "", valid_signature) is False
    assert WebhookValidator.verify_signature(payload_bytes, secret, "") is False

def test_webhook_payload_parsing():
    payload = {"event": "order_created", "order_id": "123"}
    payload_bytes = json.dumps(payload).encode('utf-8')
    
    parsed = WebhookValidator.parse_payload(payload_bytes)
    assert parsed["event"] == "order_created"
    assert parsed["order_id"] == "123"
