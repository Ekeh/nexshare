from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.api.deps import require_promoter
from app.core.db import get_db
from app.models.core import Account, LedgerEntry

router = APIRouter()

WINDOW_DAYS = 7


class DailyPoint(BaseModel):
    date: str
    clicks: int
    conversions: int


class SourceBreakdown(BaseModel):
    channel: str
    count: int
    pct: float


class AnalyticsOut(BaseModel):
    total_clicks: int
    total_clicks_change_pct: float | None
    conversions: int
    conversions_change_pct: float | None
    conversion_rate: float
    conversion_rate_change_pct: float | None
    total_commission_minor_units: int
    currency: str
    total_commission_change_pct: float | None
    series: list[DailyPoint]
    top_sources: list[SourceBreakdown]


def _pct_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)


def _count_clicks(db: Session, promoter_id, since: datetime, until: datetime) -> int:
    return int(
        db.execute(
            text(
                """
                SELECT count(*) FROM clicks c
                JOIN tracking_links tl ON tl.id = c.tracking_link_id
                WHERE tl.promoter_id = :promoter_id
                  AND c.occurred_at >= :since AND c.occurred_at < :until
                """
            ),
            {"promoter_id": str(promoter_id), "since": since, "until": until},
        ).scalar()
        or 0
    )


def _count_conversions(db: Session, promoter_id, since: datetime, until: datetime) -> int:
    return int(
        db.execute(
            text(
                """
                SELECT count(*) FROM conversions cv
                JOIN clicks c ON c.id = cv.click_id
                JOIN tracking_links tl ON tl.id = c.tracking_link_id
                WHERE tl.promoter_id = :promoter_id
                  AND cv.occurred_at >= :since AND cv.occurred_at < :until
                """
            ),
            {"promoter_id": str(promoter_id), "since": since, "until": until},
        ).scalar()
        or 0
    )


@router.get("/me", response_model=AnalyticsOut)
def promoter_analytics(
    account: Account = Depends(require_promoter),
    db: Session = Depends(get_db),
) -> AnalyticsOut:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    window_start = today_start - timedelta(days=WINDOW_DAYS - 1)
    prior_window_start = window_start - timedelta(days=WINDOW_DAYS)

    total_clicks = _count_clicks(db, account.id, window_start, now)
    prior_clicks = _count_clicks(db, account.id, prior_window_start, window_start)
    conversions = _count_conversions(db, account.id, window_start, now)
    prior_conversions = _count_conversions(db, account.id, prior_window_start, window_start)

    conversion_rate = round(conversions / total_clicks * 100, 1) if total_clicks else 0.0
    prior_conversion_rate = round(prior_conversions / prior_clicks * 100, 1) if prior_clicks else 0.0

    currency = db.scalar(
        select(LedgerEntry.currency).where(LedgerEntry.account_id == account.id).limit(1)
    ) or "USD"

    def _commission_earned(since: datetime, until: datetime) -> int:
        return int(
            db.scalar(
                select(func.coalesce(func.sum(LedgerEntry.amount_minor_units), 0)).where(
                    LedgerEntry.account_id == account.id,
                    LedgerEntry.entry_type == "commission_earned",
                    LedgerEntry.created_at >= since,
                    LedgerEntry.created_at < until,
                )
            )
            or 0
        )

    total_commission = _commission_earned(window_start, now)
    prior_commission = _commission_earned(prior_window_start, window_start)

    # Daily series, zero-filled so the chart has a contiguous x-axis.
    click_rows = db.execute(
        text(
            """
            SELECT date_trunc('day', c.occurred_at) AS day, count(*) FROM clicks c
            JOIN tracking_links tl ON tl.id = c.tracking_link_id
            WHERE tl.promoter_id = :promoter_id AND c.occurred_at >= :since
            GROUP BY 1
            """
        ),
        {"promoter_id": str(account.id), "since": window_start},
    ).all()
    conversion_rows = db.execute(
        text(
            """
            SELECT date_trunc('day', cv.occurred_at) AS day, count(*) FROM conversions cv
            JOIN clicks c ON c.id = cv.click_id
            JOIN tracking_links tl ON tl.id = c.tracking_link_id
            WHERE tl.promoter_id = :promoter_id AND cv.occurred_at >= :since
            GROUP BY 1
            """
        ),
        {"promoter_id": str(account.id), "since": window_start},
    ).all()
    clicks_by_day = {row.day.date().isoformat(): row.count for row in click_rows}
    conversions_by_day = {row.day.date().isoformat(): row.count for row in conversion_rows}

    series = []
    for i in range(WINDOW_DAYS):
        day = (window_start + timedelta(days=i)).date().isoformat()
        series.append(DailyPoint(date=day, clicks=clicks_by_day.get(day, 0), conversions=conversions_by_day.get(day, 0)))

    # Top sources — which share channel clicks came through.
    source_rows = db.execute(
        text(
            """
            SELECT COALESCE(c.channel, 'other') AS channel, count(*) AS n FROM clicks c
            JOIN tracking_links tl ON tl.id = c.tracking_link_id
            WHERE tl.promoter_id = :promoter_id AND c.occurred_at >= :since
            GROUP BY 1 ORDER BY 2 DESC
            """
        ),
        {"promoter_id": str(account.id), "since": window_start},
    ).all()
    top_sources = [
        SourceBreakdown(channel=row.channel, count=row.n, pct=round(row.n / total_clicks * 100, 1))
        for row in source_rows
    ] if total_clicks else []

    return AnalyticsOut(
        total_clicks=total_clicks,
        total_clicks_change_pct=_pct_change(total_clicks, prior_clicks),
        conversions=conversions,
        conversions_change_pct=_pct_change(conversions, prior_conversions),
        conversion_rate=conversion_rate,
        conversion_rate_change_pct=_pct_change(conversion_rate, prior_conversion_rate),
        total_commission_minor_units=total_commission,
        currency=currency,
        total_commission_change_pct=_pct_change(total_commission, prior_commission),
        series=series,
        top_sources=top_sources,
    )
