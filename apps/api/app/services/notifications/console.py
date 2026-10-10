"""Fallback senders used when no provider API key is configured, so the app
runs (and verification is genuinely testable end-to-end) without requiring
a Resend/Termii account. Never used if the corresponding API key is set —
see app/services/notifications/__init__.py.

These just note that delivery didn't really happen — the code itself is
already logged unconditionally by app/services/verification.py, real
provider configured or not, so it isn't repeated here."""
from __future__ import annotations

import logging

logger = logging.getLogger("nexshare.notifications")


class ConsoleEmailSender:
    def send(self, *, to: str, subject: str, body: str) -> None:
        logger.warning("RESEND_API_KEY not set — email to %s not actually sent.", to)


class ConsoleSmsSender:
    def send(self, *, to: str, body: str) -> None:
        logger.warning("TERMII_API_KEY not set — SMS to %s not actually sent.", to)
