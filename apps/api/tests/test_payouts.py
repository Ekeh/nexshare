"""app/services/payouts.py — request_payout(). Paystack is force-unset for
the whole test session (see conftest.py), so PaystackClient is stubbed here
rather than hitting the network: these tests are about payouts.py's own
branching (no balance / no payout account / provider rejects / provider
accepts and the resulting rollback-or-not), not about Paystack's API.
"""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.models.core import Commission, LedgerEntry, Payout, PayoutAccount
from app.services import payouts as payouts_module
from app.services.paystack import PaystackError
from app.services.payouts import NoAvailableBalanceError, NoPayoutAccountError, PayoutProviderError, request_payout
from tests.factories import make_account, make_click, make_commission, make_conversion, make_offer_campaign, make_tracking_link


@pytest.fixture()
def payout_setup(db, unique_suffix):
    business = make_account(db, role="business", suffix=unique_suffix)
    promoter = make_account(db, role="promoter", suffix=unique_suffix)
    offer, campaign = make_offer_campaign(db, business=business)
    link = make_tracking_link(db, campaign=campaign, promoter=promoter, short_code=f"sc{unique_suffix}")
    click_row_id, _, click_at = make_click(db, tracking_link=link)
    conversion = make_conversion(db, campaign=campaign, click_row_id=click_row_id, click_occurred_at=click_at)
    commission = make_commission(
        db, conversion=conversion, promoter=promoter, amount_minor_units=5000, currency="NGN", status="available"
    )
    # Commit the fixture as its own checkpoint: request_payout() rolls back
    # on a provider rejection, and since this test session joins a savepoint
    # that a rollback ends (see conftest.py's `db` fixture), an uncommitted
    # fixture would be wiped out along with the withdrawal's own changes.
    db.commit()
    return {"promoter": promoter, "commission": commission}


def _save_payout_account(db, promoter) -> PayoutAccount:
    """Models a payout account saved via its own earlier, already-committed
    request — matching real usage, and giving request_payout()'s internal
    rollback (on a provider rejection) a safe boundary that doesn't also
    wipe this out."""
    pa = PayoutAccount(
        id=uuid.uuid4(),
        promoter_id=promoter.id,
        payout_method="bank_transfer",
        bank_code="057",
        bank_name="Zenith Bank",
        account_number="0000000000",
        account_name="Test",
        paystack_recipient_code="RCP_test",
    )
    db.add(pa)
    db.commit()
    return pa


def test_no_available_balance_raises(db, unique_suffix):
    promoter = make_account(db, role="promoter", suffix=unique_suffix)
    with pytest.raises(NoAvailableBalanceError):
        request_payout(db, promoter, "bank_transfer")


def test_without_paystack_configured_creates_a_requested_payout_with_no_account_needed(db, payout_setup):
    payout = request_payout(db, payout_setup["promoter"], "bank_transfer")
    assert payout.status == "requested"
    assert payout.paystack_reference is None

    db.refresh(payout_setup["commission"])
    assert payout_setup["commission"].status == "paid"


def test_with_paystack_configured_but_no_payout_account_raises(db, payout_setup, monkeypatch):
    monkeypatch.setattr(payouts_module.settings, "paystack_secret_key", "sk_test_fake")
    with pytest.raises(NoPayoutAccountError):
        request_payout(db, payout_setup["promoter"], "bank_transfer")


def test_provider_success_marks_payout_processing_and_stores_paystack_ids(db, payout_setup, monkeypatch):
    monkeypatch.setattr(payouts_module.settings, "paystack_secret_key", "sk_test_fake")
    _save_payout_account(db, payout_setup["promoter"])

    class _FakeClient:
        def __init__(self, secret_key):
            pass

        def initiate_transfer(self, **kwargs):
            return {"status": "pending", "transfer_code": "TRF_fake_123"}

    monkeypatch.setattr(payouts_module, "PaystackClient", _FakeClient)

    payout = request_payout(db, payout_setup["promoter"], "bank_transfer")
    assert payout.status == "processing"
    assert payout.paystack_transfer_code == "TRF_fake_123"
    assert payout.paystack_reference == str(payout.id)


def test_provider_rejection_rolls_back_the_entire_withdrawal(db, payout_setup, monkeypatch):
    monkeypatch.setattr(payouts_module.settings, "paystack_secret_key", "sk_test_fake")
    _save_payout_account(db, payout_setup["promoter"])

    class _FailingClient:
        def __init__(self, secret_key):
            pass

        def initiate_transfer(self, **kwargs):
            raise PaystackError("insufficient platform balance")

    monkeypatch.setattr(payouts_module, "PaystackClient", _FailingClient)

    with pytest.raises(PayoutProviderError):
        request_payout(db, payout_setup["promoter"], "bank_transfer")

    # nothing from the failed attempt should have survived: the commission
    # is still available, no Payout or ledger entry exists for it
    db.refresh(payout_setup["commission"])
    assert payout_setup["commission"].status == "available"
    assert db.scalars(select(Payout).where(Payout.promoter_id == payout_setup["promoter"].id)).all() == []
    assert db.scalars(select(LedgerEntry).where(LedgerEntry.account_id == payout_setup["promoter"].id)).all() == []
