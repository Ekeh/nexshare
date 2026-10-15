import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_account, get_pending_verification_account
from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import create_access_token, create_pending_verification_token, hash_password, verify_password
from app.models.core import Account
from app.services.verification import ResendTooSoonError, VerificationError, generate_and_send_code, verify_code

router = APIRouter()
settings = get_settings()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    phone: str = Field(min_length=7, max_length=20)
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=200)
    role: str = "promoter"
    country_code: str = "NG"

    @field_validator("role")
    @classmethod
    def role_must_be_self_serve(cls, v: str) -> str:
        if v not in ("promoter", "business"):
            raise ValueError("role must be 'promoter' or 'business'")
        return v


class AccountOut(BaseModel):
    id: str
    email: str
    role: str
    full_name: str
    kyc_status: str
    access_token: str | None = None
    token_type: str = "bearer"


class PendingVerificationOut(BaseModel):
    account_id: str
    email: str
    phone: str
    email_verified: bool
    phone_verified: bool
    pending_verification_token: str
    # Only populated while the real provider for that channel isn't
    # configured (RESEND_API_KEY / TERMII_API_KEY unset) — see
    # generate_and_send_code's callers below. Lets a tester (or anyone,
    # before those providers go live) finish verifying without log access.
    email_test_code: str | None = None
    phone_test_code: str | None = None


class VerifyRequest(BaseModel):
    channel: Literal["email", "phone"]
    code: str


class ResendRequest(BaseModel):
    channel: Literal["email", "phone"]


class VerifyOut(BaseModel):
    channel: str
    fully_verified: bool
    account: AccountOut | None = None


class ResendOut(BaseModel):
    test_code: str | None = None


def _issue_token_response(response: Response, account: Account) -> AccountOut:
    token = create_access_token(str(account.id), account.role)
    # Browser clients: httpOnly cookie (JS can't read it, immune to XSS token
    # theft). Non-browser clients (future mobile app, per architecture.md):
    # use the `access_token` in the JSON body as a standard Bearer token.
    response.set_cookie(
        key=settings.access_token_cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=settings.access_token_expire_seconds,
        path="/",
    )
    return AccountOut(
        id=str(account.id),
        email=account.email,
        role=account.role,
        full_name=account.full_name,
        kyc_status=account.kyc_status,
        access_token=token,
    )


def _is_fully_verified(account: Account) -> bool:
    return account.email_verified_at is not None and account.phone_verified_at is not None


def _pending_verification_out(
    account: Account,
    *,
    email_test_code: str | None = None,
    phone_test_code: str | None = None,
) -> PendingVerificationOut:
    return PendingVerificationOut(
        account_id=str(account.id),
        email=account.email,
        phone=account.phone,
        email_verified=account.email_verified_at is not None,
        phone_verified=account.phone_verified_at is not None,
        pending_verification_token=create_pending_verification_token(str(account.id)),
        email_test_code=email_test_code,
        phone_test_code=phone_test_code,
    )


@router.post("/login", response_model=AccountOut)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> AccountOut:
    account = db.scalar(select(Account).where(Account.email == payload.email))
    if account is None or not verify_password(payload.password, account.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not _is_fully_verified(account):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email and phone number before logging in.",
        )

    return _issue_token_response(response, account)


@router.post("/register", response_model=PendingVerificationOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> PendingVerificationOut:
    existing_email = db.scalar(select(Account).where(Account.email == payload.email))
    if existing_email is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    existing_phone = db.scalar(select(Account).where(Account.phone == payload.phone))
    if existing_phone is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="An account with this phone number already exists"
        )

    account = Account(
        id=uuid.uuid4(),
        role=payload.role,
        email=payload.email,
        phone=payload.phone,
        country_code=payload.country_code,
        kyc_status="unverified",
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(account)
    try:
        db.commit()
    except IntegrityError:
        # Belt-and-suspenders for the above check-then-insert: two
        # concurrent registrations with the same email/phone can both pass
        # the checks above before either commits. The DB's unique
        # constraints are the real guarantee; this just keeps the response
        # a friendly 409 instead of a raw 500 in that race.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email or phone number already exists",
        )
    db.refresh(account)

    email_code = generate_and_send_code(db, account, "email", enforce_cooldown=False)
    phone_code = generate_and_send_code(db, account, "phone", enforce_cooldown=False)

    return _pending_verification_out(
        account,
        email_test_code=email_code if not settings.resend_api_key else None,
        phone_test_code=phone_code if not settings.termii_api_key else None,
    )


@router.post("/verify/start", response_model=PendingVerificationOut)
def verify_start(payload: LoginRequest, db: Session = Depends(get_db)) -> PendingVerificationOut:
    """Re-proves identity via password (like /login) and hands back a fresh
    pending-verification token — for a registered-but-never-finished-
    verifying user coming back later, since register's token has likely
    expired and /login refuses to issue one for an unverified account.

    Also (re)sends a code for each still-unverified channel, same as
    register() — the whole point of calling this is "let me finish
    verifying," and the original codes from registration may be long
    expired (or, since login is what routes here, the frontend's countdown
    UI needs something to actually be in flight)."""
    account = db.scalar(select(Account).where(Account.email == payload.email))
    if account is None or not verify_password(payload.password, account.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    email_test_code = None
    phone_test_code = None
    if account.email_verified_at is None:
        email_code = generate_and_send_code(db, account, "email", enforce_cooldown=False)
        email_test_code = email_code if not settings.resend_api_key else None
    if account.phone_verified_at is None:
        phone_code = generate_and_send_code(db, account, "phone", enforce_cooldown=False)
        phone_test_code = phone_code if not settings.termii_api_key else None

    return _pending_verification_out(account, email_test_code=email_test_code, phone_test_code=phone_test_code)


@router.post("/verify", response_model=VerifyOut)
def verify(
    payload: VerifyRequest,
    response: Response,
    account: Account = Depends(get_pending_verification_account),
    db: Session = Depends(get_db),
) -> VerifyOut:
    try:
        verify_code(db, account, payload.channel, payload.code)
    except VerificationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    fully_verified = _is_fully_verified(account)
    return VerifyOut(
        channel=payload.channel,
        fully_verified=fully_verified,
        account=_issue_token_response(response, account) if fully_verified else None,
    )


@router.post("/verify/resend", response_model=ResendOut)
def resend_code(
    payload: ResendRequest,
    account: Account = Depends(get_pending_verification_account),
    db: Session = Depends(get_db),
) -> ResendOut:
    try:
        code = generate_and_send_code(db, account, payload.channel)
    except ResendTooSoonError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {exc.retry_after_seconds}s before requesting another code",
        )

    channel_key_set = settings.resend_api_key if payload.channel == "email" else settings.termii_api_key
    return ResendOut(test_code=code if not channel_key_set else None)


@router.post("/logout")
def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(settings.access_token_cookie_name, path="/")
    return {"ok": True}


@router.get("/me", response_model=AccountOut)
def me(account: Account = Depends(get_current_account)) -> AccountOut:
    return AccountOut(
        id=str(account.id),
        email=account.email,
        role=account.role,
        full_name=account.full_name,
        kyc_status=account.kyc_status,
    )
