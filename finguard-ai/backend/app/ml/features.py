"""
Feature engineering for FinGuard AI.

`engineer_features` is a PURE, row-wise, stateless transformation (no fitting,
no data-dependent parameters) applied identically at training time and at
inference time. Because it does not learn anything from the data, running it
before or after the train/test split cannot leak information.

All stateful preprocessing (scaling, one-hot encoding) lives in the fitted
scikit-learn Pipeline (see preprocessing.py) which is fitted ONLY on the
training split. This module is duplicated verbatim in the backend
(`backend/app/ml/features.py`) so that serving uses identical logic.
"""
from __future__ import annotations

import pandas as pd

try:  # allow both `python -m src.train` and direct imports
    from .config import NUMERIC_FEATURES, CATEGORICAL_FEATURES
except ImportError:  # pragma: no cover
    from config import NUMERIC_FEATURES, CATEGORICAL_FEATURES

MODEL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build the model feature matrix from raw transaction rows.

    Expects the raw PaySim columns: step, type, amount, oldbalanceOrg,
    newbalanceOrig, oldbalanceDest, newbalanceDest. Returns a DataFrame with
    exactly the columns in MODEL_FEATURES, in order.
    """
    out = pd.DataFrame(index=df.index)

    out["type"] = df["type"].astype(str)
    out["step"] = df["step"].astype(float)
    out["hour"] = (df["step"].astype(float) % 24.0)
    out["amount"] = df["amount"].astype(float)
    out["oldbalanceOrg"] = df["oldbalanceOrg"].astype(float)
    out["newbalanceOrig"] = df["newbalanceOrig"].astype(float)
    out["oldbalanceDest"] = df["oldbalanceDest"].astype(float)
    out["newbalanceDest"] = df["newbalanceDest"].astype(float)

    # Balance-consistency errors. Genuine transactions keep the accounting
    # identity (balance_after = balance_before - amount). Fraudulent ones,
    # which drain accounts programmatically, frequently violate it. These are
    # the strongest signals in PaySim-style data.
    out["errorBalanceOrig"] = (
        out["newbalanceOrig"] + out["amount"] - out["oldbalanceOrg"]
    )
    out["errorBalanceDest"] = (
        out["oldbalanceDest"] + out["amount"] - out["newbalanceDest"]
    )

    out["amount_to_oldOrg"] = out["amount"] / (out["oldbalanceOrg"] + 1.0)
    out["orig_emptied"] = (
        (out["oldbalanceOrg"] > 0) & (out["newbalanceOrig"] <= 1e-6)
    ).astype(float)
    out["dest_zero_before"] = (out["oldbalanceDest"] <= 1e-6).astype(float)

    return out[MODEL_FEATURES]
