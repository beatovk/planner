from core.planner import build_week_cards_from_places, build_day_cards_from_places
from core.types import Place


def test_build_week_cards_from_places():
    """Тест генерации недельных карточек из mock данных"""
    places = [
        Place(
            id="1",
            name="Live Music Club",
            city="Bangkok",
            tags=["live music", "nightlife"],
            typical_time="evening",
            source="mock",
        ),
        Place(
            id="2",
            name="Street Food Market",
            city="Bangkok",
            tags=["street food", "market"],
            typical_time="day",
            source="mock",
        ),
        Place(
            id="3",
            name="Art Gallery",
            city="Bangkok",
            tags=["art", "exhibition"],
            typical_time="day",
            source="mock",
        ),
    ]

    result = build_week_cards_from_places(places, "Bangkok", ["music", "food"])

    # Проверяем структуру
    assert "days" in result
    assert "debug" in result
    assert len(result["days"]) == 7  # 7 дней недели

    # Проверяем, что есть события
    total_events = sum(len(day["items"]) for day in result["days"])
    assert total_events > 0

    # Проверяем debug информацию
    assert result["debug"]["live_count"] == 0
    assert result["debug"]["total_events"] == total_events


def test_build_day_cards_from_places():
    """Тест генерации дневных карточек из mock данных"""
    places = [
        Place(
            id="1",
            name="Live Music Club",
            city="Bangkok",
            tags=["live music", "nightlife"],
            typical_time="evening",
            source="mock",
        ),
        Place(
            id="2",
            name="Street Food Market",
            city="Bangkok",
            tags=["street food", "market"],
            typical_time="day",
            source="mock",
        ),
        Place(
            id="3",
            name="Art Gallery",
            city="Bangkok",
            tags=["art", "exhibition"],
            typical_time="day",
            source="mock",
        ),
    ]

    result = build_day_cards_from_places(
        places, "Bangkok", ["music", "food"], "2024-01-01"
    )

    # Проверяем структуру
    assert "date" in result
    assert "top3" in result
    assert "items" in result
    assert "debug" in result

    # Проверяем дату
    assert result["date"] == "2024-01-01"

    # Проверяем, что есть события
    assert len(result["items"]) > 0
    assert len(result["top3"]) > 0

    # Проверяем, что top3 это подмножество items
    assert all(top in result["items"] for top in result["top3"])

    # Проверяем debug информацию
    assert result["debug"]["live_count"] == 0
    assert result["debug"]["total_events"] == len(result["items"])


def test_cards_with_different_tags():
    """Тест генерации карточек с разными тегами"""
    places = [
        Place(
            id="1",
            name="Jazz Club",
            city="Bangkok",
            tags=["jazz", "music"],
            typical_time="evening",
            source="mock",
        ),
        Place(
            id="2",
            name="Thai Restaurant",
            city="Bangkok",
            tags=["thai food", "restaurant"],
            typical_time="day",
            source="mock",
        ),
        Place(
            id="3",
            name="Shopping Mall",
            city="Bangkok",
            tags=["shopping", "mall"],
            typical_time="day",
            source="mock",
        ),
    ]

    # Тест с тегом "music"
    music_result = build_day_cards_from_places(
        places, "Bangkok", ["music"], "2024-01-01"
    )
    assert len(music_result["items"]) > 0
    assert any("Jazz Club" in item["title"] for item in music_result["items"])

    # Тест с тегом "food"
    food_result = build_day_cards_from_places(places, "Bangkok", ["food"], "2024-01-01")
    assert len(food_result["items"]) > 0
    assert any("Thai Restaurant" in item["title"] for item in food_result["items"])

    # Тест с тегом "shopping"
    shopping_result = build_day_cards_from_places(
        places, "Bangkok", ["shopping"], "2024-01-01"
    )
    assert len(shopping_result["items"]) > 0
    assert any("Shopping Mall" in item["title"] for item in shopping_result["items"])


def test_cards_scoring():
    """Тест скоринга карточек"""
    places = [
        Place(
            id="1",
            name="Live Music Venue",
            city="Bangkok",
            tags=["live music"],
            typical_time="evening",
            source="mock",
        ),
        Place(
            id="2",
            name="Jazz Bar",
            city="Bangkok",
            tags=["jazz", "music"],
            typical_time="evening",
            source="mock",
        ),
        Place(
            id="3",
            name="General Bar",
            city="Bangkok",
            tags=["bar"],
            typical_time="evening",
            source="mock",
        ),
    ]

    result = build_day_cards_from_places(places, "Bangkok", ["music"], "2024-01-01")

    # Проверяем, что все события имеют score
    for item in result["items"]:
        assert "score" in item
        assert isinstance(item["score"], (int, float))

    # Проверяем, что события отсортированы по score (top3 должны быть первыми)
    items_scores = [item["score"] for item in result["items"]]
    top3_scores = [item["score"] for item in result["top3"]]

    # Top3 должны иметь максимальные скоры
    max_score = max(items_scores)
    assert max_score in top3_scores
