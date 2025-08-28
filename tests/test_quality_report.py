import requests
from datetime import datetime, timezone

from core.models import Event
from core.quality.qa import quality_report


def _make_events():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return [
        Event(
            id="1",
            title="Dup Event",
            url="https://a",
            source="timeout",
            start=start,
            end=start,
            desc="12345",
            image="https://img/good1.jpg",
            venue="v",
        ),
        Event(
            id="2",
            title="Dup Event",
            url="https://b",
            source="timeout",
            start=start,
            desc="123456",
            image="https://img/good2.jpg",
            venue="v",
        ),
        Event(
            id="3",
            title="Third",
            url="https://c",
            source="timeout",
            start=start,
            desc="1234567",
            image="https://img/bad3.jpg",
        ),
        Event(id="4", title="Fourth", url="https://d", source="timeout"),
        Event(
            id="5",
            title="Fifth",
            url="https://e",
            source="timeout",
            desc="x" * 20,
        ),
        Event(
            id="6",
            title="Sixth",
            url="https://f",
            source="timeout",
            start=start,
            end=start,
        ),
        Event(
            id="7",
            title="Seventh",
            url="https://g",
            source="bk",
            start=start,
            end=start,
            desc="y" * 10,
            image="https://img/good7.jpg",
        ),
        Event(id="8", title="Eighth", url="https://h", source="bk", desc="z" * 5),
        Event(
            id="9",
            title="Ninth",
            url="https://i",
            source="bk",
            start=start,
            image="https://img/good9.jpg",
        ),
        Event(id="10", title="Tenth", url="https://j", source="bk"),
    ]


def test_quality_report(monkeypatch):
    class Resp:
        def __init__(self, code):
            self.status_code = code

    def fake_head(url, timeout=5):
        return Resp(404) if "bad" in url else Resp(200)

    monkeypatch.setenv("QA_CHECK_IMAGES", "true")
    monkeypatch.setattr(requests, "head", fake_head)

    events = _make_events()
    report = quality_report(events)

    assert report["total"] == 10
    assert report["filled_start_pct"] == 60.0
    assert report["filled_end_pct"] == 30.0
    assert report["image_pct"] == 40.0
    assert round(report["avg_desc_len"], 2) == 8.83
    assert report["median_desc_len"] == 6.5
    assert report["duplicates_pct"] == 10.0
    assert report["per_source"]["timeout"]["count"] == 6
    assert report["per_source"]["bk"]["count"] == 4
    assert report["duplicates"][0] == ["1", "2"]
