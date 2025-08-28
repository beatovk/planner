from datetime import datetime, timezone

from core.models import Event


def test_string_and_url_normalization():
    event = Event(
        id="  e1 ",
        title="Title &amp; More",
        url="example.com/path",
        source=" src ",
        image="img.com/p.png",
    )
    assert event.id == "e1"
    assert event.title == "Title & More"
    assert event.source == "src"
    assert str(event.url) == "https://example.com/path"
    assert str(event.image) == "https://img.com/p.png"


def test_categories_tags_normalized():
    event = Event(
        id="1",
        title="t",
        url="https://a",
        source="s",
        categories=[" Food ", "music", "FOOD"],
        tags=" Jazz  ",
    )
    assert event.categories == ["food", "music"]
    assert event.tags == ["jazz"]


def test_attrs_and_desc_truncation():
    long_desc = "a" * 4010
    event = Event(
        id="1",
        title="t",
        url="https://a",
        source="s",
        desc=long_desc,
        attrs={"outdoor": "yes", "live": 1},
    )
    assert event.attrs["outdoor"] is True
    assert event.attrs["live"] is True
    assert "desc_full" in event.attrs and event.attrs["desc_full"] == long_desc
    assert event.desc.endswith("…")
    assert len(event.desc) <= 4001


def test_fetched_at_auto_and_identity_key():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    e1 = Event(
        id="1",
        title=" My Event ",
        url="https://a",
        source="s",
        start=start,
        venue=" Venue ",
    )
    e2 = Event(
        id="2",
        title="My Event",
        url="https://b",
        source="s",
        start=start,
        venue="Venue",
    )
    assert e1.fetched_at.tzinfo is not None
    assert e1.identity_key() == e2.identity_key()


def test_attrs_falsey_coercion_and_extra_fields_preserved():
    event = Event(
        id="1",
        title="t",
        url="https://a",
        source="s",
        attrs={"outdoor": "false", "live": 0, "rooftop": "No", "market": "yes"},
        extra_field="kept",  # extra="allow"
    )
    assert event.attrs["outdoor"] is False
    assert event.attrs["live"] is False
    assert event.attrs["rooftop"] is False
    assert event.attrs["market"] is True
    assert getattr(event, "extra_field", None) == "kept"


def test_url_edge_schemes_and_protocol_relative():
    e1 = Event(id="1", title="t", url="//example.com/x", source="s")
    assert str(e1.url).startswith("https://")
    e2 = Event(id="2", title="t", url="mailto:info@example.com", source="s")
    assert str(e2.url).startswith("mailto:")
