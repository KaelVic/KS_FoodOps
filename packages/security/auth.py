import os
import jwt
from pydantic import BaseModel
from typing import Optional

class TokenPayload(BaseModel):
    """
    Standard JWT payload abstraction.
    In a real system, this would match your OIDC provider (Auth0, Cognito, etc.)
    """
    sub: str          # User ID
    email: Optional[str] = None
    
    # We never trust tenant_id from the token or request body directly 
    # to bypass the DB mapping, but we might read it if the user selects 
    # an active tenant in the UI.

def decode_jwt(token: str) -> TokenPayload:
    """
    Decodes and validates a JWT token using PyJWT.
    """
    secret = os.environ.get("JWT_SECRET", "dummy_secret_for_development_32_bytes_long_min!")
    algorithm = os.environ.get("JWT_ALGORITHM", "HS256")
    try:
        # In a real OIDC scenario, you would fetch the JWKS and use RS256
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        # Ensure sub is present
        if "sub" not in payload:
            raise ValueError("Token missing 'sub' claim")
        return TokenPayload(**payload)
    except jwt.PyJWTError as e:
        raise ValueError(f"Invalid token: {e}")
