"""Lightweight exploratory data analysis producing a JSON-serialisable summary."""
from __future__ import annotations

from typing import Dict

import pandas as pd

try:
    from .config import TARGET_COLUMN
except ImportError:
    from config import TARGET_COLUMN


def run_eda(df: pd.DataFrame) -> Dict:
    n_rows = int(len(df))
    n_fraud = int(df[TARGET_COLUMN].sum())

    by_type = (
        df.groupby("type")[TARGET_COLUMN]
        .agg(["count", "sum"])
        .rename(columns={"count": "n", "sum": "fraud"})
    )
    by_type["fraud_rate"] = by_type["fraud"] / by_type["n"]

    amount = df["amount"]
    fraud_amount = df.loc[df[TARGET_COLUMN] == 1, "amount"]
    legit_amount = df.loc[df[TARGET_COLUMN] == 0, "amount"]

    return {
        "n_rows": n_rows,
        "n_fraud": n_fraud,
        "fraud_rate": n_fraud / max(n_rows, 1),
        "n_duplicates": int(df.duplicated().sum()),
        "missing_values": {c: int(df[c].isna().sum())
                           for c in df.columns if df[c].isna().any()},
        "transaction_types": {
            t: {
                "count": int(r["n"]),
                "fraud": int(r["fraud"]),
                "fraud_rate": float(r["fraud_rate"]),
            }
            for t, r in by_type.iterrows()
        },
        "amount_stats": {
            "mean": float(amount.mean()),
            "median": float(amount.median()),
            "max": float(amount.max()),
            "fraud_mean": float(fraud_amount.mean()) if len(fraud_amount) else 0.0,
            "legit_mean": float(legit_amount.mean()) if len(legit_amount) else 0.0,
        },
        "class_balance": {
            "legit": int((df[TARGET_COLUMN] == 0).sum()),
            "fraud": n_fraud,
            "imbalance_ratio": float((df[TARGET_COLUMN] == 0).sum()
                                     / max(n_fraud, 1)),
        },
    }
