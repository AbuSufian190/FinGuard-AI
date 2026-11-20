"""Model info, performance, and (background) training trigger."""
from __future__ import annotations

import logging
import os
import subprocess
import sys
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models as db_models
from ..database import get_db
from ..ml.predictor import get_predictor
from ..schemas import ModelInfo, TrainResponse

logger = logging.getLogger("finguard.models")
router = APIRouter(prefix="/models", tags=["models"])


@router.get("")
def list_models() -> dict:
    p = get_predictor()
    card = p.model_card
    return {
        "active_model": {
            "model_name": card.get("model_name"),
            "model_version": card.get("model_version"),
            "selection_metric": card.get("selection_metric"),
            "trained_at": card.get("trained_at"),
            "synthetic_data": card.get("synthetic_data"),
            "data_source": card.get("data_source"),
            "loaded": p.loaded,
        },
        "candidates": list(p.evaluation.get("models", {}).keys()),
    }


@router.get("/info", response_model=ModelInfo)
def model_info() -> ModelInfo:
    p = get_predictor()
    card = p.model_card
    return ModelInfo(
        model_name=card.get("model_name", "unknown"),
        model_version=card.get("model_version", "unknown"),
        selection_metric=card.get("selection_metric", "pr_auc"),
        decision_threshold=p.threshold,
        trained_at=card.get("trained_at"),
        data_source=card.get("data_source"),
        synthetic_data=card.get("synthetic_data"),
        features=p.metadata.get("model_features", []),
        loaded=p.loaded,
    )


@router.get("/performance")
def performance() -> dict:
    """Actual evaluation results from the last training run."""
    p = get_predictor()
    if not p.evaluation:
        raise HTTPException(404, "No evaluation report available. Train first.")
    return p.evaluation


def _run_training(run_id: int, data_path: str | None) -> None:
    """Executed in a background thread; shells out to the ML training module."""
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        run = db.get(db_models.TrainingRun, run_id)
        ml_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml"))
        if not os.path.isdir(ml_dir):
            run.status = "failed"
            run.message = "ml/ directory not available in this deployment."
            run.finished_at = datetime.now(timezone.utc)
            db.commit()
            return
        cmd = [sys.executable, "-m", "src.train"]
        if data_path:
            cmd += ["--data", data_path]
        proc = subprocess.run(cmd, cwd=ml_dir, capture_output=True,
                              text=True, timeout=3600)
        run.status = "completed" if proc.returncode == 0 else "failed"
        run.message = (proc.stdout[-500:] if proc.returncode == 0
                       else proc.stderr[-500:])
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        if proc.returncode == 0:
            get_predictor().load()  # hot-reload the new model
    except Exception as exc:  # pragma: no cover
        logger.exception("Training run failed")
        run = db.get(db_models.TrainingRun, run_id)
        if run:
            run.status = "failed"
            run.message = str(exc)[:500]
            run.finished_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


@router.post("/train", response_model=TrainResponse, status_code=202)
def train(background: BackgroundTasks, data_path: str | None = None,
          db: Session = Depends(get_db)) -> TrainResponse:
    """Kick off model (re)training as a background task. Training is expensive,
    so it never blocks the request; poll /api/models/info for the new version."""
    run = db_models.TrainingRun(status="running", synthetic=data_path is None,
                                data_source=data_path or "synthetic")
    db.add(run)
    db.commit()
    db.refresh(run)
    background.add_task(_run_training, run.id, data_path)
    return TrainResponse(training_run_id=run.id, status="running",
                         message="Training started in the background.")
