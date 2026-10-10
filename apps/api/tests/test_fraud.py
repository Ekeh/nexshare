"""app/services/fraud.py — the two deterministic heuristics. Each is
tested in isolation (the other held clearly not-triggering) and at its
exact boundary, since off-by-one on a threshold is the most likely bug.
"""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.services.fraud import evaluate_conversion
from tests.factories import make_account, make_click, make_commission, make_conversion, make_offer_campaign, make_tracking_link

settings = get_settings()


@pytest.fixture()
def campaign_setup(db, unique_suffix):
    business = make_account(db, role="business", suffix=unique_suffix)
    promoter = make_account(db, role="promoter", suffix=unique_suffix)
    offer, campaign = make_offer_campaign(db, business=business)
    link = make_tracking_link(db, campaign=campaign, promoter=promoter, short_code=f"sc{unique_suffix}")
    return {"promoter": promoter, "campaign": campaign, "link": link}


def _make_commission_from_click(db, campaign_setup, *, click_occurred_at):
    click_row_id, _, click_at = make_click(db, tracking_link=campaign_setup["link"], occurred_at=click_occurred_at)
    conversion = make_conversion(db, campaign=campaign_setup["campaign"], click_row_id=click_row_id, click_occurred_at=click_at)
    commission = make_commission(db, conversion=conversion, promoter=campaign_setup["promoter"])
    return commission


def test_normal_timing_and_low_velocity_triggers_no_flags(db, campaign_setup):
    old_click = datetime.now(timezone.utc) - timedelta(seconds=settings.fraud_min_click_to_conversion_seconds + 5)
    commission = _make_commission_from_click(db, campaign_setup, click_occurred_at=old_click)

    flags = evaluate_conversion(
        db, commission=commission, campaign_id=campaign_setup["campaign"].id, click_occurred_at=old_click
    )
    assert flags == []


def test_instant_conversion_flags_when_faster_than_threshold(db, campaign_setup):
    just_now = datetime.now(timezone.utc)
    commission = _make_commission_from_click(db, campaign_setup, click_occurred_at=just_now)

    flags = evaluate_conversion(
        db, commission=commission, campaign_id=campaign_setup["campaign"].id, click_occurred_at=just_now
    )
    assert [f.rule_triggered for f in flags] == ["instant_conversion"]
    assert flags[0].severity == "high"
    assert flags[0].subject_type == "commission"
    assert flags[0].subject_id == commission.id


def test_instant_conversion_does_not_flag_right_at_the_threshold(db, campaign_setup):
    # elapsed_seconds < threshold triggers it — exactly at the threshold
    # (or slightly past it) must not.
    at_threshold = datetime.now(timezone.utc) - timedelta(seconds=settings.fraud_min_click_to_conversion_seconds + 1)
    commission = _make_commission_from_click(db, campaign_setup, click_occurred_at=at_threshold)

    flags = evaluate_conversion(
        db, commission=commission, campaign_id=campaign_setup["campaign"].id, click_occurred_at=at_threshold
    )
    assert "instant_conversion" not in [f.rule_triggered for f in flags]


def test_velocity_abuse_flags_once_past_the_max(db, campaign_setup):
    old_click = timedelta(seconds=settings.fraud_min_click_to_conversion_seconds + 5)
    now = datetime.now(timezone.utc)

    # fraud_velocity_max_conversions prior conversions in the window, none
    # of them flagged (each individually under the max)
    for _ in range(settings.fraud_velocity_max_conversions):
        c = _make_commission_from_click(db, campaign_setup, click_occurred_at=now - old_click)
        flags = evaluate_conversion(db, commission=c, campaign_id=campaign_setup["campaign"].id, click_occurred_at=now - old_click)
        assert "velocity_abuse" not in [f.rule_triggered for f in flags]

    # the next one pushes the count past the max — this one should flag
    over_the_max = _make_commission_from_click(db, campaign_setup, click_occurred_at=now - old_click)
    flags = evaluate_conversion(
        db, commission=over_the_max, campaign_id=campaign_setup["campaign"].id, click_occurred_at=now - old_click
    )
    assert "velocity_abuse" in [f.rule_triggered for f in flags]


def test_velocity_abuse_ignores_conversions_outside_the_window(db, campaign_setup):
    now = datetime.now(timezone.utc)
    old_click = timedelta(seconds=settings.fraud_min_click_to_conversion_seconds + 5)
    outside_window = now - timedelta(minutes=settings.fraud_velocity_window_minutes + 1)

    # well over the max, but all outside the velocity window
    for _ in range(settings.fraud_velocity_max_conversions + 3):
        _make_commission_from_click(db, campaign_setup, click_occurred_at=outside_window)

    # Conversion.occurred_at is a server_default (real insert time), so
    # backdate it directly — that's the column evaluate_conversion's
    # velocity query actually filters on.
    db.execute(
        text("UPDATE conversions SET occurred_at = :t WHERE campaign_id = :cid"),
        {"t": outside_window, "cid": str(campaign_setup["campaign"].id)},
    )

    fresh = _make_commission_from_click(db, campaign_setup, click_occurred_at=now - old_click)
    flags = evaluate_conversion(db, commission=fresh, campaign_id=campaign_setup["campaign"].id, click_occurred_at=now - old_click)
    assert "velocity_abuse" not in [f.rule_triggered for f in flags]
