from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import (
    analytics,
    auth,
    business,
    offers,
    promoters,
    tracking_links,
    clicks,
    commissions,
    storefront,
    webhooks,
)
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="NexShare API",
    description="Performance-commerce network — offers, tracking links, clicks, commissions.",
    version="0.1.0",
)

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(promoters.router, prefix="/api/promoters", tags=["promoters"])
app.include_router(offers.router, prefix="/api/offers", tags=["offers"])
app.include_router(
    tracking_links.router, prefix="/api/tracking-links", tags=["tracking-links"]
)
app.include_router(clicks.router, prefix="/api/clicks", tags=["clicks"])
app.include_router(
    commissions.router, prefix="/api/commissions", tags=["commissions"]
)
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(business.router, prefix="/api/business", tags=["business"])
app.include_router(storefront.router, prefix="/api/storefront", tags=["storefront"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
