"""Termii (https://termii.com) SmsSender implementation — built for
Nigerian/African routes, matching this project's NG-default accounts. Swap
for another provider by writing a class with the same `send()` signature
and pointing `get_sms_sender()` (__init__.py) at it."""
from __future__ import annotations

import httpx

TERMII_API_URL = "https://api.ng.termii.com/api/sms/send"


class TermiiSmsSender:
    def __init__(self, *, api_key: str, sender_id: str):
        self._api_key = api_key
        self._sender_id = sender_id

    def send(self, *, to: str, body: str) -> None:
        response = httpx.post(
            TERMII_API_URL,
            json={
                "api_key": self._api_key,
                "to": to,
                "from": self._sender_id,
                "sms": body,
                "type": "plain",
                "channel": "generic",
            },
            timeout=10.0,
        )
        response.raise_for_status()
