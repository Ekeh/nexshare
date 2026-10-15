"""Email/phone verification: generate a code, deliver it (via
app/services/notifications), and check what the user types back.

Codes live in Redis, not Postgres — a short-lived, write-once secret with
no reporting value once consumed or expired is exactly what Redis's TTL is
for, and it means expiry is enforced by Redis itself rather than by a
manually-checked `expires_at` column. Requesting a new code overwrites/
invalidates any unconsumed one for that account+channel, so only the most
recently sent code ever works.

Stored in plaintext, not hashed — this is local-dev-only (no production
deployment yet) and the code is already logged in cleartext to the console
on every send, so hashing at rest wouldn't have raised the bar here. Revisit
this (hash it, same as passwords — see git history for the previous
version) before this is ever exposed beyond local dev.
"""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.redis import get_redis
from app.models.core import Account
from app.services.notifications import get_email_sender, get_sms_sender

settings = get_settings()
logger = logging.getLogger("nexshare.verification")


class VerificationError(Exception):
    """reason is one of: 'no_active_code', 'too_many_attempts', 'invalid_code'."""

    def __init__(self, reason: str, message: str):
        self.reason = reason
        super().__init__(message)


class ResendTooSoonError(Exception):
    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Wait {retry_after_seconds}s before requesting another code")


def _code_key(account_id, channel: str) -> str:
    return f"verification:{account_id}:{channel}"


def _cooldown_key(account_id, channel: str) -> str:
    return f"verification:cooldown:{account_id}:{channel}"


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def generate_and_send_code(db: Session, account: Account, channel: str, *, enforce_cooldown: bool = True) -> str:
    r = get_redis()
    cooldown_key = _cooldown_key(account.id, channel)

    if enforce_cooldown:
        # SET ... NX is atomic: this both checks and claims the cooldown
        # window in one round trip, so two near-simultaneous resend clicks
        # can't both slip through.
        if not r.set(cooldown_key, "1", ex=settings.verification_resend_cooldown_seconds, nx=True):
            raise ResendTooSoonError(r.ttl(cooldown_key))
    else:
        # Registration's initial send doesn't need to check the cooldown
        # (there's nothing to be too soon after yet), but it still has to
        # *claim* the window — otherwise an immediate explicit resend right
        # after registering wouldn't be throttled at all.
        r.set(cooldown_key, "1", ex=settings.verification_resend_cooldown_seconds)

    code = _generate_code()
    r.hset(
        _code_key(account.id, channel),
        mapping={"code": code, "attempts": 0},
    )
    r.expire(_code_key(account.id, channel), settings.verification_code_ttl_minutes * 60)

    # Always logged, independent of whether a real provider is configured
    # below — convenient for local development even when Resend/Termii
    # keys are set, and it's still just a 10-minute-lived, single-use code.
    # WARNING, not INFO: nothing configures the "nexshare" logger's level,
    # so under Python's default logging setup INFO is silently dropped —
    # WARNING is the lowest level actually visible without extra config.
    destination = account.email if channel == "email" else account.phone
    logger.warning("Verification code for %s (%s): %s", destination, channel, code)

    message = f"Your NexShare verification code is {code}. It expires in {settings.verification_code_ttl_minutes} minutes."
    if channel == "email":
        get_email_sender().send(to=account.email, subject="Verify your NexShare account", body=message)
    else:
        get_sms_sender().send(to=account.phone, body=message)

    return code


def verify_code(db: Session, account: Account, channel: str, submitted_code: str) -> None:
    """Raises VerificationError on any failure; otherwise consumes the code
    (deletes it from Redis) and sets accounts.{channel}_verified_at."""
    r = get_redis()
    key = _code_key(account.id, channel)

    record = r.hgetall(key)
    if not record:
        # No distinction from "expired" — Redis has already reaped it
        # either way, and the fix is the same: request a new code.
        raise VerificationError("no_active_code", "Request a new code first.")

    if int(record["attempts"]) >= settings.verification_max_attempts:
        raise VerificationError("too_many_attempts", "Too many incorrect attempts — request a new code.")

    # Constant-time compare — free to keep even in plaintext, avoids a
    # cheap timing side-channel on the comparison itself.
    if not secrets.compare_digest(submitted_code, record["code"]):
        r.hincrby(key, "attempts", 1)
        raise VerificationError("invalid_code", "That code isn't right.")

    r.delete(key)
    now = datetime.now(timezone.utc)
    if channel == "email":
        account.email_verified_at = now
    else:
        account.phone_verified_at = now
    db.commit()
