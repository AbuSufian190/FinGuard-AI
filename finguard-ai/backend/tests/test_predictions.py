import pytest


def test_predict_fraud_transaction(client, sample_fraud_tx):
    r = client.post("/api/predictions", json=sample_fraud_tx)
    assert r.status_code == 201
    body = r.json()
    assert 0.0 <= body["fraud_probability"] <= 1.0
    assert body["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert "id" in body
    # a drained-account transfer should score as elevated risk
    assert body["fraud_probability"] > 0.5


def test_predict_legit_transaction(client, sample_legit_tx):
    r = client.post("/api/predictions", json=sample_legit_tx)
    assert r.status_code == 201
    assert r.json()["fraud_probability"] < 0.5


def test_prediction_includes_explanation(client, sample_fraud_tx):
    r = client.post("/api/predictions?explain=true", json=sample_fraud_tx)
    assert r.status_code == 201
    exp = r.json()["explanation"]
    assert exp is not None
    assert len(exp["top_features"]) > 0
    assert "feature" in exp["top_features"][0]


def test_explanation_endpoint(client, sample_fraud_tx):
    pid = client.post("/api/predictions", json=sample_fraud_tx).json()["id"]
    r = client.get(f"/api/predictions/{pid}/explanation")
    assert r.status_code == 200
    assert "top_features" in r.json()


@pytest.mark.parametrize("bad", [
    {"type": "TRANSFER", "amount": -5, "oldbalanceOrg": 1,
     "newbalanceOrig": 0, "oldbalanceDest": 0, "newbalanceDest": 0},
    {"type": "NOT_A_TYPE", "amount": 5, "oldbalanceOrg": 1,
     "newbalanceOrig": 0, "oldbalanceDest": 0, "newbalanceDest": 0},
    {"amount": 5, "oldbalanceOrg": 1, "newbalanceOrig": 0,
     "oldbalanceDest": 0, "newbalanceDest": 0},  # missing type
])
def test_validation_rejects_bad_input(client, bad):
    r = client.post("/api/predictions", json=bad)
    assert r.status_code == 422


def test_history_pagination(client, sample_legit_tx):
    for _ in range(3):
        client.post("/api/predictions", json=sample_legit_tx)
    r = client.get("/api/predictions/history?page=1&page_size=2")
    assert r.status_code == 200
    body = r.json()
    assert body["page_size"] == 2
    assert len(body["items"]) <= 2
    assert body["total"] >= 3


def test_explanation_404_for_missing(client):
    r = client.get("/api/predictions/99999999/explanation")
    assert r.status_code == 404
