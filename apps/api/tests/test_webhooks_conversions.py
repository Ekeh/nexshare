"""POST /api/webhooks/conversions — idempotency, cap/budget enforcement,
and that a recorded conversion actually produces a fraud-flaggable
commission. Exercised through the real HTTP endpoint (TestClient), not the
handler function directly, since auth (the webhook secret) and request
validation are part of what's under test here too.

The `client` fixture's overridden get_db yields this same test's `db`
session, so fixtures built directly with the ORM here are visible to the
endpoint without any commit — it's one shared transaction, not two.
"""
import pytest
from sqlalchemy import select

from app.models.core import Commission, FraudFlag
from tests.factories import make_account, make_click, make_offer_campaign, make_tracking_link


@pytest.fixture()
def webhook_setup(db, unique_suffix):
    business = make_account(db, role="business", suffix=unique_suffix, webhook_secret=f"whsec_test_{unique_suffix}")
    promoter = make_account(db, role="promoter", suffix=unique_suffix)
    offer, campaign = make_offer_campaign(
        db, business=business, commission_model="fixed", commission_config={"amount_minor_units": 5000}
    )
    link = make_tracking_link(db, campaign=campaign, promoter=promoter, short_code=f"sc{unique_suffix}")
    return {"business": business, "promoter": promoter, "campaign": campaign, "link": link}


def _auth_headers(business):
    return {"Authorization": f"Bearer {business.webhook_secret}"}


def _post_conversion(client, business, **payload):
    return client.post("/api/webhooks/conversions", headers=_auth_headers(business), json=payload)


def test_unknown_click_id_is_404(client, webhook_setup):
    res = _post_conversion(client, webhook_setup["business"], click_id="does-not-exist")
    assert res.status_code == 404


def test_wrong_webhook_secret_is_401(client, webhook_setup):
    res = client.post(
        "/api/webhooks/conversions",
        headers={"Authorization": "Bearer whsec_not_the_real_one"},
        json={"click_id": "whatever"},
    )
    assert res.status_code == 401


def test_records_a_conversion_and_its_commission(db, client, webhook_setup):
    _, click_key, _ = make_click(db, tracking_link=webhook_setup["link"])

    res = _post_conversion(client, webhook_setup["business"], click_id=click_key, external_ref="order-1")
    assert res.status_code == 201
    body = res.json()
    assert body["commission_amount_minor_units"] == 5000
    assert body["duplicate"] is False

    commission = db.get(Commission, body["commission_id"])
    assert commission is not None
    assert commission.status == "pending"


def test_retrying_the_same_external_ref_is_idempotent(db, client, webhook_setup):
    _, click_key, _ = make_click(db, tracking_link=webhook_setup["link"])

    first = _post_conversion(client, webhook_setup["business"], click_id=click_key, external_ref="order-dup")
    second = _post_conversion(client, webhook_setup["business"], click_id=click_key, external_ref="order-dup")

    assert first.json()["duplicate"] is False
    assert second.json()["duplicate"] is True
    assert first.json()["conversion_id"] == second.json()["conversion_id"]

    commissions = db.scalars(select(Commission)).all()
    assert len(commissions) == 1, "a retried call must never create a second commission"


def test_max_conversions_cap_is_enforced_but_retries_still_pass(db, client, webhook_setup):
    webhook_setup["campaign"].max_conversions = 2

    clicks = [make_click(db, tracking_link=webhook_setup["link"]) for _ in range(3)]

    r1 = _post_conversion(client, webhook_setup["business"], click_id=clicks[0][1], external_ref="cap-1")
    r2 = _post_conversion(client, webhook_setup["business"], click_id=clicks[1][1], external_ref="cap-2")
    r3 = _post_conversion(client, webhook_setup["business"], click_id=clicks[2][1], external_ref="cap-3")

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r3.status_code == 409

    # a retry of an already-accepted one must still succeed even though the
    # campaign is now at its cap
    retry = _post_conversion(client, webhook_setup["business"], click_id=clicks[0][1], external_ref="cap-1")
    assert retry.status_code == 201
    assert retry.json()["duplicate"] is True


def test_budget_is_enforced_at_the_exact_boundary(db, client, webhook_setup):
    # fixed commission of 5000 minor units per conversion; budget for
    # exactly two
    webhook_setup["campaign"].budget_minor_units = 10000

    clicks = [make_click(db, tracking_link=webhook_setup["link"]) for _ in range(3)]

    r1 = _post_conversion(client, webhook_setup["business"], click_id=clicks[0][1], external_ref="bud-1")
    r2 = _post_conversion(client, webhook_setup["business"], click_id=clicks[1][1], external_ref="bud-2")
    r3 = _post_conversion(client, webhook_setup["business"], click_id=clicks[2][1], external_ref="bud-3")

    assert r1.status_code == 201
    assert r2.status_code == 201, "spend == budget must be allowed, not just spend < budget"
    assert r3.status_code == 409


def test_instant_conversion_records_a_fraud_flag_on_the_commission(db, client, webhook_setup):
    _, click_key, _ = make_click(db, tracking_link=webhook_setup["link"])

    res = _post_conversion(client, webhook_setup["business"], click_id=click_key, external_ref="fraud-1")
    assert res.status_code == 201
    commission_id = res.json()["commission_id"]

    flags = db.scalars(
        select(FraudFlag).where(FraudFlag.subject_type == "commission", FraudFlag.subject_id == commission_id)
    ).all()
    assert [f.rule_triggered for f in flags] == ["instant_conversion"], (
        "a click resolved and converted within the same request is always faster than the threshold"
    )
