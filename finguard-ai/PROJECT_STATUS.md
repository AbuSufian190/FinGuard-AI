# PROJECT_STATUS.md

Status snapshot for FinGuard AI. Updated: 2026-11-19.

## Overall: functional end-to-end (synthetic data), tested.

## Completed

- **Phase 1 — Scaffold:** full monorepo structure (ml / backend / frontend /
  docs / CI).
- **Phase 2 — ML pipeline:** synthetic PaySim-style generator, EDA, leak-free
  preprocessing, LogReg + RandomForest + XGBoost, PR-AUC/ROC-AUC/F1/precision/
  recall/confusion-matrix evaluation, validation-PR-AUC model selection,
  threshold tuning, SHAP explainer, artifact serialization. **Trained
  successfully** (Random Forest selected). Artifacts in `ml/artifacts/` and
  copied to `backend/app/ml/artifacts/`.
- **Phase 3 — Backend:** FastAPI app, Pydantic schemas, SQLAlchemy models,
  Alembic migration (0001), all required endpoints, predictor service, batch
  CSV validation, pagination, logging, CORS, global exception handling.
- **Phase 4 — Frontend:** Vite + React + TS + Tailwind SPA, sidebar nav,
  light/dark theme, all 7 pages wired to real endpoints, Recharts charts,
  Axios client, loading/error/empty states. **Production build passes.**
- **Phase 5 — Integration + tests:** backend (19) + ML (6) + frontend (5) tests
  all pass; live uvicorn server verified via HTTP (health, prediction+SHAP,
  dashboard, performance, OpenAPI routes).
- **Phase 6 — DevOps + docs:** Dockerfiles (backend/frontend/trainer),
  docker-compose (db + trainer + backend + frontend), .env.example, .gitignore,
  GitHub Actions CI, README (with real synthetic-data metrics), LICENSE,
  CONTRIBUTING, architecture + API docs.

## Verified commands

```bash
cd ml && python -m src.train           # trains, writes artifacts
cd ml && pytest tests/ -q              # 6 passed
cd backend && pytest -q                # 19 passed
cd frontend && npm run build           # type-check + build OK
cd frontend && npm run test            # 5 passed
```

## Known limitations / pending (require your input)

- **Real PaySim not used.** Metrics are from synthetic data. To benchmark:
  download PaySim to `ml/data/paysim.csv` and retrain (see `ml/data/README.md`).
- **Docker build not executed here** (no Docker daemon in the build
  environment). Configs are written and self-consistent; run
  `docker compose up --build` locally to validate images.
- **No authentication** implemented (schema leaves room for it).
- **Deployment** to Vercel/Render/Supabase is configured but not performed
  (needs your credentials + approval).

## Next exact step if resuming

1. `docker compose up --build` locally and confirm all four services come up.
2. (Optional) Train on real PaySim and commit the refreshed
   `evaluation_report.json` numbers into the README table.
3. Add UI screenshots to the README `Screenshots` section.
