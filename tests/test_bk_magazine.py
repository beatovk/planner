import logging
from pathlib import Path

from core.fetchers.bk_magazine import BKMagazineFetcher
from tests.utils.html_loader import load_html
from core.fetchers.validator import ensure_events
from core.models import Event
from tests.utils.html_loader import load_html

SNAPSHOT_DIR = Path(__file__).resolve().parent / "fixtures" / "snapshots"


def _expected(name: str) -> int:
    return int((SNAPSHOT_DIR / name).read_text().strip())


def _collect_events(caplog):
    fetcher = BKMagazineFetcher()
    raw = []
    for page in range(1, 4):
        html = load_html(f"bk_magazine/page{page}.html")
        raw.extend(fetcher._parse_page(html))
    with caplog.at_level(logging.WARNING, logger="fetcher"):
        events = ensure_events(raw, source_name=fetcher.name)
    return events


def test_bk_magazine_parsing(caplog):
    events = _collect_events(caplog)
    assert len(events) == _expected("bk_magazine_count.txt")
    assert "Invalid event" in caplog.text
    for ev in events:
        assert isinstance(ev, Event)
        assert ev.title and ev.url and ev.source and ev.fetched_at
        assert str(ev.url).startswith("http")
        if ev.image:
            assert str(ev.image).startswith("http")

def test_jsonld_preferred_over_css():
    html = load_html("bk_magazine/page_jsonld.html")
    fetcher = BKMagazineFetcher()
    events = fetcher._parse_page(html)
    assert events[0]["title"] == "JSONLD BK Event"
    assert events[0]["venue"] == "JSONLD BK Venue"
    # в фикстуре og:image нет — image остаётся None или из JSON-LD, если задана

def test_image_priority_og_over_img():
    html = '''
    <html>
    <head>
        <meta property="og:image" content="http://example.com/og.jpg">
    </head>
    <body>
        <div class="event">
            <div class="title">Test Event</div>
            <img src="http://example.com/dom.jpg">
        </div>
    </body>
    </html>
    '''
    fetcher = BKMagazineFetcher()
    events = fetcher._parse_page(html)
    assert events[0]["image"] == "http://example.com/og.jpg"
