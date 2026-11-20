"""
Synthetic PaySim-STYLE transaction generator (DEVELOPMENT DATA ONLY).

=============================================================================
 IMPORTANT: This produces a SYNTHETIC, clearly-labelled development dataset.
 It is NOT the real PaySim dataset and its metrics MUST NOT be reported as
 real PaySim benchmark results. It exists so the pipeline is fully runnable
 without the Kaggle PaySim download (which requires authentication).
 To use the real data, see data/README.md.
=============================================================================

The generator reproduces the key statistical structure that makes the PaySim
fraud problem realistic and learnable:
  * five transaction types, with fraud only on TRANSFER / CASH_OUT;
  * heavy class imbalance (default ~0.3% fraud);
  * fraud transactions tend to move large amounts and drain the origin account
    to zero, often into previously-empty destination accounts, breaking the
    balance-accounting identity.
"""
from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd

try:
    from .config import TRANSACTION_TYPES, RANDOM_STATE
except ImportError:
    from config import TRANSACTION_TYPES, RANDOM_STATE


def generate(n_rows: int = 120_000, fraud_rate: float = 0.003,
             seed: int = RANDOM_STATE) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Transaction-type mix roughly follows the real PaySim proportions.
    type_probs = {
        "CASH_OUT": 0.35,
        "PAYMENT": 0.34,
        "CASH_IN": 0.22,
        "TRANSFER": 0.08,
        "DEBIT": 0.01,
    }
    types = rng.choice(
        list(type_probs.keys()),
        size=n_rows,
        p=list(type_probs.values()),
    )

    step = rng.integers(1, 743, size=n_rows)  # ~31 days of hours

    # Amounts: log-normal, bounded.
    amount = np.round(rng.lognormal(mean=8.2, sigma=1.3, size=n_rows), 2)
    amount = np.clip(amount, 1.0, 1.0e7)

    old_org = np.round(np.clip(rng.lognormal(9.0, 1.6, n_rows), 0, 5.0e7), 2)
    # Legitimate: new = max(old - amount, 0)
    new_org = np.round(np.clip(old_org - amount, 0, None), 2)

    old_dest = np.round(np.clip(rng.lognormal(8.5, 1.8, n_rows), 0, 5.0e7), 2)
    new_dest = np.round(np.clip(old_dest + amount, 0, None), 2)

    # CASH_IN increases the origin balance instead.
    cash_in = types == "CASH_IN"
    new_org[cash_in] = np.round(old_org[cash_in] + amount[cash_in], 2)

    is_fraud = np.zeros(n_rows, dtype=int)

    # Inject fraud only on eligible types.
    eligible = np.isin(types, ["TRANSFER", "CASH_OUT"])
    eligible_idx = np.where(eligible)[0]
    n_fraud = int(round(n_rows * fraud_rate))
    n_fraud = min(n_fraud, len(eligible_idx))
    fraud_idx = rng.choice(eligible_idx, size=n_fraud, replace=False)

    is_fraud[fraud_idx] = 1
    # Fraud pattern: large amount == full origin balance, origin emptied,
    # destination frequently previously empty, accounting identity broken.
    amount[fraud_idx] = old_org[fraud_idx]
    new_org[fraud_idx] = 0.0
    zero_dest = rng.random(len(fraud_idx)) < 0.7
    old_dest[fraud_idx[zero_dest]] = 0.0
    new_dest[fraud_idx] = 0.0  # mules sweep funds out immediately

    # A little label/measurement noise so the problem is not trivially separable.
    noise = rng.random(n_rows) < 0.0004
    is_fraud[noise & eligible] = 1

    df = pd.DataFrame({
        "step": step,
        "type": types,
        "amount": amount,
        "nameOrig": [f"C{rng.integers(10**8, 10**9)}" for _ in range(n_rows)],
        "oldbalanceOrg": old_org,
        "newbalanceOrig": new_org,
        "nameDest": [f"C{rng.integers(10**8, 10**9)}" for _ in range(n_rows)],
        "oldbalanceDest": old_dest,
        "newbalanceDest": new_dest,
        "isFraud": is_fraud,
        "isFlaggedFraud": 0,
    })
    # Keep only the columns needed; preserve identifiers to mirror PaySim.
    return df


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows", type=int, default=120_000)
    ap.add_argument("--fraud-rate", type=float, default=0.003)
    ap.add_argument("--seed", type=int, default=RANDOM_STATE)
    ap.add_argument(
        "--out",
        default=os.path.join(os.path.dirname(__file__), "..", "data",
                             "synthetic_transactions.csv"),
    )
    args = ap.parse_args()

    df = generate(args.rows, args.fraud_rate, args.seed)
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    df.to_csv(out, index=False)
    n_fraud = int(df["isFraud"].sum())
    print(f"[SYNTHETIC] wrote {len(df):,} rows -> {out}")
    print(f"[SYNTHETIC] fraud: {n_fraud:,} ({n_fraud / len(df) * 100:.3f}%)")
    print("[SYNTHETIC] NOTE: development data only, not real PaySim.")


if __name__ == "__main__":
    main()
