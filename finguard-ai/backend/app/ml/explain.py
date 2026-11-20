"""
SHAP-based explanations for individual predictions.

The explainer operates on the TRANSFORMED feature space (after the fitted
preprocessor) so SHAP values align with the model's actual inputs. It is used
both offline and by the backend prediction-explanation endpoint.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd


class FraudExplainer:
    """Wraps a fitted (prep + tree-model) sklearn Pipeline with a SHAP
    TreeExplainer. Falls back to model feature_importances_ if SHAP is
    unavailable or the model is not tree-based."""

    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.prep = pipeline.named_steps["prep"]
        self.model = pipeline.named_steps["clf"]
        self.feature_names = list(self.prep.get_feature_names_out())
        self._explainer = None
        try:
            import shap  # noqa
            self._explainer = shap.TreeExplainer(self.model)
            self._mode = "shap"
        except Exception:  # pragma: no cover - non-tree or shap missing
            self._mode = "importance"

    def explain(self, raw_features: pd.DataFrame, top_k: int = 8) -> Dict:
        """Return top contributing features for a single-row engineered frame."""
        X = self.prep.transform(raw_features)
        if self._mode == "shap":
            values = self._explainer.shap_values(X)
            if isinstance(values, list):  # some versions return per-class list
                values = values[1] if len(values) > 1 else values[0]
            values = np.asarray(values)
            row = values[0] if values.ndim == 2 else values
            contributions = row
        else:
            imp = getattr(self.model, "feature_importances_",
                          np.ones(len(self.feature_names)))
            contributions = imp * X[0]

        pairs = list(zip(self.feature_names, np.asarray(contributions).ravel(),
                         np.asarray(X[0]).ravel()))
        pairs.sort(key=lambda p: abs(p[1]), reverse=True)
        top = pairs[:top_k]

        return {
            "method": self._mode,
            "top_features": [
                {
                    "feature": name,
                    "contribution": float(contrib),
                    "value": float(val),
                    "direction": "increases_risk" if contrib > 0
                    else "decreases_risk",
                }
                for name, contrib, val in top
            ],
        }
