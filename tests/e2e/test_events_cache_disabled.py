from fastapi.testclient import TestClient
import os
from main import app

def test_events_cache_disabled(monkeypatch):
    # REDIS_URL отсутствует -> кэш должен быть DISABLED,
    # но keys_checked уже должны присутствовать.
    if "REDIS_URL" in os.environ:
        monkeypatch.delenv("REDIS_URL", raising=False)
    client = TestClient(app)
    payload = {
        "city": "bangkok",
        "date": "2025-08-31",
        "selected_category_ids": ["art_exhibits"]
    }
    res = client.post("/api/events", json=payload)
    assert res.status_code == 200
    d = res.json()["debug"]
    assert d["cache"]["status"] == "DISABLED"
    assert d["cache"]["keys_checked"], "keys_checked must not be empty even when cache is disabled"
    assert d["source"] == "db"
