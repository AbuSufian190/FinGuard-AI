def test_health_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"
    assert isinstance(body["model_loaded"], bool)


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "docs" in r.json()
