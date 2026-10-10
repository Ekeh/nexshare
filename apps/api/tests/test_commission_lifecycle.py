"""app/services/commission_lifecycle.py — the one place legal status
transitions are enforced and ledger entries posted. Covers: illegal
transitions are rejected and change nothing, ledger entries post on the
right transitions (and only those), and the automatic sweep's two
rule-based gates (fraud flags, hold period).
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models.core import FraudFlag, LedgerEntry
from app.services.commission_lifecycle import IllegalTransitionError, run_lifecycle_sweep, transition
from tests.factories import make_account, make_click, make_commission, make_conversion, make_offer_campaign, make_tracking_link


@pytest.fixture()
def commission_setup(db, unique_suffix):
    business = make_account(db, role="business", suffix=unique_suffix)
    promoter = make_account(db, role="promoter", suffix=unique_suffix)
    offer, campaign = make_offer_campaign(db, business=business)
    link = make_tracking_link(db, campaign=campaign, promoter=promoter, short_code=f"sc{unique_suffix}")
    click_row_id, _, click_at = make_click(db, tracking_link=link)
    conversion = make_conversion(db, campaign=campaign, click_row_id=click_row_id, click_occurred_at=click_at)
    commission = make_commission(db, conversion=conversion, promoter=promoter, amount_minor_units=5000, status="pending")
    return {"commission": commission, "conversion": conversion, "campaign": campaign, "promoter": promoter}


def test_illegal_transition_raises_and_changes_nothing(db, commission_setup):
    commission = commission_setup["commission"]
    with pytest.raises(IllegalTransitionError):
        transition(db, commission, "paid", reason="test: skip straight to paid")
    assert commission.status == "pending"
    assert commission.status_history == []


def test_pending_to_approved_is_legal_and_posts_no_ledger_entry(db, commission_setup):
    commission = commission_setup["commission"]
    transition(db, commission, "approved", reason="test")
    assert commission.status == "approved"
    entries = db.scalars(select(LedgerEntry).where(LedgerEntry.commission_id == commission.id)).all()
    assert entries == []


def test_available_posts_commission_earned_entry(db, commission_setup):
    commission = commission_setup["commission"]
    transition(db, commission, "approved", reason="test")
    transition(db, commission, "available", reason="test")

    entries = db.scalars(select(LedgerEntry).where(LedgerEntry.commission_id == commission.id)).all()
    assert len(entries) == 1
    assert entries[0].entry_type == "commission_earned"
    assert entries[0].amount_minor_units == commission.amount_minor_units


def test_reversal_from_approved_posts_no_entry_but_reversal_from_available_nets_it_out(db, commission_setup):
    commission = commission_setup["commission"]
    transition(db, commission, "approved", reason="test")
    transition(db, commission, "reversed", reason="test")

    entries = db.scalars(select(LedgerEntry).where(LedgerEntry.commission_id == commission.id)).all()
    assert entries == [], "nothing was ever earned, so nothing needs netting out"


def test_reversal_from_available_posts_offsetting_entry(db, commission_setup):
    commission = commission_setup["commission"]
    transition(db, commission, "approved", reason="test")
    transition(db, commission, "available", reason="test")
    transition(db, commission, "reversed", reason="test")

    entries = db.scalars(
        select(LedgerEntry).where(LedgerEntry.commission_id == commission.id).order_by(LedgerEntry.created_at)
    ).all()
    assert [e.entry_type for e in entries] == ["commission_earned", "commission_reversed"]
    assert entries[0].amount_minor_units == commission.amount_minor_units
    assert entries[1].amount_minor_units == -commission.amount_minor_units
    # the original entry is never edited or deleted — only ever netted by a new one
    assert entries[0].amount_minor_units == commission.amount_minor_units


def test_sweep_blocks_pending_to_approved_while_a_fraud_flag_is_unresolved(db, commission_setup):
    commission = commission_setup["commission"]
    db.add(
        FraudFlag(
            id=uuid.uuid4(),
            subject_type="commission",
            subject_id=commission.id,
            rule_triggered="instant_conversion",
            severity="high",
            resolved=False,
        )
    )
    db.flush()

    result = run_lifecycle_sweep(db)
    db.refresh(commission)
    assert commission.status == "pending"
    assert result["approved"] == 0


def test_sweep_approves_once_the_fraud_flag_is_resolved(db, commission_setup):
    commission = commission_setup["commission"]
    flag = FraudFlag(
        id=uuid.uuid4(),
        subject_type="commission",
        subject_id=commission.id,
        rule_triggered="instant_conversion",
        severity="high",
        resolved=True,
    )
    db.add(flag)
    db.flush()

    result = run_lifecycle_sweep(db)
    db.refresh(commission)
    assert commission.status == "approved"
    assert result["approved"] == 1


def test_sweep_holds_approved_until_hold_period_elapses(db, commission_setup):
    commission = commission_setup["commission"]
    campaign = commission_setup["campaign"]
    campaign.hold_period_days = 3
    transition(db, commission, "approved", reason="test")

    # approved just now — sweep should NOT move it to available yet
    result = run_lifecycle_sweep(db)
    db.refresh(commission)
    assert commission.status == "approved"
    assert result["available"] == 0

    # backdate the approval past the hold period and sweep again
    commission.status_history = [
        {"status": "approved", "at": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat(), "reason": "test"}
    ]
    db.flush()
    result = run_lifecycle_sweep(db)
    db.refresh(commission)
    assert commission.status == "available"
    assert result["available"] == 1
