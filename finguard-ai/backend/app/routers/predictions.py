"""Prediction endpoints: single, batch, history, explanation."""
from __future__ import annotations

import base64
import io
import logging

import pandas as pd
from fastapi import (APIRouter, Depends, File, HTTPException, Query,
                     UploadFile, status)
from sqlalchemy.orm import Session

from .. import crud
from ..config import get_settings
from ..database import get_db
from ..ml.config import RAW_COLUMNS, TRANSACTION_TYPES
from ..ml.predictor import get_predictor
from ..schemas import (BatchPredictionResponse, BatchRowResult, BatchSummary,
                       Explanation, HistoryItem, Page, PredictionResponse,
                       TransactionInput)

logger = logging.getLogger("finguard.predictions")
router = APIRouter(prefix="/predictions", tags=["predictions"])
settings = get_settings()


def _require_model() -> None:
    if not get_predictor().loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded. Run training first.")


@router.post("", response_model=PredictionResponse,
             status_code=status.HTTP_201_CREATED)
def create_prediction(payload: TransactionInput,
                      explain: bool = Query(True),
                      db: Session = Depends(get_db)) -> PredictionResponse:
    _require_model()
    predictor = get_predictor()
    tx = payload.model_dump()
    result = predictor.predict_one(tx)
    explanation = predictor.explain_one(tx) if explain else None

    tx_row = crud.create_transaction(db, tx)
    pred = crud.create_prediction(db, transaction_id=tx_row.id, result=result,
                                  source="single", explanation=explanation)
    db.commit()

    return PredictionResponse(
        id=pred.id, created_at=pred.created_at, transaction=payload,
        explanation=Explanation(**explanation) if explanation else None,
        **result,
    )


@router.post("/batch", response_model=BatchPredictionResponse)
async def batch_predict(file: UploadFile = File(...),
                        db: Session = Depends(get_db)
                        ) -> BatchPredictionResponse:
    _require_model()

    # --- file validation ---------------------------------------------------
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Only .csv files are accepted.")
    raw = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(raw) > max_bytes:
        raise HTTPException(
            413, f"File exceeds {settings.max_upload_mb} MB limit.")
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:
        raise HTTPException(400, f"Could not parse CSV: {exc}") from exc

    missing = [c for c in RAW_COLUMNS if c not in df.columns]
    if missing:
        raise HTTPException(
            422, f"CSV missing required columns: {', '.join(missing)}. "
                 f"Expected: {', '.join(RAW_COLUMNS)}")
    if len(df) == 0:
        raise HTTPException(422, "CSV contains no rows.")
    if len(df) > settings.max_batch_rows:
        raise HTTPException(
            413, f"Too many rows ({len(df)}); max {settings.max_batch_rows}.")

    bad_types = set(df["type"].astype(str).unique()) - set(TRANSACTION_TYPES)
    if bad_types:
        raise HTTPException(
            422, f"Unknown transaction type(s): {', '.join(sorted(bad_types))}")

    # --- scoring ------------------------------------------------------------
    scored = get_predictor().predict_frame(df)

    results = [
        BatchRowResult(row=int(i),
                       fraud_probability=float(r.fraud_probability),
                       is_fraud=bool(r.is_fraud),
                       risk_level=str(r.risk_level))
        for i, r in scored.reset_index(drop=True).iterrows()
    ]
    flagged = int(scored["is_fraud"].sum())
    high = int((scored["risk_level"] == "HIGH").sum())
    summary = BatchSummary(
        total_rows=len(scored), flagged_fraud=flagged,
        fraud_rate=flagged / len(scored), high_risk=high)

    # downloadable annotated CSV
    buf = io.StringIO()
    scored.to_csv(buf, index=False)
    csv_b64 = base64.b64encode(buf.getvalue().encode()).decode()

    # persist an aggregate record per row (capped persistence for large files)
    persist = scored.head(1000)
    for _, r in persist.iterrows():
        tx = {c: r[c] for c in RAW_COLUMNS}
        res = {
            "fraud_probability": float(r.fraud_probability),
            "is_fraud": bool(r.is_fraud),
            "risk_level": str(r.risk_level),
            "threshold": get_predictor().threshold,
            "model_name": get_predictor().model_card.get("model_name",
                                                         "unknown"),
            "model_version": get_predictor().model_card.get("model_version",
                                                           "unknown"),
        }
        tx_row = crud.create_transaction(db, tx)
        crud.create_prediction(db, transaction_id=tx_row.id, result=res,
                               source="batch")
    db.commit()

    return BatchPredictionResponse(summary=summary, results=results,
                                   result_csv_base64=csv_b64)


@router.get("/history", response_model=Page[HistoryItem])
def history(page: int = Query(1, ge=1),
            page_size: int = Query(20, ge=1, le=100),
            risk_level: str | None = Query(None),
            is_fraud: bool | None = Query(None),
            type: str | None = Query(None),
            search: str | None = Query(None),
            db: Session = Depends(get_db)) -> Page[HistoryItem]:
    rows, total = crud.list_predictions(
        db, page=page, page_size=page_size, risk_level=risk_level,
        is_fraud=is_fraud, tx_type=type, search=search)
    items = [
        HistoryItem(
            id=r.id, created_at=r.created_at,
            type=r.transaction.type if r.transaction else "?",
            amount=r.transaction.amount if r.transaction else 0.0,
            fraud_probability=r.fraud_probability, is_fraud=r.is_fraud,
            risk_level=r.risk_level, source=r.source,
        ) for r in rows
    ]
    pages = (total + page_size - 1) // page_size
    return Page[HistoryItem](items=items, total=total, page=page,
                             page_size=page_size, pages=pages)


@router.get("/{pred_id}/explanation", response_model=Explanation)
def explanation(pred_id: int, db: Session = Depends(get_db)) -> Explanation:
    pred = crud.get_prediction(db, pred_id)
    if pred is None:
        raise HTTPException(404, "Prediction not found.")
    if pred.explanation:
        return Explanation(**pred.explanation)
    # recompute on demand from the stored transaction
    _require_model()
    if not pred.transaction:
        raise HTTPException(404, "No transaction attached to this prediction.")
    tx = {
        "step": pred.transaction.step, "type": pred.transaction.type,
        "amount": pred.transaction.amount,
        "oldbalanceOrg": pred.transaction.old_balance_orig,
        "newbalanceOrig": pred.transaction.new_balance_orig,
        "oldbalanceDest": pred.transaction.old_balance_dest,
        "newbalanceDest": pred.transaction.new_balance_dest,
    }
    exp = get_predictor().explain_one(tx)
    if exp is None:
        raise HTTPException(503, "Explainer unavailable.")
    pred.explanation = exp
    db.commit()
    return Explanation(**exp)
