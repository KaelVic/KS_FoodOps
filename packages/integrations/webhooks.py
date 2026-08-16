import hmac
import hashlib
import json
from typing import Any, Dict

class WebhookValidator:
    """
    Utility class for validating standard POS webhooks (iFood, TOTVS, Linx, Saipos).
    Uses HMAC SHA-256 for integrity verification.
    """
    
    @staticmethod
    def verify_signature(payload_bytes: bytes, secret: str, signature: str) -> bool:
        """
        Verifies if the provided HMAC SHA-256 signature matches the payload.
        
        Args:
            payload_bytes: The raw bytes of the request body.
            secret: The webhook secret shared with the POS provider.
            signature: The signature provided in the headers (e.g., X-Signature).
            
        Returns:
            bool: True if signature is valid, False otherwise.
        """
        if not secret or not signature:
            return False
            
        expected_signature = hmac.new(
            key=secret.encode('utf-8'),
            msg=payload_bytes,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)

    @staticmethod
    def parse_payload(payload_bytes: bytes) -> Dict[str, Any]:
        """
        Parses the JSON payload. Should be called only after signature verification.
        """
        return json.loads(payload_bytes.decode('utf-8'))
