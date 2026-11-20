"""Transactions listing endpoint (paginated)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Transaction
from ..schemas import Page

router = APIRouter(tags=["transactions"])


@router.get("/transactions")
def list_transactions(page: int = Query(1, ge=1),
                      page_size: int = Query(20, ge=1, le=100),
                      type: str | None = Query(None),
                      db: Session = Depends(get_db)) -> dict:
    stmt = select(Transaction)
    count_stmt = select(func.count(Transaction.id))
    if type:
        stmt = stmt.where(Transaction.type == type)
        count_stmt = count_stmt.where(Transaction.type == type)
    total = db.execute(count_stmt).scalar_one()
    rows = db.execute(
        stmt.order_by(Transaction.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    items = [
        {
            "id": r.id, "step": r.step, "type": r.type, "amount": r.amount,
            "oldbalanceOrg": r.old_balance_orig,
            "newbalanceOrig": r.new_balance_orig,
            "oldbalanceDest": r.old_balance_dest,
            "newbalanceDest": r.new_balance_dest,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        } for r in rows
    ]
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page,
            "page_size": page_size, "pages": pages}
