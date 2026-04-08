"""
JWT Token Utilities — Issue 4 fix.
Creates and verifies JWT tokens for authentication.
"""

import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

# Secret key for JWT signing — use env var or fallback
JWT_SECRET = os.getenv("JWT_SECRET", "claimassist_jwt_secret_2026_change_in_production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))


def create_access_token(email: str, full_name: str = "") -> str:
    """Create a signed JWT token with user claims."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": email,              # subject (user email)
        "name": full_name,
        "iat": now,                # issued at
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),  # expiry
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict]:
    """
    Verify and decode a JWT token.
    Returns the payload dict on success, or None on failure.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        print("[JWT] Token expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"[JWT] Invalid token: {e}")
        return None
