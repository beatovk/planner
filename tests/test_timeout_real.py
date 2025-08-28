import logging
from pathlib import Path
from core.fetchers.timeout_bkk import TimeOutBKKFetcher
from core.fetchers.validator import ensure_events
from core.models import Event


def test_timeout_real_page_parsing(caplog):
    """Тест парсинга реальной страницы TimeOut Bangkok"""
    fetcher = TimeOutBKKFetcher()

    # Загружаем реальную HTML страницу
    html_path = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "html"
        / "real"
        / "timeout_bkk_events.html"
    )
    if not html_path.exists():
        pytest.skip("Real HTML fixture not found")

    html_content = html_path.read_text(encoding="utf-8")

    # Парсим страницу
    raw_events = fetcher._parse_page(html_content)

    # Проверяем, что получили события
    assert len(raw_events) > 0, "Должны получить хотя бы одно событие"

    # Валидируем события
    with caplog.at_level(logging.WARNING, logger="fetcher"):
        events = ensure_events(raw_events, source_name=fetcher.name)

    # Проверяем, что все события прошли валидацию
    assert len(events) > 0, "Должны получить валидные события"

    # Проверяем структуру первого события
    first_event = events[0]
    assert isinstance(first_event, Event)
    assert first_event.title, "Заголовок должен быть заполнен"
    assert first_event.url, "URL должен быть заполнен"
    assert first_event.source == "timeout_bkk"

    # Проверяем, что есть теги
    if first_event.tags:
        print(f"Теги первого события: {first_event.tags}")

    # Проверяем, что есть описание
    if first_event.desc:
        print(f"Описание первого события: {first_event.desc[:100]}...")

    # Проверяем, что есть место проведения
    if first_event.venue:
        print(f"Место проведения: {first_event.venue}")

    print(f"Всего событий: {len(events)}")
    print(f"Первый заголовок: {first_event.title}")
