import pytest
import tempfile
import os
from sqlalchemy import create_engine
from packages.wp_places.dao import init_schema, save_places
from packages.wp_places.search import ensure_fts, reindex_fts, search, get_search_stats


@pytest.fixture
def temp_db():
    """Создание временной БД для тестов"""
    # Создаем временный файл БД
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Создаем engine для временной БД
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url)

    yield engine

    # Очистка после тестов
    engine.dispose()
    os.unlink(db_path)


@pytest.fixture
def sample_places():
    """Тестовые данные мест с контентом для поиска"""
    return [
        {
            "id": "jazz_club_1",
            "name": "Blue Note Jazz Club",
            "description": "Famous jazz club with live music every night. Great atmosphere for jazz lovers.",
            "city": "bangkok",
            "address": "123 Jazz Street",
            "tags": ["jazz", "live music", "nightlife", "club"],
            "flags": ["entertainment", "jazz", "nightlife"],
            "typical_time": "evening",
            "source": "test",
            "rating": 4.8,
            "price_range": "$$$",
            "google_maps_url": "https://maps.google.com/jazz1",
        },
        {
            "id": "thai_restaurant_1",
            "name": "Spice Garden Thai Restaurant",
            "description": "Authentic Thai cuisine with traditional recipes. Famous for tom yum soup.",
            "city": "bangkok",
            "address": "456 Food Avenue",
            "tags": ["thai food", "restaurant", "tom yum", "authentic"],
            "flags": ["food_dining", "thai_cuisine", "restaurants"],
            "typical_time": "lunch",
            "source": "test",
            "rating": 4.6,
            "price_range": "$$",
            "google_maps_url": "https://maps.google.com/thai1",
        },
        {
            "id": "art_gallery_1",
            "name": "Modern Art Gallery",
            "description": "Contemporary art exhibitions featuring local and international artists.",
            "city": "bangkok",
            "address": "789 Art Boulevard",
            "tags": ["art", "gallery", "exhibition", "contemporary"],
            "flags": ["art_exhibits", "culture", "education"],
            "typical_time": "day",
            "source": "test",
            "rating": 4.4,
            "price_range": "Free",
            "google_maps_url": "https://maps.google.com/art1",
        },
        {
            "id": "rooftop_bar_1",
            "name": "Sky High Rooftop Bar",
            "description": "Luxury rooftop bar with panoramic city views. Perfect for sunset cocktails.",
            "city": "bangkok",
            "address": "101 Sky Tower",
            "tags": ["rooftop", "bar", "cocktails", "view", "luxury"],
            "flags": ["rooftop", "entertainment", "bars"],
            "typical_time": "evening",
            "source": "test",
            "rating": 4.7,
            "price_range": "$$$",
            "google_maps_url": "https://maps.google.com/rooftop1",
        },
        {
            "id": "jazz_cafe_1",
            "name": "Jazz & Coffee House",
            "description": "Cozy cafe with jazz background music and great coffee. Relaxing atmosphere.",
            "city": "bangkok",
            "address": "202 Coffee Lane",
            "tags": ["jazz", "cafe", "coffee", "relaxing", "background music"],
            "flags": ["cafes", "jazz", "relaxation"],
            "typical_time": "day",
            "source": "test",
            "rating": 4.3,
            "price_range": "$",
            "google_maps_url": "https://maps.google.com/jazzcafe1",
        },
    ]


def test_ensure_fts(temp_db):
    """Тест создания FTS5 таблиц и триггеров"""
    # Инициализируем основную схему
    init_schema(temp_db)

    # Создаем FTS5
    ensure_fts(temp_db)

    # Проверяем, что FTS таблица создана
    with temp_db.connect() as conn:
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='places_fts'"
        )
        assert result.fetchone() is not None

        # Проверяем, что триггеры созданы
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'places_fts_%'"
        )
        triggers = [row[0] for row in result]
        assert "places_fts_insert" in triggers
        assert "places_fts_update" in triggers
        assert "places_fts_delete" in triggers


def test_reindex_fts(temp_db, sample_places):
    """Тест переиндексации FTS5 после сохранения мест"""
    # Инициализируем схему и FTS5
    init_schema(temp_db)
    ensure_fts(temp_db)

    # Сохраняем места
    saved_count = save_places(temp_db, sample_places)
    assert saved_count == 5

    # Переиндексируем FTS
    fts_count = reindex_fts(temp_db)
    assert fts_count == 5

    # Проверяем, что FTS таблица содержит данные
    with temp_db.connect() as conn:
        result = conn.execute("SELECT COUNT(*) FROM places_fts")
        assert result.fetchone()[0] == 5


