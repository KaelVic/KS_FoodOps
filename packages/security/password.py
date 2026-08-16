import bcrypt

def hash_password(plain: str) -> str:
    """
    Hashes a plaintext password using bcrypt directly.
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    """
    Verifies a plaintext password against a bcrypt hash directly.
    """
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
