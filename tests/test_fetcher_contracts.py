import logging

from core.fetchers.bk_magazine import BKMagazineFetcher
from core.fetchers.timeout_bkk import TimeOutBKKFetcher
from core.models import Event


def _sample_events():
    return [
        {"id": "1", "title": "Good", "url": "https://e.com", "source": ""},
        {"id": "bad", "url": "not-a-url", "source": "src"},
    ]


def _run_fetcher(fetcher_cls, monkeypatch, caplog):
    fetcher = fetcher_cls()

    def fake_raw(self, category=None, limit=None):
        return _sample_events()

    monkeypatch.setattr(fetcher_cls, "_raw_events", fake_raw)
    with caplog.at_level(logging.WARNING, logger="fetcher"):
        events = fetcher.fetch()
    assert len(events) == 1
    assert isinstance(events[0], Event)
    assert "Invalid event" in caplog.text
    # имя источника должно подставиться, если было пустым
    assert events[0].source in {"timeout_bkk", "bk_magazine"}


def test_timeout_bkk_fetcher(monkeypatch, caplog):
    _run_fetcher(TimeOutBKKFetcher, monkeypatch, caplog)


def test_bk_magazine_fetcher(monkeypatch, caplog):
    _run_fetcher(BKMagazineFetcher, monkeypatch, caplog)


def test_fetcher_handles_exception(monkeypatch, caplog):
    fetcher = TimeOutBKKFetcher()

    def boom(self, category=None, limit=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(TimeOutBKKFetcher, "_raw_events", boom)
    with caplog.at_level(logging.WARNING, logger="fetcher"):
        events = fetcher.fetch()
    assert events == []
    assert "boom" in caplog.text


def test_limit_applied_after_validation(monkeypatch, caplog):
    fetcher = TimeOutBKKFetcher()

    def fake_raw(self, category=None, limit=None):
        # 1 валидный + 3 бракованных → после фильтрации останется 1, limit=1 не режет валидность
        return [
            {"id": "1", "title": "Good", "url": "https://e.com", "source": ""},
            {"id": "x", "url": "bad-url", "source": "s"},
            {"id": "y", "url": "also-bad", "source": "s"},
            {"id": "z", "url": "://bad", "source": "s"},
        ]

    monkeypatch.setattr(TimeOutBKKFetcher, "_raw_events", fake_raw)
    with caplog.at_level(logging.WARNING, logger="fetcher"):
        events = fetcher.fetch(limit=1)
    assert len(events) == 1
    assert isinstance(events[0], Event)
    assert events[0].source == "timeout_bkk"
