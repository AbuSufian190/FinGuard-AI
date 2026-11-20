"""Database access helpers (parameterised via the ORM — no raw SQL)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from . import models


def create_transaction(db: Session, tx: dict) -> models.Transaction:
    row = models.Transaction(
        step=tx.get("step", 0),
        type=tx["type"],
        amount=tx["amount"],
        old_balance_orig=tx["oldbalanceOrg"],
        new_balance_orig=tx["newbalanceOrig"],
        old_balance_dest=tx["oldbalanceDest"],
        new_balance_dest=tx["newbalanceDest"],
    )
    db.add(row)
    db.flush()
    return row


def create_prediction(db: Session, *, transaction_id: int | None,
                      result: dict, source: str = "single",
                      explanation: dict | None = None) -> models.Prediction:
    row = models.Prediction(
        transaction_id=transaction_id,
        fraud_probability=result["fraud_probability"],
        is_fraud=result["is_fraud"],
        risk_level=result["risk_level"],
        threshold=result["threshold"],
        model_name=result["model_name"],
        model_version=result["model_version"],
        source=source,
        explanation=explanation,
    )
    db.add(row)
    db.flush()
    return row


def get_prediction(db: Session, pred_id: int) -> models.Prediction | None:
    return db.get(models.Prediction, pred_id)


def list_predictions(db: Session, *, page: int, page_size: int,
                     risk_level: str | None = None,
                     is_fraud: bool | None = None,
                     tx_type: str | None = None,
                     search: str | None = None):
    stmt = select(models.Prediction).join(
        models.Transaction,
        models.Prediction.transaction_id == models.Transaction.id,
        isouter=True,
    )
    count_stmt = select(func.count(models.Prediction.id)).join(
        models.Transaction,
        models.Prediction.transaction_id == models.Transaction.id,
        isouter=True,
    )

    filters = []
    if risk_level:
        filters.append(models.Prediction.risk_level == risk_level)
    if is_fraud is not None:
        filters.append(models.Prediction.is_fraud == is_fraud)
    if tx_type:
        filters.append(models.Transaction.type == tx_type)
    if search:
        # numeric search against id or amount
        try:
            val = float(search)
            filters.append(
                (models.Prediction.id == int(val))
                | (models.Transaction.amount == val)
            )
        except ValueError:
            pass

    for f in filters:
        stmt = stmt.where(f)
        count_stmt = count_stmt.where(f)

    total = db.execute(count_stmt).scalar_one()
    stmt = (stmt.order_by(models.Prediction.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size))
    rows = db.execute(stmt).scalars().all()
    return rows, total


def dashboard_summary(db: Session, days: int = 14) -> dict:
    total = db.execute(
        select(func.count(models.Prediction.id))).scalar_one()
    fraud = db.execute(
        select(func.count(models.Prediction.id))
        .where(models.Prediction.is_fraud.is_(True))).scalar_one()
    avg_amount = db.execute(
        select(func.avg(models.Transaction.amount))).scalar() or 0.0

    # Daily trend over the recent window.
    since = datetime.now(timezone.utc) - timedelta(days=days)
    trend_rows = db.execute(
        select(
            func.date(models.Prediction.created_at).label("day"),
            func.count(models.Prediction.id),
            func.sum(case((models.Prediction.is_fraud.is_(True), 1),
                          else_=0)),
        )
        .where(models.Prediction.created_at >= since)
        .group_by("day").order_by("day")
    ).all()
    trend = [{"date": str(r[0]), "total": int(r[1]),
              "fraud": int(r[2] or 0)} for r in trend_rows]

    dist_rows = db.execute(
        select(models.Prediction.risk_level, func.count(models.Prediction.id))
        .group_by(models.Prediction.risk_level)
    ).all()
    fraud_distribution = [{"risk_level": r[0], "count": int(r[1])}
                          for r in dist_rows]

    return {
        "total_transactions": int(total),
        "fraudulent_detected": int(fraud),
        "fraud_detection_rate": (fraud / total) if total else 0.0,
        "average_amount": float(avg_amount),
        "trend": trend,
        "fraud_distribution": fraud_distribution,
    }


def recent_suspicious(db: Session, limit: int = 5):
    stmt = (select(models.Prediction)
            .where(models.Prediction.is_fraud.is_(True))
            .order_by(models.Prediction.created_at.desc()).limit(limit))
    return db.execute(stmt).scalars().all()
