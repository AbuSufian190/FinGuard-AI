"""Health check endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..ml.predictor import get_predictor
from ..schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
        database = "connected"
    except Exception:
        database = "unavailable"
    return HealthResponse(
        status="ok",
        model_loaded=get_predictor().loaded,
        database=database,
        version="1.0.0",
    )
