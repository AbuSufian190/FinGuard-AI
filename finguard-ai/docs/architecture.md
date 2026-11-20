# FinGuard AI — Architecture

## Overview

FinGuard AI is a modular, three-tier full-stack application:

```
┌──────────────────────────┐        REST/JSON        ┌───────────────────────────┐
│        Frontend          │ ──────────────────────► │          Backend          │
│  React + TS + Vite       │ ◄────────────────────── │  FastAPI + Pydantic       │
│  Tailwind + Recharts     │                         │  SQLAlchemy ORM           │
└──────────────────────────┘                         └────────────┬──────────────┘
                                                                   │
                           ┌───────────────────────────────┬──────┴───────────┐
                           ▼                                ▼                  ▼
                  ┌──────────────────┐          ┌────────────────────┐ ┌──────────────┐
                  │  Inference layer │          │   PostgreSQL DB    │ │  Artifacts   │
                  │  Predictor +     │          │  transactions      │ │ model.joblib │
                  │  SHAP explainer  │          │  predictions       │ │ metadata     │
                  └────────┬─────────┘          │  model_versions    │ │ eval report  │
                           │                    │  training_runs     │ └──────┬───────┘
                           │ loads                                           │ produced by
                           ▼                                                 ▼
                  ┌───────────────────────────────────────────────────────────────────┐
                  │                       Offline ML training pipeline                   │
                  │  generate/ingest → EDA → feature engineering → leak-free split →    │
                  │  train (LogReg / RF / XGBoost) → evaluate (PR-AUC, ROC-AUC, F1 …) → │
                  │  select best (validation PR-AUC) → serialise pipeline + metadata    │
                  └───────────────────────────────────────────────────────────────────┘
```

## Separation of concerns

- **Training is offline and separate from inference.** The ML pipeline
  (`ml/`) produces serialized artifacts. The backend loads those artifacts and
  performs only fast, stateless inference. Retraining via the API runs as a
  background task and never blocks request handling.
- **One preprocessing pipeline, two consumers.** Feature engineering
  (`features.py`, pure/stateless) plus a fitted scikit-learn `ColumnTransformer`
  (`preprocessing.py`, fitted on the training split only) are serialized
  together as a single `Pipeline`. The backend reuses this exact object, so
  training and serving preprocessing cannot drift.

## Leakage prevention

The train/validation/test split happens **before** any stateful transformer is
fitted. Scaling and one-hot encoding learn their parameters from the training
split alone. Feature engineering is row-wise and stateless, so it carries no
cross-row information.

## Request flow (single prediction)

1. Frontend `POST /api/predictions` with a validated `TransactionInput`.
2. FastAPI validates the payload (Pydantic) and calls the `Predictor`.
3. `engineer_features` → fitted `Pipeline.predict_proba` → probability.
4. Probability compared to the tuned decision threshold → `is_fraud` + risk tier.
5. SHAP `TreeExplainer` produces top contributing features.
6. Transaction + prediction persisted to PostgreSQL; response returned.

## Technology choices

| Layer     | Choice                         | Why                                        |
|-----------|--------------------------------|--------------------------------------------|
| Model     | XGBoost / RF / LogReg          | Strong tabular baselines; tree models pair well with SHAP |
| Selection | Validation PR-AUC              | Robust to extreme class imbalance          |
| Explain   | SHAP TreeExplainer             | Faithful per-prediction attributions       |
| API       | FastAPI + Pydantic             | Async, typed, auto OpenAPI docs            |
| DB        | PostgreSQL + SQLAlchemy/Alembic| Relational history, migrations             |
| UI        | React + Vite + Tailwind        | Fast, modern SaaS dashboard                |
