import secrets
import uuid
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.core import Campaign, Offer, TrackingLink

router = APIRouter()


def _with_click_id(url: str, click_id: str) -> str:
    """Appends ?nx_click=<click_id> (preserving any existing query string) —
    this, not the cookie below, is what actually lets a business's checkout
    recover the click_id: destination_url is on their domain, so a cookie
    set here (nexshare's origin) is invisible to it. Their integration
    reads this param and echoes click_id back in the conversion webhook."""
    parts = urlsplit(url)
    query = parse_qsl(parts.query, keep_blank_values=True)
    query.append(("nx_click", click_id))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


@router.get("/{short_code}")
def record_click(short_code: str, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    # Intentionally unauthenticated: hit by anonymous customers following a
    # promoter's shared link, not by a logged-in account.
    row = db.execute(
        select(TrackingLink, Offer)
        .join(Campaign, Campaign.id == TrackingLink.campaign_id)
        .join(Offer, Offer.id == Campaign.offer_id)
        .where(TrackingLink.short_code == short_code)
    ).first()

    if row is None:
        # Unknown/expired link — send them somewhere real rather than a bare 404.
        return RedirectResponse(url="/")

    link, offer = row
    click_id = secrets.token_hex(16)
    channel = request.query_params.get("ch")
    # No Click ORM model: `clicks` is a partitioned table with a composite
    # (id, occurred_at) primary key (see alembic/versions/0001), which
    # SQLAlchemy's ORM doesn't map cleanly — raw insert, same as seed_demo.py.
    db.execute(
        text(
            "INSERT INTO clicks (id, tracking_link_id, click_id, channel) "
            "VALUES (:id, :tracking_link_id, :click_id, :channel)"
        ),
        {"id": str(uuid.uuid4()), "tracking_link_id": str(link.id), "click_id": click_id, "channel": channel},
    )
    db.commit()

    destination = _with_click_id(offer.destination_url, click_id) if offer.destination_url else "/"
    response = RedirectResponse(url=destination)
    # Best-effort same-origin fallback (e.g. a destination that's a
    # subdomain of ours); the query param above is the real mechanism.
    response.set_cookie("nx_click_id", click_id, max_age=60 * 60 * 24 * 30)
    return response
