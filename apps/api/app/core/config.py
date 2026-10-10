from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://nexshare:nexshare@localhost:5432/nexshare"
    redis_url: str = "redis://localhost:6379/0"
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]
    # Public origin of the web app. Tracking-link share URLs are built as
    # f"{public_base_url}/api/clicks/{short_code}" — Next.js's rewrite
    # (next.config.js) proxies that path to the API, so the shared link
    # stays on the branded domain instead of pointing at the API host.
    public_base_url: str = "http://localhost:3000"
    # Must be >= 32 bytes for HS256 (RFC 7518 §3.2) — override via env var in
    # any real environment; this default is dev-only.
    jwt_secret: str = "dev-only-secret-change-me-please-32bytes-min"
    jwt_algorithm: str = "HS256"
    access_token_cookie_name: str = "access_token"
    access_token_expire_seconds: int = 60 * 60 * 24 * 14  # 14 days

    # Email/phone verification. Delivery is provider-agnostic (see
    # app/services/notifications) — set the relevant API key to send for
    # real; leave it unset and the app logs the code to the console instead
    # of failing, so registration still works without either account.
    resend_api_key: str | None = None
    resend_from_email: str = "NexShare <onboarding@resend.dev>"
    termii_api_key: str | None = None
    termii_sender_id: str = "N-Alert"
    verification_code_ttl_minutes: int = 10
    verification_max_attempts: int = 5
    verification_resend_cooldown_seconds: int = 60
    # How long a post-registration/pending-login token is valid to finish
    # verification with, before the holder has to re-prove their password.
    pending_verification_token_ttl_minutes: int = 30

    # Rule-based fraud detection (app/services/fraud.py) — no ML/external
    # service, just two deterministic thresholds run at conversion-recording
    # time. A real checkout can't complete in under a few seconds, so a
    # conversion reported faster than this is almost certainly a fabricated
    # or replayed webhook call rather than an actual customer visit.
    fraud_min_click_to_conversion_seconds: int = 3
    # More than this many conversions from the same promoter on the same
    # campaign within the window below looks like self-dealing/farming
    # rather than organic sales.
    fraud_velocity_window_minutes: int = 10
    fraud_velocity_max_conversions: int = 3

    # Paystack (https://paystack.com) — the real payment rail for promoter
    # payouts (app/services/paystack.py). Unset in dev: withdrawing still
    # creates a Payout row but it stays "requested" with no way to become
    # "completed", same as before this was wired up. Use a test secret key
    # (sk_test_...) to exercise the whole flow against Paystack's sandbox
    # without moving real money.
    paystack_secret_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
