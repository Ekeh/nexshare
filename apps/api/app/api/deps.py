import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import decode_access_token
from app.models.core import Account

settings = get_settings()


def _extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:]
    return request.cookies.get(settings.access_token_cookie_name)


def get_current_account(request: Request, db: Session = Depends(get_db)) -> Account:
    token = _extract_token(request)
    payload = decode_access_token(token) if token else None
    # A pending-verification token (register/login for an unverified
    # account) is intentionally not a real session — only /api/auth/verify*
    # (get_pending_verification_account, below) accepts it.
    if payload is None or payload.get("purpose") == "pending_verification":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    account = db.get(Account, uuid.UUID(payload["sub"]))
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return account


def get_pending_verification_account(request: Request, db: Session = Depends(get_db)) -> Account:
    """For /api/auth/verify* only: requires the narrow pending-verification
    token (see create_pending_verification_token), not a normal session."""
    token = _extract_token(request)
    payload = decode_access_token(token) if token else None
    if payload is None or payload.get("purpose") != "pending_verification":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired verification session — please log in again",
            headers={"WWW-Authenticate": "Bearer"},
        )

    account = db.get(Account, uuid.UUID(payload["sub"]))
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired verification session — please log in again",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return account


def require_role(*roles: str):
    """Dependency factory: 401 with no/invalid token, 403 if the token's
    account doesn't hold one of the required roles ("necessary access")."""

    def dependency(account: Account = Depends(get_current_account)) -> Account:
        if account.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(roles)}",
            )
        return account

    return dependency


require_promoter = require_role("promoter")
require_business = require_role("business")


def get_business_from_webhook_secret(request: Request, db: Session = Depends(get_db)) -> Account:
    """For POST /api/webhooks/* only: a business's own server calls these,
    not a browser with a cookie — authenticated with the static
    `webhook_secret` from GET /api/business/webhook-secret, sent as a
    normal bearer token. Deliberately separate from get_current_account:
    a session JWT must never work here, and this must never work on a
    cookie/session-authenticated route."""
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing webhook credentials")

    account = db.scalar(select(Account).where(Account.webhook_secret == token, Account.role == "business"))
    if account is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook credentials")
    return account
