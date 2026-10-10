"""Paystack (https://paystack.com) client — the real payment rail behind
promoter payouts. Previously `POST /promoters/me/withdraw` (payouts.py)
created a Payout row that stayed "requested" forever; this module is what
lets it actually become "completed" (or "failed").

Flow: a promoter saves a payout destination (`PayoutAccount` — resolved
against Paystack's `/bank/resolve` so a typo'd account number is caught
before anything is sent, then registered as a Paystack transfer recipient).
Withdrawing initiates a real transfer to that recipient
(`app/services/payouts.py`); Paystack confirms it asynchronously via a
webhook (`POST /api/webhooks/paystack`) — `app/scripts/sync_payouts.py`
polls as a fallback for any payout a webhook never reached, the same
"no scheduler, run this by hand or from cron" pattern as
`process_commissions`.

Test-mode transfers (a `sk_test_...` secret key) never move real money —
Paystack simulates the whole lifecycle, including a delayed
`transfer.success` webhook, against synthetic test bank data.
"""
from __future__ import annotations

import hashlib
import hmac
from typing import Any

import httpx

BASE_URL = "https://api.paystack.co"


class PaystackError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class PaystackClient:
    def __init__(self, secret_key: str):
        self._secret_key = secret_key

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._secret_key}", "Content-Type": "application/json"}

    def _request(self, method: str, path: str, *, params: dict | None = None, json: dict | None = None) -> dict:
        response = httpx.request(
            method, f"{BASE_URL}{path}", headers=self._headers(), params=params, json=json, timeout=15.0
        )
        body = response.json()
        if not body.get("status"):
            raise PaystackError(body.get("message", "Paystack request failed"), status_code=response.status_code)
        return body["data"]

    def list_banks(self, *, currency: str = "NGN") -> list[dict[str, Any]]:
        return self._request("GET", "/bank", params={"currency": currency, "perPage": 100})

    def resolve_account(self, *, account_number: str, bank_code: str) -> dict[str, Any]:
        """Raises PaystackError if the account number/bank combination
        doesn't resolve to a real account — the caller's confirmation that
        a payout destination isn't just typo'd digits."""
        return self._request(
            "GET", "/bank/resolve", params={"account_number": account_number, "bank_code": bank_code}
        )

    def create_transfer_recipient(
        self, *, account_number: str, bank_code: str, account_name: str, currency: str = "NGN"
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/transferrecipient",
            json={
                "type": "nuban",
                "name": account_name,
                "account_number": account_number,
                "bank_code": bank_code,
                "currency": currency,
            },
        )

    def initiate_transfer(
        self, *, amount_minor_units: int, recipient_code: str, reference: str, reason: str, currency: str = "NGN"
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/transfer",
            json={
                "source": "balance",
                "amount": amount_minor_units,
                "recipient": recipient_code,
                "reference": reference,
                "reason": reason,
                "currency": currency,
            },
        )

    def fetch_transfer(self, transfer_code: str) -> dict[str, Any]:
        return self._request("GET", f"/transfer/{transfer_code}")


def verify_webhook_signature(*, payload: bytes, signature: str, secret_key: str) -> bool:
    expected = hmac.new(secret_key.encode(), payload, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature)
