# Dataset guide

FinGuard AI is designed for the **PaySim** synthetic mobile-money dataset.

- Source: https://www.kaggle.com/datasets/ealaxi/paysim1
- License: CC BY-SA 4.0 (attribute the author, E. A. Lopez-Rojas et al.).
- Size: ~6.3M rows, 11 columns.

## Why a download guide instead of an automatic download

The PaySim file lives behind Kaggle authentication and cannot be fetched
automatically without your credentials. Per the project rules, FinGuard does
**not** attempt to download private/authenticated datasets on your behalf.

## Option A — Use the real PaySim data (recommended for the portfolio)

1. Create a free Kaggle account and accept the dataset terms.
2. Download `PS_20174392719_1491204439457_log.csv` from the link above.
3. Place it here as `ml/data/paysim.csv`.
4. Train on it:

   ```bash
   cd ml
   python -m src.train --data data/paysim.csv
   ```

The PaySim columns already match FinGuard's expected schema
(`step, type, amount, oldbalanceOrg, newbalanceOrig, oldbalanceDest,
newbalanceDest, isFraud`). Identifier columns and `isFlaggedFraud` are ignored.

## Option B — Synthetic development data (default, no download)

If you just want to run the stack, FinGuard generates a **clearly-labelled
synthetic** PaySim-style dataset automatically:

```bash
cd ml
python -m src.train              # generates synthetic data, then trains
```

> ⚠️ Synthetic-data metrics are **development metrics only** and must never be
> presented as real PaySim benchmark results. The synthetic generator produces
> a more separable problem than real PaySim, so scores will look optimistic.
