"""Rule-based fraud detection, run at conversion-recording time (see
app/api/routes/webhooks.py). No ML/external service — two deterministic
heuristics that write FraudFlag rows. The commission lifecycle's automatic
pending -> approved sweep already gates on unresolved flags (see
_has_unresolved_fraud_flags in commission_lifecycle.py) — this module is
what actually writes them; that gate was previously wired to a detector
that didn't exist. A business resolves a flag via
POST /api/business/fraud-flags/{id}/resolve once they've reviewed it (or
sidesteps it entirely by approving/rejecting the commission manually — a
deliberate human decision overrides an automatic heuristic).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.core import Commission, Conversion, FraudFlag


def evaluate_conversion(
    db: Session,
    *,
    commission: Commission,
    campaign_id: uuid.UUID,
    click_occurred_at: datetime,
) -> list[FraudFlag]:
    """Call after `commission` (and its conversion) have been added and
    flushed, so both are visible to the velocity query below within this
    transaction. Returns new, unsaved FraudFlag rows for the caller to add
    and commit — never raises and never blocks the conversion itself; a
    flag only affects the *automatic* approval step, not whether the sale
    is recorded."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    flags: list[FraudFlag] = []

    elapsed_seconds = (now - click_occurred_at).total_seconds()
    if elapsed_seconds < settings.fraud_min_click_to_conversion_seconds:
        flags.append(
            FraudFlag(
                id=uuid.uuid4(),
                subject_type="commission",
                subject_id=commission.id,
                rule_triggered="instant_conversion",
                severity="high",
            )
        )

    window_start = now - timedelta(minutes=settings.fraud_velocity_window_minutes)
    recent_count = db.scalar(
        select(func.count())
        .select_from(Commission)
        .join(Conversion, Conversion.id == Commission.conversion_id)
        .where(
            Commission.promoter_id == commission.promoter_id,
            Conversion.campaign_id == campaign_id,
            Conversion.occurred_at >= window_start,
        )
    )
    if recent_count > settings.fraud_velocity_max_conversions:
        flags.append(
            FraudFlag(
                id=uuid.uuid4(),
                subject_type="commission",
                subject_id=commission.id,
                rule_triggered="velocity_abuse",
                severity="medium",
            )
        )

    return flags
