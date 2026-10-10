from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings

settings = get_settings()


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(account_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": account_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(seconds=settings.access_token_expire_seconds),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_pending_verification_token(account_id: str) -> str:
    """A short-lived, narrowly-scoped token issued after register/login for
    an account that hasn't finished email+phone verification yet. Carries
    `purpose: "pending_verification"` so `get_current_account` (deps.py)
    refuses it for normal endpoints — it's only accepted by the
    /api/auth/verify* routes."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": account_id,
        "purpose": "pending_verification",
        "iat": now,
        "exp": now + timedelta(minutes=settings.pending_verification_token_ttl_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
