"""Provider-agnostic notification ports. Verification logic
(app/services/verification.py) depends only on these Protocols — swapping
the email or SMS vendor is writing one new adapter class here and pointing
the factory (__init__.py) at it, never touching the verification flow."""
from __future__ import annotations

from typing import Protocol


class EmailSender(Protocol):
    def send(self, *, to: str, subject: str, body: str) -> None: ...


class SmsSender(Protocol):
    def send(self, *, to: str, body: str) -> None: ...
