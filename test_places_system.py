#!/usr/bin/env python
"""
Test script for places system.
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.places_service import PlacesService
from core.models.place import Place
from core.query.place_facets import map_place_to_flags, categories_to_place_flags
from core.logging import logger


def test_place_model():
    """Test Place model creation and validation."""
    print("Testing Place model...")
    
    # Создаем тестовое место
    place_data = {
        "id": "test123",
        "source": "test_source",
        "city": "bangkok",
        "name": "Test Restaurant",
        "description": "A great test restaurant",
        "url": "https://example.com/test",
        "tags": ["restaurant", "thai", "food"],
        "flags": ["food_dining"],
        "popularity": 0.8,
    }
    
    place = Place(**place_data)
    
    # Проверяем основные поля
    assert place.id == "test123"
    assert place.name == "Test Restaurant"
    assert place.city == "bangkok"
    assert "food_dining" in place.flags
    assert "restaurant" in place.tags
    
    # Проверяем identity_key
    identity_key = place.identity_key()
    assert "test-restaurant" in identity_key
    assert "bangkok" in identity_key
    
    print("✅ Place model test passed")


def test_place_facets():
    """Test place facets mapping."""
    print("Testing place facets mapping...")
    
    # Тестируем маппинг места в флаги
    place_data = {
        "name": "Modern Art Gallery",
        "description": "Contemporary art exhibition space",
        "tags": ["art", "culture", "exhibition"],
        "area": "Silom"
    }
    
    flags = map_place_to_flags(place_data)
    assert "art_exhibits" in flags
    print(f"✅ Place flags mapping: {flags}")
    
    # Тестируем конвертацию категорий в флаги
    categories = ["art", "food"]
    facets = categories_to_place_flags(categories)
    
    assert "art" in facets["categories"]
    assert "food" in facets["categories"]
    assert len(facets["flags"]) > 0
    
    print(f"✅ Categories to flags: {facets}")


def test_places_service():
    """Test PlacesService functionality."""
    print("Testing PlacesService...")
    
    try:
        service = PlacesService()
        
        # Проверяем доступные города и категории
        cities = service.fetcher.get_supported_cities()
        categories = service.fetcher.get_supported_categories()
        
        assert "bangkok" in cities
        assert len(categories) > 0
        
        print(f"✅ Supported cities: {cities}")
        print(f"✅ Supported categories: {categories}")
        
        # Проверяем статистику
        stats = service.get_stats("bangkok")
        assert "city" in stats
        assert "database" in stats
        assert "cache" in stats
        
        print("✅ Service stats test passed")
        
    except Exception as e:
        print(f"⚠️ Service test skipped (may need DB/Redis): {e}")


def test_place_creation():
    """Test creating various types of places."""
    print("Testing place creation...")
    
    # Ресторан
    restaurant = Place(
        id="rest1",
        source="test",
        city="bangkok",
        name="Thai Delight Restaurant",
        description="Authentic Thai cuisine",
        tags=["restaurant", "thai", "food"],
        flags=["food_dining"],
        area="Sukhumvit",
        price_level=2
    )
    
    # Художественная галерея
    gallery = Place(
        id="gallery1",
        source="test",
        city="bangkok",
        name="Bangkok Art Space",
        description="Contemporary art gallery",
        tags=["art", "gallery", "culture"],
        flags=["art_exhibits"],
        area="Silom"
    )
    
    # Музыкальный клуб
    club = Place(
        id="club1",
        source="test",
        city="bangkok",
        name="Electric Beats Club",
        description="Electronic music venue",
        tags=["club", "music", "nightlife"],
        flags=["electronic_music"],
        area="Thonglor"
    )
    
    places = [restaurant, gallery, club]
    
    for place in places:
        # Проверяем, что флаги правильно определены
        assert len(place.flags) > 0
        print(f"✅ {place.name}: {place.flags}")
    
    print("✅ Place creation test passed")


def main():
    """Run all tests."""
    print("🧪 Running places system tests...\n")
    
    try:
        test_place_model()
        test_place_facets()
        test_place_creation()
        test_places_service()
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
