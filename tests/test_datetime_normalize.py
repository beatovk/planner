from bs4 import BeautifulSoup
from core.fetchers.timeout_bkk import TimeOutBKKFetcher
from core.fetchers.validator import ensure_events
from core.normalize.datetime import parse_date, parse_range, normalize_start_end

def test_parse_date_basic():
    """Test basic date parsing"""
    dt = parse_date("2024-01-15")
    assert dt is not None
    assert dt.year == 2024
    assert dt.month == 1
    assert dt.day == 15
    assert dt.tzinfo is not None
    assert str(dt.tzinfo) == "Asia/Bangkok"

def test_parse_date_relative():
    """Test relative date parsing"""
    dt = parse_date("tomorrow")
    assert dt is not None
    assert dt.tzinfo is not None

def test_parse_range_jan():
    """Test range parsing like '4–6 Jan' and 'Jan 4–6'"""
    start, end = parse_range("4–6 Jan")
    assert start is not None
    assert end is not None
    assert start.day == 4
    assert end.day == 6
    assert start.month == 1
    assert end.month == 1
    
    start2, end2 = parse_range("Jan 4–6")
    assert start2 is not None
    assert end2 is not None
    assert start2.day == 4
    assert end2.day == 6

def test_parse_range_end_of_month():
    """Test 'end of month' parsing"""
    start, end = parse_range("end of month")
    assert start is not None
    assert end is not None
    assert start.tzinfo is not None
    assert end.tzinfo is not None

def test_parse_range_every_friday():
    """Test 'every friday' parsing"""
    start, end = parse_range("every friday")
    assert start is not None
    assert end is not None
    assert start.tzinfo is not None
    assert end.tzinfo is not None

def test_normalize_start_end():
    """Test normalize_start_end function"""
    start, end, time_str = normalize_start_end("2024-01-15", "2024-01-16", None)
    assert start is not None
    assert end is not None
    assert start.tzinfo is not None
    assert end.tzinfo is not None

def test_fetcher_en_html():
    """Test integration through fetcher + ensure_events"""
    html = '''
    <html>
    <body>
        <article class="tile _article_osmln_1" data-start="2024-01-15" data-end="2024-01-16">
            <h3 class="_h3_c6c0h_1">Test Event</h3>
            <a href="/bangkok/event1">Event Link</a>
            <img class="_image_osmln_46" src="https://example.com/test.jpg">
            <div class="_summary_osmln_21">
                <p class="_p_1mmxl_1">Test description</p>
            </div>
            <time class="_time_1wpy4_1" datetime="2024-01-15T19:00:00">8:00 PM</time>
        </article>
    </body>
    </html>
    '''
    
    fetcher = TimeOutBKKFetcher()
    raw = fetcher._parse_page(html)
    assert len(raw) == 1
    
    event = raw[0]
    assert event["title"] == "Test Event"
    assert event["start"] is not None
    assert event["end"] is not None
    assert event["start"].tzinfo is not None
    assert str(event["start"].tzinfo) == "Asia/Bangkok"
    
    # интеграция через фетчер + ensure_events
    evs = ensure_events(raw, source_name=fetcher.name)
    assert evs[0].start.tzinfo is not None and str(evs[0].start.tzinfo) == "Asia/Bangkok"
