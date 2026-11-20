"""Dashboard analytics + transactions listing."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud
from ..database import get_db
from ..schemas import DashboardSummary, HistoryItem

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard(db: Session = Depends(get_db)) -> DashboardSummary:
    summary = crud.dashboard_summary(db)
    recent = crud.recent_suspicious(db, limit=5)
    summary["recent_suspicious"] = [
        HistoryItem(
            id=r.id, created_at=r.created_at,
            type=r.transaction.type if r.transaction else "?",
            amount=r.transaction.amount if r.transaction else 0.0,
            fraud_probability=r.fraud_probability, is_fraud=r.is_fraud,
            risk_level=r.risk_level, source=r.source,
        ) for r in recent
    ]
    return DashboardSummary(**summary)
