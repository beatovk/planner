import pytest
import tempfile
import os
from sqlalchemy import create_engine
from packages.wp_places.dao import (
    init_schema,
    save_places,
    get_places_by_flags,
    get_all_places,
    get_places_stats,
    load_from_json,
)


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
    """Тестовые данные мест"""
    return [
        {
            "id": "place_1",
            "name": "Test Restaurant",
            "description": "A test restaurant",
            "city": "bangkok",
            "address": "123 Test St",
            "tags": ["food", "restaurant"],
            "flags": ["food_dining", "thai_cuisine"],
            "typical_time": "lunch",
            "source": "test",
            "rating": 4.5,
            "price_range": "$$",
            "google_maps_url": "https://maps.google.com/test1",
        },
        {
            "id": "place_2",
            "name": "Test Park",
            "description": "A test park",
            "city": "bangkok",
            "address": "456 Park Ave",
            "tags": ["park", "nature"],
            "flags": ["parks", "nature"],
            "typical_time": "day",
            "source": "test",
            "rating": 4.0,
            "price_range": "Free",
            "google_maps_url": "https://maps.google.com/test2",
        },
        {
            "id": "place_3",
            "name": "Test Museum",
            "description": "A test museum",
            "city": "bangkok",
            "address": "789 Museum Blvd",
            "tags": ["art", "museum"],
            "flags": ["art_exhibits", "culture"],
            "typical_time": "day",
            "source": "test",
            "rating": 4.8,
            "price_range": "$",
            "google_maps_url": "https://maps.google.com/test3",
        },
    ]


def test_init_schema(temp_db):
    """Тест инициализации схемы БД"""
    # Инициализируем схему
    init_schema(temp_db)

    # Проверяем, что таблица создана
    with temp_db.connect() as conn:
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='places'"
        )
        assert result.fetchone() is not None

        # Проверяем структуру таблицы
        result = conn.execute("PRAGMA table_info(places)")
        columns = {row[1] for row in result}
        expected_columns = {
            "id",
            "name",
            "description",
            "city",
            "address",
            "tags",
            "flags",
            "typical_time",
            "source",
            "rating",
            "price_range",
            "google_maps_url",
            "created_at",
            "updated_at",
        }
        assert expected_columns.issubset(columns)


def test_save_places(temp_db, sample_places):
    """Тест сохранения мест в БД"""
    # Инициализируем схему
    init_schema(temp_db)

    # Сохраняем места
    saved_count = save_places(temp_db, sample_places)
    assert saved_count == 3

    # Проверяем, что места сохранены
    with temp_db.connect() as conn:
        result = conn.execute("SELECT COUNT(*) FROM places")
        assert result.fetchone()[0] == 3

        # Проверяем конкретное место
        result = conn.execute(
            "SELECT name, city, rating FROM places WHERE id = 'place_1'"
        )
        row = result.fetchone()
        assert row[0] == "Test Restaurant"
        assert row[1] == "bangkok"
        assert row[2] == 4.5


def test_get_places_by_flags(temp_db, sample_places):
    """Тест получения мест по флагам"""
    # Инициализируем схему и сохраняем данные
    init_schema(temp_db)
    save_places(temp_db, sample_places)

    # Получаем места по флагам
    food_places = get_places_by_flags(temp_db, ["food_dining"], limit=10)
    assert len(food_places) == 1
    assert food_places[0]["name"] == "Test Restaurant"

    # Получаем места по нескольким флагам
    outdoor_places = get_places_by_flags(temp_db, ["parks", "nature"], limit=10)
    assert len(outdoor_places) == 1
    assert outdoor_places[0]["name"] == "Test Park"

    # Проверяем лимит
    all_places = get_places_by_flags(
        temp_db, ["food_dining", "parks", "art_exhibits"], limit=2
    )
    assert len(all_places) == 2


def test_get_all_places(temp_db, sample_places):
    """Тест получения всех мест"""
    # Инициализируем схему и сохраняем данные
    init_schema(temp_db)
    save_places(temp_db, sample_places)

    # Получаем все места
    all_places = get_all_places(temp_db, limit=10)
    assert len(all_places) == 3

    # Проверяем сортировку по рейтингу
    assert all_places[0]["rating"] == 4.8  # Museum
    assert all_places[1]["rating"] == 4.5  # Restaurant
    assert all_places[2]["rating"] == 4.0  # Park

    # Проверяем лимит
    limited_places = get_all_places(temp_db, limit=2)
    assert len(limited_places) == 2


def test_get_places_stats(temp_db, sample_places):
    """Тест получения статистики по местам"""
    # Инициализируем схему и сохраняем данные
    init_schema(temp_db)
    save_places(temp_db, sample_places)

    # Получаем статистику
    stats = get_places_stats(temp_db)

    assert stats["total_places"] == 3
    assert stats["cities"]["bangkok"] == 3
    assert stats["average_rating"] == 4.43  # (4.5 + 4.0 + 4.8) / 3
    assert "food_dining" in stats["flags_distribution"]
    assert "parks" in stats["flags_distribution"]
    assert "art_exhibits" in stats["flags_distribution"]


def test_load_from_json(temp_db, sample_places):
    """Тест загрузки мест из JSON"""
    # Инициализируем схему
    init_schema(temp_db)

    # Создаем временный JSON файл
    import json

    fd, json_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)

    try:
        with open(json_path, "w") as f:
            json.dump(sample_places, f)

        # Загружаем из JSON
        loaded_count = load_from_json(temp_db, json_path)
        assert loaded_count == 3

        # Проверяем, что места загружены
        all_places = get_all_places(temp_db, limit=10)
        assert len(all_places) == 3

    finally:
        os.unlink(json_path)


def test_update_existing_place(temp_db, sample_places):
    """Тест обновления существующего места"""
    # Инициализируем схему и сохраняем данные
    init_schema(temp_db)
    save_places(temp_db, sample_places)

    # Обновляем место
    updated_place = sample_places[0].copy()
    updated_place["rating"] = 5.0
    updated_place["description"] = "Updated description"

    save_places(temp_db, [updated_place])

    # Проверяем обновление
    with temp_db.connect() as conn:
        result = conn.execute(
            "SELECT rating, description FROM places WHERE id = 'place_1'"
        )
        row = result.fetchone()
        assert row[0] == 5.0
        assert row[1] == "Updated description"

        # Проверяем, что общее количество не изменилось
        result = conn.execute("SELECT COUNT(*) FROM places")
        assert result.fetchone()[0] == 3
