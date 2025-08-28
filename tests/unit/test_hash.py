from packages.wp_core.utils.hash import generate_etag, generate_weak_etag


def test_generate_etag_empty():
    """Тест ETag для пустого списка событий."""
    assert generate_etag([]) == '"empty"'


def test_generate_etag_single():
    """Тест ETag для одного события."""
    etag = generate_etag(["123"])
    assert etag.startswith('"') and etag.endswith('"')
    assert len(etag) == 34  # 32 hex chars + 2 quotes


def test_generate_etag_multiple():
    """Тест ETag для нескольких событий."""
    etag1 = generate_etag(["123", "456"])
    etag2 = generate_etag(["456", "123"])  # Порядок не должен влиять
    assert etag1 == etag2


def test_generate_etag_consistency():
    """Тест консистентности ETag для одинаковых данных."""
    events = ["123", "456", "789"]
    etag1 = generate_etag(events)
    etag2 = generate_etag(events)
    assert etag1 == etag2


def test_generate_weak_etag():
    """Тест слабого ETag."""
    weak_etag = generate_weak_etag(["123", "456"])
    assert weak_etag.startswith("W/")
    assert weak_etag[2:] == generate_etag(["123", "456"])[1:]  # Без кавычек
