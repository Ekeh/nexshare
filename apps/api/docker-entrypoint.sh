#!/bin/sh
# Runs migrations against whatever DATABASE_URL points at, then starts the
# API. Migrations are safe to run on every container start — alembic only
# applies revisions that haven't been applied yet (see `alembic_version`).
set -e

alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
