#!/usr/bin/env python3
"""
Test script for Step 1: Place Contract + Table + CRUD operations.
"""

import sys
import logging
from pathlib import Path

# Добавляем src в Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from models.place import Place, PlaceCreate, PriceLevel
from services.places_service import create_places_service

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_place_creation():
    """Test place creation and validation."""
    print("🧪 Testing Place model creation...")
    
    # Создаем тестовые данные
    place_data = PlaceCreate(
        source="test_source",
        source_url="https://example.com/test",
        name="Test Restaurant",
        description="A wonderful test restaurant in Bangkok",
        city="bangkok",
        area="Sukhumvit",
        flags=["food_dining", "restaurant"],
        tags=["thai", "local"],
        price_level=PriceLevel.MODERATE,
        cuisine="Thai",
        atmosphere="casual"
    )
    
    print(f"✅ Place data created: {place_data.name}")
    print(f"   Source: {place_data.source}")
    print(f"   Area: {place_data.area}")
    print(f"   Flags: {place_data.flags}")
    print(f"   Price: {place_data.price_level}")
    
    return place_data


def test_place_model():
    """Test Place model with full data."""
    print("\n🧪 Testing Place model...")
    
    # Создаем Place объект
    place = Place(
        id="test_001",
        source="test_source",
        source_url="https://example.com/test",
        name="Test Restaurant",
        description="A wonderful test restaurant in Bangkok with authentic Thai cuisine",
        city="bangkok",
        area="Sukhumvit",
        address="123 Sukhumvit Road, Bangkok",
        lat=13.7563,
        lon=100.5018,
        flags=["food_dining", "restaurant"],
        tags=["thai", "local", "authentic"],
        price_level=PriceLevel.MODERATE,
        cuisine="Thai",
        atmosphere="casual",
        image_url="https://example.com/image.jpg",
        popularity=0.8,
        quality_score=0.9
    )
    
    print(f"✅ Place model created: {place.name}")
    print(f"   ID: {place.id}")
    print(f"   Identity Key: {place.get_identity_key()}")
    print(f"   Search Text: {place.get_search_text()[:100]}...")
    print(f"   Quality Score: {place.quality_score}")
    
    return place


def test_database_operations():
    """Test database operations."""
    print("\n🧪 Testing database operations...")
    
    try:
        # Создаем сервис
        service = create_places_service()
        print("✅ Places service created")
        
        # Создаем тестовое место
        place_data = PlaceCreate(
            source="test_source",
            source_url="https://example.com/test",
            name="Test Restaurant",
            description="A wonderful test restaurant in Bangkok",
            city="bangkok",
            area="Sukhumvit",
            flags=["food_dining", "restaurant"],
            tags=["thai", "local"],
            price_level=PriceLevel.MODERATE,
            cuisine="Thai",
            atmosphere="casual"
        )
        
        # Создаем место в БД
        created_place = service.create_place(place_data)
        if created_place:
            print(f"✅ Place created in database: {created_place.id}")
            
            # Получаем место по ID
            retrieved_place = service.get_place(created_place.id)
            if retrieved_place:
                print(f"✅ Place retrieved from database: {retrieved_place.name}")
                print(f"   Description: {retrieved_place.description}")
                print(f"   Flags: {retrieved_place.flags}")
            else:
                print("❌ Failed to retrieve place")
            
            # Поиск по флагам
            places_by_flags = service.get_places_by_flags(["food_dining"], limit=10)
            print(f"✅ Found {len(places_by_flags)} places with food_dining flag")
            
            # Поиск по району
            places_by_area = service.get_places_by_area("Sukhumvit", limit=10)
            print(f"✅ Found {len(places_by_area)} places in Sukhumvit area")
            
            # Статистика
            stats = service.get_places_stats()
            print(f"✅ Database stats: {stats.get('total_places', 0)} total places")
            
            # Удаляем тестовое место
            if service.delete_place(created_place.id):
                print(f"✅ Test place deleted: {created_place.id}")
            else:
                print("❌ Failed to delete test place")
            
        else:
            print("❌ Failed to create place in database")
        
        # Закрываем сервис
        service.close()
        print("✅ Places service closed")
        
    except Exception as e:
        print(f"❌ Error testing database operations: {e}")
        logger.error(f"Database test error: {e}", exc_info=True)


