# FinGuard AI — API Reference

Base URL: `/api`. Interactive docs (Swagger UI) at `/docs`, ReDoc at `/redoc`.

| Method | Path | Description |
|--------|------|-------------|
| GET  | `/health` | Service + model + DB status |
| GET  | `/dashboard/summary` | Aggregated analytics for the dashboard |
| GET  | `/transactions` | Paginated stored transactions |
| POST | `/predictions` | Score a single transaction (`?explain=true` by default) |
| POST | `/predictions/batch` | Score an uploaded CSV |
| GET  | `/predictions/history` | Paginated, filterable prediction history |
| GET  | `/predictions/{id}/explanation` | SHAP explanation for a stored prediction |
| GET  | `/models` | Active model + candidate list |
| GET  | `/models/info` | Active model metadata |
| GET  | `/models/performance` | Full evaluation report (real metrics) |
| POST | `/models/train` | Trigger background (re)training |

## POST /predictions

Request body:

```json
{
  "step": 100,
  "type": "TRANSFER",
  "amount": 181000.0,
  "oldbalanceOrg": 181000.0,
  "newbalanceOrig": 0.0,
  "oldbalanceDest": 0.0,
  "newbalanceDest": 0.0
}
```

Response `201`:

```json
{
  "id": 42,
  "created_at": "2026-11-19T10:00:00Z",
  "fraud_probability": 0.98,
  "is_fraud": true,
  "risk_level": "HIGH",
  "threshold": 0.9849,
  "model_name": "random_forest",
  "model_version": "v2026.11.19",
  "transaction": { "...": "echoed input" },
  "explanation": {
    "method": "shap",
    "top_features": [
      { "feature": "errorBalanceOrig", "contribution": 0.31,
        "value": -1.2, "direction": "increases_risk" }
    ]
  }
}
```

### Validation

- `type` must be one of `PAYMENT, TRANSFER, CASH_OUT, CASH_IN, DEBIT`.
- All amounts/balances must be `>= 0`. Invalid payloads return `422`.
- If no model is loaded, prediction endpoints return `503`.

## POST /predictions/batch

`multipart/form-data` with a `file` field (CSV). Required columns:
`step, type, amount, oldbalanceOrg, newbalanceOrig, oldbalanceDest,
newbalanceDest`.

- Rejects non-CSV (`400`), missing columns / empty / unknown types (`422`),
  oversized files (`413`).
- Returns a summary, per-row results, and a base64-encoded annotated CSV.

## GET /predictions/history

Query params: `page`, `page_size` (≤100), `risk_level`, `is_fraud`, `type`,
`search` (matches id or amount). Returns a standard page envelope
(`items, total, page, page_size, pages`).

## Error format

All errors use FastAPI's `{"detail": "..."}` shape with an appropriate HTTP
status code. Unhandled errors return `500` with a generic message (details are
logged server-side, never leaked to the client).
