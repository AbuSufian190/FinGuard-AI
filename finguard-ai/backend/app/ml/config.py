"""
Canonical dataset + feature schema for FinGuard AI.

This module is the single source of truth for the transaction schema and the
engineered feature set. It is intentionally dependency-light (stdlib only) so it
can be imported by the ML training code and by the FastAPI backend without
pulling heavy packages. A copy is shipped inside the backend at
`backend/app/ml/feature_schema.py` and MUST be kept identical.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Raw transaction schema (mirrors the public PaySim dataset)
# ---------------------------------------------------------------------------
TRANSACTION_TYPES = ["PAYMENT", "TRANSFER", "CASH_OUT", "CASH_IN", "DEBIT"]

# In the real PaySim data, fraud is only ever labelled on TRANSFER / CASH_OUT.
FRAUD_ELIGIBLE_TYPES = ["TRANSFER", "CASH_OUT"]

RAW_COLUMNS = [
    "step",            # 1 unit = 1 hour of simulation
    "type",            # transaction type (categorical)
    "amount",          # transaction amount
    "oldbalanceOrg",   # sender balance before
    "newbalanceOrig",  # sender balance after
    "oldbalanceDest",  # recipient balance before
    "newbalanceDest",  # recipient balance after
]

TARGET_COLUMN = "isFraud"

# ---------------------------------------------------------------------------
# Engineered feature schema (output of engineer_features)
# ---------------------------------------------------------------------------
# Categorical feature that is one-hot encoded by the preprocessor.
CATEGORICAL_FEATURES = ["type"]

# Numeric features (passed through / scaled by the preprocessor).
NUMERIC_FEATURES = [
    "step",
    "hour",               # step % 24
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
    "errorBalanceOrig",   # newbalanceOrig + amount - oldbalanceOrg
    "errorBalanceDest",    # oldbalanceDest + amount - newbalanceDest
    "amount_to_oldOrg",   # amount / (oldbalanceOrg + 1)
    "orig_emptied",       # 1 if sender balance dropped to ~0
    "dest_zero_before",   # 1 if recipient had 0 balance before
]

MODEL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES

# ---------------------------------------------------------------------------
# Primary model-selection metric (documented decision).
# For a highly imbalanced fraud problem, PR-AUC (average precision) is the most
# informative single number because it focuses on the positive (fraud) class and
# is insensitive to the large true-negative mass. Accuracy is deliberately NOT
# used for selection.
# ---------------------------------------------------------------------------
SELECTION_METRIC = "pr_auc"

RANDOM_STATE = 42
