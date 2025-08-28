from core.planner import find_candidates
from core.types import Place


def test_planner_with_smart_tag_matching():
    # Создаем тестовые места с составными тегами
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
        Place(
            id="4",
            name="Rooftop Bar",
            city="Bangkok",
            tags=["cocktails"],
            typical_time="evening",
            source="mock",
        ),
        Place(
            id="5",
            name="Outdoor Park",
            city="Bangkok",
            tags=["park"],
            typical_time="day",
            source="mock",
        ),
    ]

    # Тест 1: music должен найти live music club
    music_results = find_candidates(places, "Bangkok", ["music"])
    assert len(music_results) > 0
    assert any("Live Music Club" in p.name for p in music_results)

    # Тест 2: food должен найти street food market
    food_results = find_candidates(places, "Bangkok", ["food"])
    assert len(food_results) > 0
    assert any("Street Food Market" in p.name for p in food_results)

    # Тест 3: markets должен найти street food market
    markets_results = find_candidates(places, "Bangkok", ["markets"])
    assert len(markets_results) > 0
    assert any("Street Food Market" in p.name for p in markets_results)

    # Тест 4: art должен найти art gallery
    art_results = find_candidates(places, "Bangkok", ["art"])
    assert len(art_results) > 0
    assert any("Art Gallery" in p.name for p in art_results)

    # Тест 5: rooftop не должен найти ничего (нет в тегах)
    rooftop_results = find_candidates(places, "Bangkok", ["rooftop"])
    assert len(rooftop_results) == 0

    # Тест 6: outdoor не должен найти ничего (нет в тегах)
    outdoor_results = find_candidates(places, "Bangkok", ["outdoor"])
    assert len(outdoor_results) == 0


def test_planner_scoring_order():
    # Тест сортировки по скору
    places = [
        Place(
            id="1",
            name="Music Club",
            city="Bangkok",
            tags=["music"],
            typical_time="evening",
            source="mock",
        ),
        Place(
            id="2",
            name="Live Music Venue",
            city="Bangkok",
            tags=["live music"],
            typical_time="evening",
            source="mock",
        ),
        Place(
            id="3",
            name="Jazz Bar",
            city="Bangkok",
            tags=["jazz", "music"],
            typical_time="evening",
            source="mock",
        ),
    ]

    # Ищем по тегу "music" - должен вернуть в порядке убывания скора
    results = find_candidates(places, "Bangkok", ["music"])
    assert len(results) == 3

    # Jazz Bar должен быть первым (2 совпадения: jazz + music = скор 2)
    assert results[0].name == "Jazz Bar"

    # Live Music Venue должен быть вторым (точное совпадение фразы = скор 2)
    assert results[1].name == "Live Music Venue"

    # Music Club должен быть третьим (1 совпадение: music = скор 1)
    assert results[2].name == "Music Club"
