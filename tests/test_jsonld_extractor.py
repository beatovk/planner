from core.extractors.jsonld import extract_events_from_jsonld


def test_image_string():
    html = """
    <script type="application/ld+json">
    {"@type":"Event","name":"ImgString","image":"http://example.com/a.jpg"}
    </script>
    """
    events = extract_events_from_jsonld(html)
    assert len(events) == 1
    assert events[0]["title"] == "ImgString"
    assert events[0]["image"] == "http://example.com/a.jpg"


def test_graph_mixed_types():
    html = """
    <script type="application/ld+json">
    {"@graph": [
      {"@type": "Organization", "name": "Org"},
      {"@type": "MusicEvent", "name": "Concert", "location": "Hall"}
    ]}
    </script>
    """
    events = extract_events_from_jsonld(html)
    assert len(events) == 1
    assert events[0]["title"] == "Concert"
    assert events[0]["venue"] == "Hall"


def test_empty_when_no_jsonld():
    assert extract_events_from_jsonld("<html></html>") == []
