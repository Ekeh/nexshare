"""POST /api/webhooks/paystack — signature verification and event ->
Payout status mapping. Paystack itself is never contacted; this only
exercises our own handler against a synthetic, correctly (or incorrectly)
signed payload, matching how Paystack actually calls this endpoint.
"""
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone

import pytest

from app.models.core import Payout
from tests.factories import make_account


def _sign(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()


@pytest.fixture()
def paystack_configured(monkeypatch):
    from app.api.routes import webhooks as webhooks_module

    monkeypatch.setattr(webhooks_module.settings, "paystack_secret_key", "sk_test_fake_webhook_secret")
    return "sk_test_fake_webhook_secret"


@pytest.fixture()
def processing_payout(db, unique_suffix):
    promoter = make_account(db, role="promoter", suffix=unique_suffix)
    payout = Payout(
        id=uuid.uuid4(),
        promoter_id=promoter.id,
        amount_minor_units=5000,
        currency="NGN",
        payout_method="bank_transfer",
        status="processing",
        requested_at=datetime.now(timezone.utc),
        paystack_reference=f"ref-{unique_suffix}",
        paystack_transfer_code=f"TRF_{unique_suffix}",
    )
    db.add(payout)
    db.commit()
    return payout


def test_returns_503_when_paystack_not_configured(client):
    res = client.post("/api/webhooks/paystack", json={"event": "transfer.success", "data": {}})
    assert res.status_code == 503


def test_invalid_signature_is_rejected(client, paystack_configured):
    body = json.dumps({"event": "transfer.success", "data": {}}).encode()
    res = client.post(
        "/api/webhooks/paystack", content=body, headers={"x-paystack-signature": "not-the-real-signature"}
    )
    assert res.status_code == 401


def test_transfer_success_marks_payout_completed(client, db, paystack_configured, processing_payout):
    payload = {
        "event": "transfer.success",
        "data": {"reference": processing_payout.paystack_reference, "transfer_code": processing_payout.paystack_transfer_code},
    }
    body = json.dumps(payload).encode()
    res = client.post(
        "/api/webhooks/paystack", content=body, headers={"x-paystack-signature": _sign(body, paystack_configured)}
    )
    assert res.status_code == 200

    db.refresh(processing_payout)
    assert processing_payout.status == "completed"


def test_transfer_failed_marks_payout_failed_with_reason(client, db, paystack_configured, processing_payout):
    payload = {
        "event": "transfer.failed",
        "data": {"reference": processing_payout.paystack_reference, "reason": "Insufficient funds"},
    }
    body = json.dumps(payload).encode()
    res = client.post(
        "/api/webhooks/paystack", content=body, headers={"x-paystack-signature": _sign(body, paystack_configured)}
    )
    assert res.status_code == 200

    db.refresh(processing_payout)
    assert processing_payout.status == "failed"
    assert processing_payout.failure_reason == "Insufficient funds"


def test_unrecognized_event_is_ignored_not_errored(client, paystack_configured, processing_payout):
    payload = {"event": "recipient.created", "data": {}}
    body = json.dumps(payload).encode()
    res = client.post(
        "/api/webhooks/paystack", content=body, headers={"x-paystack-signature": _sign(body, paystack_configured)}
    )
    assert res.status_code == 200
    assert res.json()["ignored"] == "recipient.created"


def test_unknown_reference_does_not_error(client, paystack_configured):
    payload = {"event": "transfer.success", "data": {"reference": "no-such-reference"}}
    body = json.dumps(payload).encode()
    res = client.post(
        "/api/webhooks/paystack", content=body, headers={"x-paystack-signature": _sign(body, paystack_configured)}
    )
    assert res.status_code == 200
    assert res.json()["matched"] is False
