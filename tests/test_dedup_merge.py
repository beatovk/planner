from datetime import datetime, timezone
from core.models import Event
from core.dedup import merge_events

def _dt(y, m, d):
    return datetime(y, m, d, tzinfo=timezone.utc)

def test_merge_by_identity_and_fuzzy():
    # два дубля одного события (разные источники), плюс почти-дубль с опечаткой
    e1 = Event(
        id="t1",
        title="Rooftop Jazz Night",
        url="https://timeout.example/a",
        source="timeout_bkk",
        start=_dt(2024,1,10),
        end=_dt(2024,1,10),
        venue="Sky Bar",
        desc="Short.",
        image="https://img.example/a1.jpg",
        tags=["music"],
        categories=["nightlife"],
    )
    e2 = Event(
        id="b1",
        title="Rooftop Jazz Night",
        url="https://bk.example/a",
        source="bk_magazine",
        start=_dt(2024,1,10),
        end=_dt(2024,1,10),
        venue="Sky Bar",
        desc="Longer description about the rooftop jazz night with details.",
        image="https://img.example/a2.jpg",
        tags=["jazz","music"],
        categories=["nightlife"],
    )
    e3 = Event(
        id="t2",
        title="Rooftop Jaz Night",  # опечатка
        url="https://timeout.example/b",
        source="timeout_bkk",
        start=_dt(2024,1,10),
        end=_dt(2024,1,10),
        venue="Sky Bar",
        desc="Another variant.",
        image=None,
        tags=["rooftop"],
        categories=["nightlife"],
    )
    e4 = Event(  # другое событие
        id="x1",
        title="Street Food Market",
        url="https://timeout.example/c",
        source="timeout_bkk",
        start=_dt(2024,1,11),
        end=_dt(2024,1,11),
        venue="Old Town",
        desc="Tasty.",
        image=None,
        tags=["streetfood"],
        categories=["food"],
    )
    merged = merge_events([e1, e2, e3, e4])
    # ожидаем 2 результата (джазовая группа слита)
    assert len(merged) == 2
    jazz = [m for m in merged if "jazz" in m.tags or "music" in m.tags][0]
    # источник/URL взят по приоритету timeout_bkk
    assert jazz.source == "timeout_bkk"
    assert str(jazz.url).startswith("https://timeout.")
    # описание — самое информативное (длиннее)
    assert "Longer description" in (jazz.attrs.get("desc_full") or jazz.desc or "")
    # теги/категории — объединены без дубликатов
    assert set(jazz.tags) >= {"music","jazz","rooftop"}
    assert "nightlife" in jazz.categories
    # merged_ids и sources присутствуют
    assert set(jazz.attrs.get("merged_ids", [])) >= {"t1","b1","t2"}
    assert set(jazz.attrs.get("sources", [])) >= {"timeout_bkk","bk_magazine"}
