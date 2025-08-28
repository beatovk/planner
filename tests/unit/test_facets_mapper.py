import pytest
from packages.wp_tags.facets import (
    categories_to_facets,
    fallback_flags,
    map_event_to_flags,
)


def test_categories_to_facets_mapping():
    """Тест маппинга категорий в фасеты."""

    # Тест для art_exhibits
    selected_ids = ["art_exhibits"]
    facets = categories_to_facets(selected_ids)

    assert "flags" in facets, "facets should contain 'flags' key"
    assert "categories" in facets, "facets should contain 'categories' key"

    # Проверяем что флаги не пустые
    flags = facets.get("flags", [])
    assert len(flags) > 0, f"flags should not be empty, got {flags}"

    # Проверяем что art_exhibits маппится в art
    assert "art" in flags, f"'art' should be in flags, got {flags}"

    # Проверяем что categories содержат исходные ID
    categories = facets.get("categories", [])
    assert (
        "art_exhibits" in categories
    ), f"'art_exhibits' should be in categories, got {categories}"


def test_fallback_flags_never_empty():
    """Тест что fallback_flags никогда не возвращает пустой набор."""

    # Тест с пустыми флагами
    selected_ids = ["art_exhibits"]
    facets = {"flags": [], "categories": selected_ids}

    flags = fallback_flags(selected_ids, facets)
    assert len(flags) > 0, f"fallback_flags should never return empty set, got {flags}"

    # Проверяем что fallback содержит "all" или другие флаги
    assert "all" in flags or any(
        flag in flags for flag in ["art", "culture"]
    ), f"fallback should contain meaningful flags, got {flags}"


def test_multiple_categories_mapping():
    """Тест маппинга нескольких категорий."""

    selected_ids = ["art_exhibits", "exhibitions", "culture"]
    facets = categories_to_facets(selected_ids)

    flags = facets.get("flags", [])
    assert (
        len(flags) > 0
    ), f"flags should not be empty for multiple categories, got {flags}"

    # Проверяем что art_exhibits и exhibitions маппятся в art
    assert "art" in flags, f"'art' should be in flags for art categories, got {flags}"

    # Проверяем что culture маппится в culture
    assert (
        "culture" in flags
    ), f"'culture' should be in flags for culture category, got {flags}"


def test_fallback_flags_with_valid_facets():
    """Тест fallback_flags когда фасеты уже содержат валидные флаги."""

    selected_ids = ["art_exhibits"]
    facets = {"flags": ["art", "culture"], "categories": selected_ids}

    flags = fallback_flags(selected_ids, facets)

    # Когда фасеты уже содержат флаги, fallback не должен их заменять
    assert "art" in flags, f"'art' should be preserved from facets, got {flags}"
    assert "culture" in flags, f"'culture' should be preserved from facets, got {flags}"

    # Проверяем что флаги не дублируются
    assert len(flags) == len(
        set(flags)
    ), f"flags should not contain duplicates, got {flags}"


def test_edge_cases():
    """Тест граничных случаев."""

    # Пустой список категорий
    facets = categories_to_facets([])
    assert facets["flags"] == set(), "Empty categories should result in empty flags set"
    assert (
        facets["categories"] == set()
    ), "Empty categories should result in empty categories set"

    # Неизвестные категории
    selected_ids = ["unknown_category"]
    facets = categories_to_facets(selected_ids)
    flags = fallback_flags(selected_ids, facets)
    assert len(flags) > 0, "Unknown categories should still result in non-empty flags"


def test_map_event_to_flags_art():
    """Тест маппинга арт-событий."""
    event = {
        "title": "Modern Art Exhibition",
        "description": "Contemporary art gallery featuring local artists",
        "tags": ["art", "culture", "exhibition"],
    }

    flags = map_event_to_flags(event)
    assert "art_exhibits" in flags, f"Art event should map to art_exhibits, got {flags}"
    assert len(flags) > 0, "Flags should not be empty for art event"


def test_map_event_to_flags_music():
    """Тест маппинга музыкальных событий."""
    event = {
        "title": "Jazz Night at Skybar",
        "description": "Live jazz music with rooftop views",
        "tags": ["music", "live", "jazz"],
    }

    flags = map_event_to_flags(event)
    assert "jazz_blues" in flags, f"Jazz event should map to jazz_blues, got {flags}"
    assert "rooftop" in flags, f"Rooftop event should map to rooftop, got {flags}"
    assert len(flags) >= 2, f"Music event should map to multiple flags, got {flags}"


def test_map_event_to_flags_food():
    """Тест маппинга фуд-событий."""
    event = {
        "title": "Thai Street Food Festival",
        "description": "Authentic Thai street food vendors",
        "tags": ["food", "thai", "street"],
    }

    flags = map_event_to_flags(event)
    assert "food_dining" in flags, f"Food event should map to food_dining, got {flags}"
    assert len(flags) > 0, "Flags should not be empty for food event"


def test_map_event_to_flags_multiple():
    """Тест маппинга событий с несколькими категориями."""
    event = {
        "title": "Art Workshop in the Park",
        "description": "Learn painting techniques in beautiful outdoor setting",
        "tags": ["art", "workshop", "outdoor", "learning"],
    }

    flags = map_event_to_flags(event)
    assert (
        "art_exhibits" in flags
    ), f"Art workshop should map to art_exhibits, got {flags}"
    assert "workshops" in flags, f"Workshop should map to workshops, got {flags}"
    assert "parks" in flags, f"Park event should map to parks, got {flags}"
    assert (
        len(flags) >= 3
    ), f"Multi-category event should map to multiple flags, got {flags}"


def test_map_event_to_flags_empty():
    """Тест маппинга событий без совпадений."""
    event = {
        "title": "Generic Event",
        "description": "No specific category keywords",
        "tags": ["general", "event"],
    }

    flags = map_event_to_flags(event)
    assert len(flags) == 0, f"Generic event should have no flags, got {flags}"


def test_map_event_to_flags_missing_fields():
    """Тест маппинга событий с отсутствующими полями."""
    event = {"title": "Art Show"}

    flags = map_event_to_flags(event)
    assert (
        "art_exhibits" in flags
    ), f"Art event should map to art_exhibits even with missing fields, got {flags}"


def test_map_event_to_flags_case_insensitive():
    """Тест что маппинг нечувствителен к регистру."""
    event = {
        "title": "ART GALLERY",
        "description": "EXHIBITION of modern ART",
        "tags": ["GALLERY", "MUSEUM"],
    }

    flags = map_event_to_flags(event)
    assert (
        "art_exhibits" in flags
    ), f"Uppercase art event should still map to art_exhibits, got {flags}"