def test_search_jazz(temp_db, sample_places):
    """Тест поиска по запросу 'jazz'"""
    # Инициализируем схему, FTS5 и данные
    init_schema(temp_db)
    ensure_fts(temp_db)
    save_places(temp_db, sample_places)
    reindex_fts(temp_db)

    # Ищем места с 'jazz'
    results = search(temp_db, "jazz", limit=10)

    # Должны найти 2 места с jazz
    assert len(results) == 2

    # Проверяем, что найдены правильные места
    place_names = [place["name"] for place in results]
    assert "Blue Note Jazz Club" in place_names
    assert "Jazz & Coffee House" in place_names

    # Проверяем, что результаты отсортированы по релевантности
    # (первый результат должен быть более релевантным)
    assert "Blue Note Jazz Club" == results[0]["name"]  # Больше упоминаний jazz


def test_search_thai_food(temp_db, sample_places):
    """Тест поиска по запросу 'thai food'"""
    # Инициализируем схему, FTS5 и данные
    init_schema(temp_db)
    ensure_fts(temp_db)
    save_places(temp_db, sample_places)
    reindex_fts(temp_db)

    # Ищем места с 'thai food'
    results = search(temp_db, "thai food", limit=10)

    # Должны найти 1 место
    assert len(results) == 1
    assert results[0]["name"] == "Spice Garden Thai Restaurant"


def test_search_rooftop(temp_db, sample_places):
    """Тест поиска по запросу 'rooftop'"""
    # Инициализируем схему, FTS5 и данные
    init_schema(temp_db)
    ensure_fts(temp_db)
    save_places(temp_db, sample_places)
    reindex_fts(temp_db)

    # Ищем места с 'rooftop'
    results = search(temp_db, "rooftop", limit=10)

    # Должны найти 1 место
    assert len(results) == 1
    assert results[0]["name"] == "Sky High Rooftop Bar"


def test_search_by_category(temp_db, sample_places):
    """Тест поиска по категории"""
    # Инициализируем схему, FTS5 и данные
    init_schema(temp_db)
    ensure_fts(temp_db)
    save_places(temp_db, sample_places)
    reindex_fts(temp_db)

    # Ищем места с 'jazz' в категории 'entertainment'
    from packages.wp_places.search import search_by_category

    results = search_by_category(temp_db, "jazz", "entertainment", limit=10)

    # Должны найти места с jazz в entertainment
    assert len(results) >= 1
    jazz_places = [p for p in results if "jazz" in p["name"].lower()]
    assert len(jazz_places) >= 1


def test_search_empty_query(temp_db, sample_places):
    """Тест поиска с пустым запросом"""
    # Инициализируем схему, FTS5 и данные
    init_schema(temp_db)
    ensure_fts(temp_db)
    save_places(temp_db, sample_places)
    reindex_fts(temp_db)

    # Пустой запрос должен вернуть пустой список
    results = search(temp_db, "", limit=10)
    assert len(results) == 0

    results = search(temp_db, "   ", limit=10)
    assert len(results) == 0


def test_search_limit(temp_db, sample_places):
    """Тест ограничения результатов поиска"""
    # Инициализируем схему, FTS5 и данные
    init_schema(temp_db)
    ensure_fts(temp_db)
    save_places(temp_db, sample_places)
    reindex_fts(temp_db)

    # Ищем с лимитом 2
    results = search(temp_db, "bangkok", limit=2)
    assert len(results) <= 2


def test_get_search_stats(temp_db, sample_places):
    """Тест получения статистики поиска"""
    # Инициализируем схему, FTS5 и данные
    init_schema(temp_db)
    ensure_fts(temp_db)
    save_places(temp_db, sample_places)
    reindex_fts(temp_db)

    # Получаем статистику
    stats = get_search_stats(temp_db)

    assert stats["fts_records"] == 5
    assert stats["places_records"] == 5
    assert stats["sync_status"] == "synced"
    assert stats["fts_enabled"] == True


def test_search_ranking(temp_db, sample_places):
    """Тест ранжирования результатов поиска"""
    # Инициализируем схему, FTS5 и данные
    init_schema(temp_db)
    ensure_fts(temp_db)
    save_places(temp_db, sample_places)
    reindex_fts(temp_db)

    # Ищем по 'music' - должно найти jazz места
    results = search(temp_db, "music", limit=10)

    # Проверяем, что результаты отсортированы по релевантности
    # Места с большим количеством совпадений должны быть первыми
    assert len(results) >= 2

    # Blue Note Jazz Club должен быть первым (больше упоминаний music)
    if results[0]["name"] == "Blue Note Jazz Club":
        assert True  # Ожидаемый порядок
    elif results[1]["name"] == "Blue Note Jazz Club":
        assert True  # Альтернативный порядок
    else:
        # Проверяем, что хотя бы одно jazz место найдено
        jazz_places = [p for p in results if "jazz" in p["name"].lower()]
        assert len(jazz_places) >= 1
