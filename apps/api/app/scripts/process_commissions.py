"""Run the commission lifecycle's automatic transitions (pending -> approved,
approved -> available) against every eligible commission. There's no task
scheduler in this project yet, so this stands in for what would otherwise be
a periodic cron/worker job.

Run from apps/api with the venv active:
    python -m app.scripts.process_commissions
"""
from __future__ import annotations

from app.core.db import SessionLocal
from app.services.commission_lifecycle import run_lifecycle_sweep


def main() -> None:
    db = SessionLocal()
    try:
        result = run_lifecycle_sweep(db)
        print(f"Approved: {result['approved']}, moved to available: {result['available']}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
