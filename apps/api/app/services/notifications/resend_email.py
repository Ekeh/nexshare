"""Resend (https://resend.com) EmailSender implementation. Swap for another
provider by writing a class with the same `send()` signature and pointing
`get_email_sender()` (__init__.py) at it — nothing else in the codebase
references Resend directly."""
from __future__ import annotations

import httpx

RESEND_API_URL = "https://api.resend.com/emails"


class ResendEmailSender:
    def __init__(self, *, api_key: str, from_address: str):
        self._api_key = api_key
        self._from_address = from_address

    def send(self, *, to: str, subject: str, body: str) -> None:
        response = httpx.post(
            RESEND_API_URL,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "from": self._from_address,
                "to": [to],
                "subject": subject,
                "text": body,
            },
            timeout=10.0,
        )
        response.raise_for_status()
