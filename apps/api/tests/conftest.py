"""Test setup. Order matters: the env vars below MUST be set before any
`app.*` module is imported anywhere (including by other fixtures in this
file) — app/core/config.py's Settings is built once and cached
(@lru_cache), and both app/core/db.py and app/core/redis.py build their
engine/client from it at import time. Nothing above these lines may import
from `app`.

Tests run against a disposable `nexshare_test` Postgres database (dropped
and recreated fresh each session, migrated with the real Alembic chain —
never against the schema created ad hoc, so migrations are exercised too)
and Redis logical db 15 — never the dev database/`nexshare-redis` db 0 a
developer might have real data in. PAYSTACK_SECRET_KEY is force-unset so no
test can accidentally reach the real Paystack API even if a developer's own
.env has a real key configured; tests that need Paystack-configured
behavior monkeypatch it explicitly and stub PaystackClient.
"""
import os

TEST_DATABASE_URL = "postgresql+psycopg://nexshare:nexshare@localhost:5432/nexshare_test"
_ADMIN_DATABASE_URL = "postgresql://nexshare:nexshare@localhost:5432/postgres"
TEST_REDIS_URL = "redis://localhost:6379/15"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["REDIS_URL"] = TEST_REDIS_URL
os.environ["PAYSTACK_SECRET_KEY"] = ""
os.environ["RESEND_API_KEY"] = ""
os.environ["TERMII_API_KEY"] = ""
os.environ["ENVIRONMENT"] = "test"

import subprocess  # noqa: E402
import sys  # noqa: E402
import uuid  # noqa: E402
from pathlib import Path  # noqa: E402

import psycopg  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

API_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    """Drop-and-recreate rather than reuse: guarantees the schema always
    matches the current migration chain, and that a test run never starts
    from a state some earlier crashed run left behind."""
    with psycopg.connect(_ADMIN_DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = 'nexshare_test' AND pid <> pg_backend_pid()"
            )
            cur.execute("DROP DATABASE IF EXISTS nexshare_test")
            cur.execute("CREATE DATABASE nexshare_test")

    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=API_ROOT,
        env={**os.environ, "DATABASE_URL": TEST_DATABASE_URL},
        check=True,
        capture_output=True,
    )


@pytest.fixture(scope="session")
def engine(_test_database):
    eng = create_engine(TEST_DATABASE_URL)
    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    """One test, one connection, one outer transaction that's always rolled
    back — even a `db.commit()` inside application code only commits a
    SAVEPOINT nested within it (SQLAlchemy 2.0's documented "join a session
    to an external transaction" recipe for test suites —
    `join_transaction_mode="create_savepoint"` is what actually makes a
    plain `session.commit()`/`rollback()` operate on the SAVEPOINT instead
    of the outer connection-level transaction; without it, a commit ends
    the whole thing early and a rollback wipes out earlier committed
    fixture data too — confirmed the hard way), so nothing a test does
    ever survives it, however deep the call stack commits."""
    connection = engine.connect()
    outer_tx = connection.begin()
    Session = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")
    session = Session()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, transaction):
        if transaction.nested and not transaction._parent.nested:
            sess.begin_nested()

    yield session

    session.close()
    outer_tx.rollback()
    connection.close()


@pytest.fixture()
def redis_client():
    from app.core.redis import get_redis

    client = get_redis()
    client.flushdb()
    yield client
    client.flushdb()


@pytest.fixture()
def client(db):
    """A TestClient wired to the same transactional `db` session as the
    test itself, so a test can set up fixtures with the ORM, call the API,
    and read the result back through one consistent view of the data."""
    from app.core.db import get_db
    from app.main import app

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def unique_suffix():
    """Short unique string for building non-colliding emails/phones/short_codes
    within a test — the DB is rolled back between tests, but factories still
    need values unique *within* a single test's own inserts."""
    return uuid.uuid4().hex[:10]
