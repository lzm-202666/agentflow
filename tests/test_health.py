async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

async def test_ping(client):
    r = await client.get("/api/ping")
    assert r.status_code == 200
    assert r.json() == {"pong":True}

async def test_metrics(client):
    r = await client.get("/metrics")
    assert r.status_code == 200
    assert "agentflow_requests_total" in r.text