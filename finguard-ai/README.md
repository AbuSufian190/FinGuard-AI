# FinGuard AI — Intelligent Financial Fraud Detection Platform

FinGuard AI is a full-stack, machine-learning web application that detects
potentially fraudulent financial transactions in real time. It trains Logistic
Regression, Random Forest and XGBoost models on PaySim-style mobile-money data,
selects the best by **PR-AUC**, serves predictions through a FastAPI backend,
and presents them in a modern React dashboard with **SHAP-based explanations**
of *why* each transaction was flagged.

> ⚠️ **Educational portfolio project.** Not a production financial system. The
> metrics shown below were produced on a **synthetic development dataset**, not
> the real PaySim benchmark (see [Dataset](#dataset)).

---

## Table of contents

1. [Problem statement](#problem-statement)
2. [Features](#features)
3. [Technology stack](#technology-stack)
4. [Architecture](#architecture)
5. [Folder structure](#folder-structure)
6. [Dataset](#dataset)
7. [ML methodology](#ml-methodology)
8. [Model evaluation results](#model-evaluation-results)
9. [Installation](#installation)
10. [Environment setup](#environment-setup)
11. [Database setup](#database-setup)
12. [API documentation](#api-documentation)
13. [Screenshots](#screenshots)
14. [Deployment](#deployment)
15. [Limitations](#limitations)
16. [Future improvements](#future-improvements)

---

## Problem statement

Financial fraud causes large losses and is hard to catch because fraudulent
transactions are a tiny fraction of all activity (severe class imbalance) and
look superficially similar to legitimate ones. FinGuard AI frames this as a
supervised binary-classification problem on transaction records, optimising for
catching fraud (recall / PR-AUC) without drowning analysts in false positives.

## Features

- **Dashboard** — totals, fraud count, detection rate, average amount,
  transaction trend, risk distribution, recent suspicious transactions.
- **Transaction Analysis** — score a single transaction and see a probability,
  risk tier, and top SHAP contributing factors.
- **Batch Detection** — upload a CSV, validate it, score every row, download an
  annotated results CSV.
- **Model Performance** — model comparison table, ROC and PR curves, confusion
  matrix, all from **real evaluation output**.
- **Prediction History** — searchable, filterable, paginated record of past
  predictions.
- **Model Information** — active model, version, threshold, features.
- **Settings / About** — light/dark theme, live system status.

Every page is wired to a real backend endpoint — no hard-coded analytics.

## Technology stack

**Frontend:** React, TypeScript, Vite, Tailwind CSS, shadcn/ui-style components,
Recharts, Axios, React Router.
**Backend:** Python, FastAPI, Pydantic, SQLAlchemy, Alembic.
**ML:** Pandas, NumPy, scikit-learn, XGBoost, SHAP, Joblib.
**Database:** PostgreSQL (SQLite for zero-config local dev).
**Testing:** Pytest, HTTPX, Vitest, React Testing Library.
**DevOps:** Docker, Docker Compose, GitHub Actions.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full diagram and
rationale. In short: an **offline training pipeline** produces a serialized
scikit-learn `Pipeline` (preprocessing + model) plus metadata; the **FastAPI
backend** loads those artifacts and performs stateless inference and SHAP
explanation; **PostgreSQL** stores transactions, predictions, model versions and
training runs; the **React** SPA talks to the backend over REST. Training and
inference are deliberately decoupled, and the *same* fitted preprocessing
pipeline is used in both so they can never drift.

## Folder structure

```
finguard-ai/
├── ml/                    # Offline ML pipeline
│   ├── src/               # config, features, preprocessing, train, evaluate, explain, eda
│   ├── data/              # dataset location + download guide (gitignored CSVs)
│   ├── artifacts/         # trained model.joblib, feature_metadata.json, model_card.json
│   ├── reports/           # evaluation_report.json, eda_summary.json
│   └── tests/             # ML unit tests
├── backend/               # FastAPI service
│   ├── app/
│   │   ├── main.py        # app factory, CORS, exception handling, lifespan
│   │   ├── config.py      # env-based settings
│   │   ├── database.py    # SQLAlchemy engine/session
│   │   ├── models.py      # ORM: transactions, predictions, model_versions, training_runs
│   │   ├── schemas.py     # Pydantic request/response models
│   │   ├── crud.py        # DB access (ORM, parameterised)
│   │   ├── ml/            # predictor, explainer, shared feature code, artifacts
│   │   └── routers/       # health, dashboard, transactions, predictions, models
│   ├── alembic/           # migrations
│   └── tests/             # backend tests (pytest + httpx)
├── frontend/              # React + Vite SPA
│   └── src/{api,components,pages,hooks,lib}
├── docs/                  # architecture.md, api.md
├── .github/workflows/     # CI
├── docker-compose.yml
├── .env.example
└── README.md
```

## Dataset

FinGuard targets the **PaySim** synthetic mobile-money dataset
([Kaggle](https://www.kaggle.com/datasets/ealaxi/paysim1), CC BY-SA 4.0).
PaySim requires a Kaggle login, so it is **not** downloaded automatically and is
**not** redistributed here. Two options (details in
[ml/data/README.md](ml/data/README.md)):

- **Real PaySim:** download the CSV, place it at `ml/data/paysim.csv`, and run
  `python -m src.train --data data/paysim.csv`.
- **Synthetic dev data (default):** `python -m src.train` generates a
  clearly-labelled PaySim-style dataset so the stack runs with no download.

## ML methodology

1. **EDA** — transaction-type mix, amount distributions, fraud distribution,
   balance patterns, missing values, duplicates, class imbalance.
2. **Feature engineering** — balance-consistency errors (`errorBalanceOrig`,
   `errorBalanceDest`), account-emptying flags, amount ratios, hour-of-day.
   Pure and row-wise (no leakage).
3. **Leak-free split** — stratified train/validation/test split **before** any
   stateful preprocessing is fitted.
4. **Preprocessing** — one-hot encoding + standard scaling inside a scikit-learn
   `ColumnTransformer`, fitted on the training split only.
5. **Class imbalance** — handled via `class_weight="balanced"` (LogReg/RF) and
   `scale_pos_weight` (XGBoost). SMOTE is intentionally *not* applied globally;
   if used it must stay inside training folds only.
6. **Models** — Logistic Regression, Random Forest, XGBoost.
7. **Selection** — best model chosen by **validation PR-AUC** (documented;
   accuracy is never the selection metric). The decision threshold is tuned on
   the validation split to maximise F1.
8. **Explainability** — SHAP `TreeExplainer` for per-prediction attributions.
9. **Artifacts** — serialized pipeline, feature metadata, model card, and a full
   evaluation report are saved and loaded by the backend.

## Model evaluation results

> **Source: SYNTHETIC development data — NOT real PaySim benchmark results.**
> Numbers are reproducible via `cd ml && python -m src.train` and are read live
> by the Model Performance page. Synthetic data is more separable than real
> PaySim, so these scores are optimistic. Re-run on real PaySim for meaningful
> benchmarks.

Run: 120,000 rows, fraud rate ≈ 0.31%, stratified 60/20/20 split.
**Selected model: Random Forest** (highest validation PR-AUC). Decision
threshold ≈ **0.985** (tuned on validation).

Test-split metrics (threshold applied for precision/recall/F1):

| Model               | PR-AUC | ROC-AUC |   F1  | Precision | Recall |
|---------------------|:------:|:-------:|:-----:|:---------:|:------:|
| Logistic Regression | 0.921  | 0.980   | 0.929 |  1.000    | 0.867  |
| Random Forest ⭐     | 0.920  | 0.957   | 0.951 |  1.000    | 0.907  |
| XGBoost             | 0.921  | 0.962   | 0.958 |  1.000    | 0.920  |

Selected-model confusion matrix (test): TN=23,925 · FP=0 · FN=7 · TP=68.

## Installation

### Option 1 — Docker Compose (recommended)

```bash
cp .env.example .env         # adjust POSTGRES_PASSWORD etc.
docker compose up --build
```

This starts PostgreSQL, runs a one-shot **trainer** that writes a model into a
shared volume, runs backend migrations, and serves:

- Frontend: http://localhost:8080
- Backend API + Swagger docs: http://localhost:8000/docs

### Option 2 — Local (no Docker)

```bash
# 1. Train a model (required before the backend can predict)
cd ml
pip install -r requirements.txt
python -m src.train                 # synthetic data; or --data data/paysim.csv

# 2. Backend (defaults to local SQLite if DATABASE_URL is unset)
cd ../backend
pip install -r requirements.txt
alembic upgrade head                # or let startup auto-create tables
python seed_demo.py                 # optional: demo data for the dashboard
uvicorn app.main:app --reload       # http://localhost:8000

# 3. Frontend
cd ../frontend
npm install
npm run dev                         # http://localhost:5173 (proxies /api -> :8000)
```

## Environment setup

Copy `.env.example` to `.env`. Key variables: `DATABASE_URL`, `CORS_ORIGINS`,
`MAX_UPLOAD_MB`, `MAX_BATCH_ROWS`, and the `POSTGRES_*` credentials used by
Compose. The frontend reads `VITE_API_BASE_URL` (empty = use the dev proxy).
**Secrets live only in `.env`, which is gitignored.**

## Database setup

Schema is managed by **Alembic** (`backend/alembic/`). Apply migrations with
`alembic upgrade head`. For quick local runs, the app can also auto-create
tables on startup. Entities: `transactions`, `predictions`, `model_versions`,
`training_runs`, with indexes on prediction `created_at`, `is_fraud` and
`risk_level`.

## API documentation

Full reference in [docs/api.md](docs/api.md); interactive Swagger UI at `/docs`.
Endpoints include `/api/health`, `/api/dashboard/summary`, `/api/transactions`,
`/api/predictions`, `/api/predictions/batch`, `/api/predictions/history`,
`/api/predictions/{id}/explanation`, `/api/models`, `/api/models/performance`,
`/api/models/train`.

## Screenshots

_Run the stack locally and add screenshots of the Dashboard, Transaction
Analysis, and Model Performance pages here. (No screenshots are bundled — the UI
renders live from your own data.)_

## Deployment

Deployment configs are provided but **nothing is deployed automatically** — that
requires your own credentials and approval.

- **Frontend → Vercel:** build `npm run build`, output `frontend/dist`, set
  `VITE_API_BASE_URL` to your backend URL.
- **Backend → Render:** Docker deploy of `backend/`; set `DATABASE_URL` and
  `CORS_ORIGINS`; start command runs `alembic upgrade head` then uvicorn.
- **Database → Supabase / any managed PostgreSQL:** point `DATABASE_URL` at it.
- Train a model and make the artifacts available to the backend (bake into the
  image or mount a volume) before enabling predictions.

## Limitations

- Shipped metrics are from **synthetic data**, not real PaySim.
- No authentication/authorization (out of scope; schema leaves room for a
  `users` table).
- Batch persistence is capped (first 1,000 rows) to protect the demo DB.
- SHAP explanations add latency on large batches; batch scoring returns
  probabilities without per-row SHAP by default.
- The model is a tabular baseline, not tuned for a specific production cost
  matrix.

## Future improvements

- Authentication + role-based access control.
- Hyper-parameter search and probability calibration.
- Threshold selection driven by an explicit cost matrix.
- Model monitoring / drift detection and a model registry.
- Streaming / real-time scoring and alerting.
- Async batch jobs with progress for very large files.

---

Licensed under the [MIT License](LICENSE). PaySim data is CC BY-SA 4.0 and is
not redistributed here.
