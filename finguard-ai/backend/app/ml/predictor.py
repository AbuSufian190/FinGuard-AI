"""
Model inference service.

Loads the trained pipeline and metadata produced by the ML training job and
serves predictions, batch predictions and SHAP explanations. The SAME fitted
preprocessing pipeline from training is used here, so training and serving are
guaranteed consistent.

Designed to fail soft: if artifacts are missing (e.g. training has not run yet)
the service reports `loaded = False` instead of crashing the API, and the
health endpoint surfaces that state.
"""
from __future__ import annotations

import json
import logging
import os
import threading

import joblib
import pandas as pd

from .config import RAW_COLUMNS
from .features import engineer_features

logger = logging.getLogger("finguard.predictor")

ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "artifacts")


class Predictor:
    def __init__(self, artifact_dir: str = ARTIFACT_DIR,
                 medium_cutoff: float = 0.30, high_cutoff: float = 0.70):
        self.artifact_dir = artifact_dir
        self.medium_cutoff = medium_cutoff
        self.high_cutoff = high_cutoff
        self._lock = threading.Lock()
        self.pipeline = None
        self.explainer = None
        self.metadata: dict = {}
        self.model_card: dict = {}
        self.evaluation: dict = {}
        self.threshold = 0.5
        self.load()

    # ------------------------------------------------------------------ load
    def load(self) -> None:
        with self._lock:
            model_path = os.path.join(self.artifact_dir, "model.joblib")
            if not os.path.exists(model_path):
                logger.warning("No model artifact at %s; predictor disabled "
                               "until training runs.", model_path)
                self.pipeline = None
                return
            self.pipeline = joblib.load(model_path)
            self.metadata = self._read_json("feature_metadata.json")
            self.model_card = self._read_json("model_card.json")
            self.evaluation = self._read_json("evaluation_report.json")
            self.threshold = float(
                self.metadata.get("decision_threshold", 0.5))
            # Lazy, best-effort explainer.
            try:
                from .explain import FraudExplainer
                self.explainer = FraudExplainer(self.pipeline)
            except Exception as exc:  # pragma: no cover
                logger.warning("Explainer unavailable: %s", exc)
                self.explainer = None
            logger.info("Model loaded: %s %s (threshold=%.4f)",
                        self.model_card.get("model_name", "?"),
                        self.model_card.get("model_version", "?"),
                        self.threshold)

    def _read_json(self, name: str) -> dict:
        path = os.path.join(self.artifact_dir, name)
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return {}

    @property
    def loaded(self) -> bool:
        return self.pipeline is not None

    def _ensure(self) -> None:
        if not self.loaded:
            raise RuntimeError(
                "Model is not loaded. Run training first "
                "(`cd ml && python -m src.train`).")

    def _risk_level(self, prob: float) -> str:
        if prob >= self.high_cutoff:
            return "HIGH"
        if prob >= self.medium_cutoff:
            return "MEDIUM"
        return "LOW"

    # --------------------------------------------------------------- predict
    def predict_one(self, tx: dict) -> dict:
        self._ensure()
        raw = pd.DataFrame([{
            "step": tx.get("step", 0),
            "type": tx["type"],
            "amount": tx["amount"],
            "oldbalanceOrg": tx["oldbalanceOrg"],
            "newbalanceOrig": tx["newbalanceOrig"],
            "oldbalanceDest": tx["oldbalanceDest"],
            "newbalanceDest": tx["newbalanceDest"],
        }])
        X = engineer_features(raw)
        prob = float(self.pipeline.predict_proba(X)[:, 1][0])
        return {
            "fraud_probability": prob,
            "is_fraud": bool(prob >= self.threshold),
            "risk_level": self._risk_level(prob),
            "threshold": self.threshold,
            "model_name": self.model_card.get("model_name", "unknown"),
            "model_version": self.model_card.get("model_version", "unknown"),
        }

    def explain_one(self, tx: dict, top_k: int = 8) -> dict | None:
        self._ensure()
        if self.explainer is None:
            return None
        raw = pd.DataFrame([{k: tx.get(k, 0) for k in RAW_COLUMNS}])
        X = engineer_features(raw)
        return self.explainer.explain(X, top_k=top_k)

    # --------------------------------------------------------------- batch
    def predict_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        """Vectorised batch scoring. `df` must contain the raw PaySim columns.
        Returns the input with fraud_probability / is_fraud / risk_level added.
        """
        self._ensure()
        X = engineer_features(df)
        probs = self.pipeline.predict_proba(X)[:, 1]
        out = df.copy()
        out["fraud_probability"] = probs
        out["is_fraud"] = probs >= self.threshold
        out["risk_level"] = [self._risk_level(p) for p in probs]
        return out


_predictor: Predictor | None = None
_init_lock = threading.Lock()


def get_predictor() -> Predictor:
    global _predictor
    if _predictor is None:
        with _init_lock:
            if _predictor is None:
                from ..config import get_settings
                s = get_settings()
                _predictor = Predictor(medium_cutoff=s.risk_medium_cutoff,
                                       high_cutoff=s.risk_high_cutoff)
    return _predictor
