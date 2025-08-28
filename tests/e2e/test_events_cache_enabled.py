from fastapi.testclient import TestClient
import os
import pytest
from unittest.mock import patch
import fakeredis
from main import app


def test_events_cache_enabled():
    """Тест включённого кэша: первый POST → MISS + запись, второй POST → HIT/STALE."""

    # Создаём fake Redis сервер
    fake_redis = fakeredis.FakeRedis(decode_responses=True)

    # Мокаем ensure_client и is_configured чтобы возвращать fake Redis
    with (
        patch("core.cache.ensure_client", return_value=fake_redis),
        patch("core.cache.is_configured", return_value=True),
    ):
        client = TestClient(app)

        payload = {
            "city": "bangkok",
            "date": "2025-08-31",
            "selected_category_ids": ["art_exhibits"],
        }

        # 1-й вызов (MISS + запись)
        res1 = client.post("/api/events", json=payload)
        assert res1.status_code == 200
        debug1 = res1.json()["debug"]

        # Проверяем что кэш работает
        assert debug1["cache"]["status"] in [
            "MISS",
            "db",
        ], f"Expected MISS or db, got {debug1['cache']['status']}"
        assert debug1["cache"]["keys_checked"], "keys_checked must not be empty"
        assert debug1["source"] == "db", f"Expected source=db, got {debug1['source']}"

        # 2-й вызов (HIT/STALE)
        res2 = client.post("/api/events", json=payload)
        assert res2.status_code == 200
        debug2 = res2.json()["debug"]

        # Проверяем что второй вызов даёт HIT или STALE
        assert debug2["cache"]["status"] in [
            "HIT",
            "STALE",
        ], f"Expected HIT or STALE, got {debug2['cache']['status']}"
        assert (
            debug2["source"] == "redis"
        ), f"Expected source=redis, got {debug2['source']}"
        assert debug2["cache"][
            "keys_checked"
        ], "keys_checked must not be empty on second call"

        # Проверяем что события читаются из кэша
        events2 = res2.json()["events"]
        assert len(events2) > 0, "Should have events from cache"

        print(
            f"First call: {debug1['cache']['status']}, Second call: {debug2['cache']['status']}"
        )
        print(f"First source: {debug1['source']}, Second source: {debug2['source']}")
        print(f"Events count: {len(events2)}")


def test_events_cache_keys_structure():
    """Тест структуры ключей кэша."""

    fake_redis = fakeredis.FakeRedis(decode_responses=True)

    with (
        patch("core.cache.ensure_client", return_value=fake_redis),
        patch("core.cache.is_configured", return_value=True),
    ):
        client = TestClient(app)

        payload = {
            "city": "bangkok",
            "date": "2025-08-31",
            "selected_category_ids": ["art_exhibits"],
        }

        res = client.post("/api/events", json=payload)
        assert res.status_code == 200
        debug = res.json()["debug"]

        # Проверяем структуру ключей
        keys_checked = debug["cache"]["keys_checked"]
        assert len(keys_checked) > 0, "keys_checked must not be empty"

        # Проверяем формат ключей (v2:bangkok:2025-08-31:flag:art)
        for key in keys_checked:
            assert key.startswith("v2:"), f"Key should start with 'v2:', got {key}"
            assert "bangkok" in key, f"Key should contain city, got {key}"
            assert "2025-08-31" in key, f"Key should contain date, got {key}"
            assert "flag:" in key, f"Key should contain 'flag:', got {key}"

        print(f"Keys checked: {keys_checked}")
