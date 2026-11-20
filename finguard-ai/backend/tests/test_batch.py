import io

import pandas as pd


def _csv_bytes(rows):
    return pd.DataFrame(rows).to_csv(index=False).encode()


def test_batch_prediction_valid(client):
    rows = [
        {"step": 1, "type": "TRANSFER", "amount": 5000, "oldbalanceOrg": 5000,
         "newbalanceOrig": 0, "oldbalanceDest": 0, "newbalanceDest": 0},
        {"step": 2, "type": "PAYMENT", "amount": 100, "oldbalanceOrg": 2000,
         "newbalanceOrig": 1900, "oldbalanceDest": 50, "newbalanceDest": 150},
    ]
    files = {"file": ("tx.csv", _csv_bytes(rows), "text/csv")}
    r = client.post("/api/predictions/batch", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["total_rows"] == 2
    assert len(body["results"]) == 2
    assert body["result_csv_base64"]


def test_batch_rejects_non_csv(client):
    files = {"file": ("tx.txt", b"hello", "text/plain")}
    r = client.post("/api/predictions/batch", files=files)
    assert r.status_code == 400


def test_batch_rejects_missing_columns(client):
    files = {"file": ("tx.csv", b"a,b\n1,2\n", "text/csv")}
    r = client.post("/api/predictions/batch", files=files)
    assert r.status_code == 422


def test_batch_rejects_empty(client):
    cols = "step,type,amount,oldbalanceOrg,newbalanceOrig,oldbalanceDest,newbalanceDest\n"
    files = {"file": ("tx.csv", cols.encode(), "text/csv")}
    r = client.post("/api/predictions/batch", files=files)
    assert r.status_code == 422
