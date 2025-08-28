import logging
from pathlib import Path

from core.fetchers.timeout_bkk import TimeOutBKKFetcher
from core.fetchers.validator import ensure_events
from core.models import Event
from tests.utils.html_loader import load_html

SNAPSHOT_DIR = Path(__file__).resolve().parent / "fixtures" / "snapshots"


def _expected(name: str) -> int:
    return int((SNAPSHOT_DIR / name).read_text().strip())


def _collect_events(caplog):
    fetcher = TimeOutBKKFetcher()
    # Используем реальную HTML страницу
    try:
        html_path = Path(__file__).resolve().parent / "fixtures" / "html" / "real" / "timeout_bkk_events.html"
        if html_path.exists():
            html_content = html_path.read_text(encoding="utf-8")
            raw = fetcher._parse_page(html_content)
        else:
            # Fallback к старым фикстурам
            raw = []
            for page in range(1, 4):
                html = load_html(f"timeout_bkk/page{page}.html")
                raw.extend(fetcher._parse_page(html))
    except Exception as e:
        # Fallback к старым фикстурам
        raw = []
        for page in range(1, 4):
            html = load_html(f"timeout_bkk/page{page}.html")
            raw.extend(fetcher._parse_page(html))
    
    with caplog.at_level(logging.WARNING, logger="fetcher"):
        events = ensure_events(raw, source_name=fetcher.name)
    return events


def test_timeout_bkk_parsing(caplog):
    events = _collect_events(caplog)
    assert len(events) == _expected("timeout_bkk_count.txt")
    assert "Invalid event" in caplog.text
    for ev in events:
        assert isinstance(ev, Event)
        assert ev.title and ev.url and ev.source and ev.fetched_at
        assert str(ev.url).startswith("http")
        if ev.image:
            assert str(ev.image).startswith("http")

def test_jsonld_preferred_over_css():
    html = load_html("timeout_bkk/page_jsonld.html")
    fetcher = TimeOutBKKFetcher()
    events = fetcher._parse_page(html)
    assert events[0]["title"] == "JSONLD Timeout Event"
    assert events[0]["venue"] == "JSONLD Venue"
    # в фикстуре og:image нет — image остаётся None или из JSON-LD, если задана

def test_image_priority_og_over_img():
    html = '''
    <html>
    <head>
        <meta property="og:image" content="http://example.com/og.jpg">
    </head>
    <body>
        <article class="tile _article_osmln_1">
            <h3 class="_h3_c6c0h_1">Test Event</h3>
            <img class="_image_osmln_46" src="http://example.com/dom.jpg">
        </article>
    </body>
    </html>
    '''
    fetcher = TimeOutBKKFetcher()
    events = fetcher._parse_page(html)
    assert events[0]["image"] == "http://example.com/og.jpg"
