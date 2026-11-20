def test_dashboard_summary(client, sample_fraud_tx):
    client.post("/api/predictions", json=sample_fraud_tx)
    r = client.get("/api/dashboard/summary")
    assert r.status_code == 200
    body = r.json()
    for key in ("total_transactions", "fraudulent_detected",
                "fraud_detection_rate", "average_amount", "trend",
                "fraud_distribution", "recent_suspicious"):
        assert key in body
    assert body["total_transactions"] >= 1


def test_model_info(client):
    r = client.get("/api/models/info")
    assert r.status_code == 200
    body = r.json()
    assert body["selection_metric"] == "pr_auc"
    assert body["loaded"] is True
    assert len(body["features"]) > 0


def test_model_performance_real_metrics(client):
    r = client.get("/api/models/performance")
    assert r.status_code == 200
    body = r.json()
    assert "selected_model" in body
    assert "models" in body
    sel = body["selected_model"]
    assert "test" in body["models"][sel]
    assert 0.0 <= body["models"][sel]["test"]["pr_auc"] <= 1.0


def test_transactions_listing(client, sample_legit_tx):
    client.post("/api/predictions", json=sample_legit_tx)
    r = client.get("/api/transactions?page=1&page_size=5")
    assert r.status_code == 200
    assert "items" in r.json()
