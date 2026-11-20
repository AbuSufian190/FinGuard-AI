"""
Leak-free preprocessing pipeline builder.

The returned ColumnTransformer is a *stateful* estimator and is fitted ONLY on
the training split inside train.py. One-hot encoding and scaling parameters are
therefore learned exclusively from training data. The same fitted object is
serialized and reused unchanged at inference time, guaranteeing identical
preprocessing in production.
"""
from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from .config import NUMERIC_FEATURES, CATEGORICAL_FEATURES
except ImportError:
    from config import NUMERIC_FEATURES, CATEGORICAL_FEATURES


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
            ("num", StandardScaler(), NUMERIC_FEATURES),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def make_pipeline(estimator) -> Pipeline:
    """Wrap preprocessing + estimator so raw engineered features flow through
    one object. Fitting this on train data fits the preprocessor on train only.
    """
    return Pipeline(steps=[("prep", build_preprocessor()), ("clf", estimator)])
