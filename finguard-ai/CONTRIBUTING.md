# Contributing to FinGuard AI

Thanks for your interest in improving FinGuard AI!

## Development setup

See the [README](./README.md) for full setup. In short:

```bash
# ML (train a model first — the backend needs the artifacts)
cd ml && pip install -r requirements.txt && python -m src.train

# Backend
cd ../backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# Frontend
cd ../frontend && npm install && npm run dev
```

## Workflow

1. Fork and create a feature branch: `git checkout -b feature/my-change`.
2. Make your change with clear, focused commits.
3. Add or update tests for any behaviour you change.
4. Run the full test suite locally (see below) — it must be green.
5. Open a pull request describing the change and the reasoning.

## Running tests

```bash
cd ml && pytest tests/ -q
cd ../backend && pytest -q
cd ../frontend && npm run test && npm run build
```

## Code style

- **Python**: PEP 8, type hints where practical, docstrings on public functions.
- **TypeScript/React**: functional components, typed props, no `any` in new code
  unless unavoidable.
- Keep modules small and single-purpose.

## Guidelines

- Never commit secrets or `.env` files.
- Never commit trained model binaries or datasets (they are gitignored and
  regenerated via training).
- Do not report synthetic-data metrics as real PaySim results.
- Validate and sanitise all external input (API payloads, CSV uploads).
