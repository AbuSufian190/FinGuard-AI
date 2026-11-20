"""
Seed the database with demo predictions so the dashboard has data on first run.

Usage:  cd backend && python seed_demo.py [--rows 300]

Generates synthetic transactions, scores them with the loaded model, and stores
the predictions spread across the last two weeks. Safe to run multiple times.
"""
from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta, timezone

from app import crud
from app.database import SessionLocal, init_db
from app.ml.predictor import get_predictor


def _random_tx() -> dict:
    ttype = random.choices(
        ["PAYMENT", "CASH_OUT", "CASH_IN", "TRANSFER", "DEBIT"],
        weights=[34, 35, 22, 8, 1])[0]
    old_org = round(random.lognormvariate(9.0, 1.6), 2)
    amount = round(random.lognormvariate(8.2, 1.3), 2)
    fraud_like = ttype in ("TRANSFER", "CASH_OUT") and random.random() < 0.08
    if fraud_like:
        amount = old_org
        new_org = 0.0
        old_dest = 0.0
        new_dest = 0.0
    else:
        new_org = max(old_org - amount, 0.0)
        old_dest = round(random.lognormvariate(8.5, 1.8), 2)
        new_dest = old_dest + amount
    return {
        "step": random.randint(1, 743), "type": ttype, "amount": amount,
        "oldbalanceOrg": old_org, "newbalanceOrig": new_org,
        "oldbalanceDest": old_dest, "newbalanceDest": new_dest,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=300)
    args = ap.parse_args()

    init_db()
    predictor = get_predictor()
    if not predictor.loaded:
        raise SystemExit("Model not loaded; run `cd ml && python -m src.train` "
                         "first.")

    db = SessionLocal()
    now = datetime.now(timezone.utc)
    created = 0
    try:
        for _ in range(args.rows):
            tx = _random_tx()
            result = predictor.predict_one(tx)
            tx_row = crud.create_transaction(db, tx)
            pred = crud.create_prediction(db, transaction_id=tx_row.id,
                                          result=result, source="single")
            # backdate across the last 14 days for a nice trend
            offset = timedelta(days=random.randint(0, 13),
                               hours=random.randint(0, 23))
            pred.created_at = now - offset
            tx_row.created_at = pred.created_at
            created += 1
        db.commit()
    finally:
        db.close()
    print(f"Seeded {created} demo predictions.")


if __name__ == "__main__":
    main()