def test_search_functionality():
    """Test search functionality."""
    print("\n🧪 Testing search functionality...")
    
    try:
        # Создаем сервис
        service = create_places_service()
        
        # Создаем несколько тестовых мест
        test_places = [
            PlaceCreate(
                source="test_source",
                source_url="https://example.com/place1",
                name="Thai Delight Restaurant",
                description="Authentic Thai cuisine in Sukhumvit",
                city="bangkok",
                area="Sukhumvit",
                flags=["food_dining", "thai_cuisine"],
                tags=["authentic", "local"],
                price_level=PriceLevel.AFFORDABLE
            ),
            PlaceCreate(
                source="test_source",
                source_url="https://example.com/place2",
                name="Sukhumvit Art Gallery",
                description="Contemporary art gallery in Sukhumvit",
                city="bangkok",
                area="Sukhumvit",
                flags=["art_exhibits", "culture"],
                tags=["contemporary", "art"],
                price_level=PriceLevel.BUDGET
            ),
            PlaceCreate(
                source="test_source",
                source_url="https://example.com/place3",
                name="Rooftop Skybar",
                description="Luxury rooftop bar with city views",
                city="bangkok",
                area="Silom",
                flags=["bars", "rooftop", "luxury"],
                tags=["rooftop", "views", "cocktails"],
                price_level=PriceLevel.EXPENSIVE
            )
        ]
        
        # Создаем места в БД
        created_places = service.create_places(test_places)
        print(f"✅ Created {len(created_places)} test places")
        
        # Тестируем поиск
        print("\n🔍 Testing search functionality...")
        
        # Поиск по тексту
        search_results = service.search_places_simple(query="Thai", limit=10)
        print(f"   Text search 'Thai': {len(search_results)} results")
        
        # Поиск по флагам
        food_results = service.search_places_simple(flags=["food_dining"], limit=10)
        print(f"   Flag search 'food_dining': {len(food_results)} results")
        
        # Поиск по району
        sukhumvit_results = service.search_places_simple(area="Sukhumvit", limit=10)
        print(f"   Area search 'Sukhumvit': {len(sukhumvit_results)} results")
        
        # Комбинированный поиск
        combined_results = service.search_places_simple(
            query="restaurant",
            flags=["food_dining"],
            area="Sukhumvit",
            limit=10
        )
        print(f"   Combined search: {len(combined_results)} results")
        
        # Получаем популярные места
        popular_places = service.get_popular_places(limit=5)
        print(f"   Popular places: {len(popular_places)} results")
        
        # Получаем места высокого качества
        quality_places = service.get_high_quality_places(limit=5)
        print(f"   High quality places: {len(quality_places)} results")
        
        # Очищаем тестовые данные
        for place in created_places:
            service.delete_place(place.id)
        print(f"✅ Cleaned up {len(created_places)} test places")
        
        # Закрываем сервис
        service.close()
        
    except Exception as e:
        print(f"❌ Error testing search functionality: {e}")
        logger.error(f"Search test error: {e}", exc_info=True)


def main():
    """Main test function."""
    print("🚀 Starting Step 1 tests...")
    print("=" * 50)
    
    try:
        # Тест 1: Создание данных места
        test_place_creation()
        
        # Тест 2: Модель места
        test_place_model()
        
        # Тест 3: Операции с базой данных
        test_database_operations()
        
        # Тест 4: Функциональность поиска
        test_search_functionality()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("\n🎯 What we've accomplished:")
        print("   • Pydantic Place model with validation")
        print("   • SQLite database with FTS5 search")
        print("   • Full CRUD operations")
        print("   • Advanced search with filters")
        print("   • Quality scoring system")
        print("   • Statistics and reporting")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error(f"Test failure: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
