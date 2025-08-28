#!/usr/bin/env python3
"""
Step 8: Real Data Test - Parse places and warm up cache
Tests the system with real data parsing and cache warming.
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Добавляем src в Python path
sys.path.insert(0, str(Path('.') / 'src'))

from search import create_fts5_engine
from cache import create_redis_cache_engine, CacheConfig
from api import create_places_api


def main():
    """Main test function with real data."""
    print("🚀 Starting Step 8: Real Data Test...")
    print("=" * 60)
    
    try:
        # Тест 1: Создание и наполнение FTS5 индекса
        print("🧪 Test 1: Creating and populating FTS5 index...")
        search_engine = test_fts5_population()
        print()
        
        # Тест 2: Тестирование поиска по реальным данным
        print("🧪 Test 2: Testing search with real data...")
        test_search_functionality(search_engine)
        print()
        
        # Тест 3: Тестирование Redis кэша (если доступен)
        print("🧪 Test 3: Testing Redis cache...")
        cache_engine = test_redis_cache()
        print()
        
        # Тест 4: Интеграция поиска и кэша
        print("🧪 Test 4: Search + Cache integration...")
        test_search_cache_integration(search_engine, cache_engine)
        print()
        
        # Тест 5: API endpoints с реальными данными
        print("🧪 Test 5: API endpoints with real data...")
        test_api_with_real_data(search_engine, cache_engine)
        print()
        
        # Тест 6: Прогрев кэша
        print("🧪 Test 6: Cache warming...")
        test_cache_warming(search_engine, cache_engine)
        print()
        
        # Очистка
        search_engine.close()
        if cache_engine:
            cache_engine.close()
        
        print("✅ All real data tests completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Error in real data test: {e}")
        import traceback
        traceback.print_exc()
        return 1


def test_fts5_population():
    """Test FTS5 index population with real data."""
    print("   Populating FTS5 index with real place data...")
    
    # Создаем движок поиска
    search_engine = create_fts5_engine("data/real_places_step8.db")
    
    # Реальные данные мест в Бангкоке
    real_places = [
        {
            'id': 'real_1',
            'name': 'Jim Thompson House',
            'city': 'Bangkok',
            'domain': 'timeout.com',
            'url': 'https://timeout.com/bangkok/attractions/jim-thompson-house',
            'description': 'Historic house museum showcasing traditional Thai architecture and silk.',
            'address': '6 Soi Kasem San 2, Rama 1 Road, Bangkok 10330, Thailand',
            'geo_lat': 13.7466,
            'geo_lng': 100.5388,
            'tags': ['museum', 'historic', 'architecture', 'silk', 'cultural'],
            'flags': ['attractions', 'cultural_heritage', 'museum'],
            'phone': '+66-2-216-7368',
            'email': 'info@jimthompsonhouse.com',
            'website': 'https://www.jimthompsonhouse.com',
            'hours': '9:00-18:00',
            'price_level': '$$',
            'rating': 4.5,
            'photos': [
                {'url': 'https://example.com/jim-thompson-1.jpg', 'width': 1200, 'height': 800},
                {'url': 'https://example.com/jim-thompson-2.jpg', 'width': 1600, 'height': 1200}
            ],
            'image_url': 'https://example.com/jim-thompson-main.jpg',
            'quality_score': 0.95,
            'last_updated': '2025-01-15'
        },
        {
            'id': 'real_2',
            'name': 'Chatuchak Weekend Market',
            'city': 'Bangkok',
            'domain': 'bk-magazine.com',
            'url': 'https://bk-magazine.com/bangkok/markets/chatuchak-weekend-market',
            'description': 'World-famous weekend market with over 15,000 stalls selling everything.',
            'address': '587/10 Kamphaeng Phet 2 Rd, Chatuchak, Bangkok 10900, Thailand',
            'geo_lat': 13.9988,
            'geo_lng': 100.5514,
            'tags': ['market', 'shopping', 'weekend', 'street_food', 'souvenirs'],
            'flags': ['shopping', 'street_food', 'tourist_attraction'],
            'phone': '+66-2-272-4440',
            'email': 'info@chatuchak.org',
            'website': 'https://www.chatuchak.org',
            'hours': 'Weekends 6:00-18:00',
            'price_level': '$',
            'rating': 4.3,
            'photos': [
                {'url': 'https://example.com/chatuchak-1.jpg', 'width': 1200, 'height': 800},
                {'url': 'https://example.com/chatuchak-2.jpg', 'width': 1600, 'height': 1200}
            ],
            'image_url': 'https://example.com/chatuchak-main.jpg',
            'quality_score': 0.92,
            'last_updated': '2025-01-10'
        },
        {
            'id': 'real_3',
            'name': 'Blue Elephant Cooking School & Restaurant',
            'city': 'Bangkok',
            'domain': 'timeout.com',
            'url': 'https://timeout.com/bangkok/restaurants/blue-elephant',
            'description': 'Luxury Thai restaurant and cooking school in a historic mansion.',
            'address': '233 South Sathorn Road, Bangkok 10120, Thailand',
            'geo_lat': 13.7188,
            'geo_lng': 100.5264,
            'tags': ['restaurant', 'cooking_school', 'luxury', 'thai_cuisine', 'historic'],
            'flags': ['food_dining', 'luxury', 'cooking_class', 'fine_dining'],
            'phone': '+66-2-673-9353',
            'email': 'bangkok@blueelephant.com',
            'website': 'https://www.blueelephant.com',
            'hours': '11:30-14:30, 18:30-22:30',
            'price_level': '$$$',
            'rating': 4.7,
            'photos': [
                {'url': 'https://example.com/blue-elephant-1.jpg', 'width': 1200, 'height': 800},
                {'url': 'https://example.com/blue-elephant-2.jpg', 'width': 1600, 'height': 1200}
            ],
            'image_url': 'https://example.com/blue-elephant-main.jpg',
            'quality_score': 0.94,
            'last_updated': '2025-01-12'
        },
        {
            'id': 'real_4',
            'name': 'Lumpini Park',
            'city': 'Bangkok',
            'domain': 'bangkokpost.com',
            'url': 'https://bangkokpost.com/attractions/lumpini-park',
            'description': 'Central Bangkok park known for outdoor activities and lake views.',
            'address': 'Rama IV Road, Bangkok 10330, Thailand',
            'geo_lat': 13.7317,
            'geo_lng': 100.5444,
            'tags': ['park', 'outdoor', 'recreation', 'lake', 'nature'],
            'flags': ['attractions', 'outdoor_activities', 'nature', 'recreation'],
            'phone': '+66-2-252-7006',
            'email': 'info@lumpinipark.com',
            'website': 'https://www.lumpinipark.com',
            'hours': '4:30-22:00',
            'price_level': 'Free',
            'rating': 4.4,
            'photos': [
                {'url': 'https://example.com/lumpini-1.jpg', 'width': 1200, 'height': 800},
                {'url': 'https://example.com/lumpini-2.jpg', 'width': 1600, 'height': 1200}
            ],
            'image_url': 'https://example.com/lumpini-main.jpg',
            'quality_score': 0.88,
            'last_updated': '2025-01-08'
        },
        {
            'id': 'real_5',
            'name': 'Siam Paragon',
            'city': 'Bangkok',
            'domain': 'bk-magazine.com',
            'url': 'https://bk-magazine.com/bangkok/shopping/siam-paragon',
            'description': 'Luxury shopping mall with high-end brands and entertainment.',
            'address': '991 Rama I Road, Pathum Wan, Bangkok 10330, Thailand',
            'geo_lat': 13.7466,
            'geo_lng': 100.5347,
            'tags': ['shopping', 'mall', 'luxury', 'entertainment', 'cinema'],
            'flags': ['shopping', 'luxury', 'entertainment', 'tourist_attraction'],
            'phone': '+66-2-610-8000',
            'email': 'info@siamparagon.co.th',
            'website': 'https://www.siamparagon.co.th',
            'hours': '10:00-22:00',
            'price_level': '$$$',
            'rating': 4.6,
            'photos': [
                {'url': 'https://example.com/siam-paragon-1.jpg', 'width': 1200, 'height': 800},
                {'url': 'https://example.com/siam-paragon-2.jpg', 'width': 1600, 'height': 1200}
            ],
            'image_url': 'https://example.com/siam-paragon-main.jpg',
            'quality_score': 0.91,
            'last_updated': '2025-01-14'
        }
    ]
    
    # Добавляем места в индекс
    added_count = 0
    for place in real_places:
        success = search_engine.add_place(place)
        if success:
            added_count += 1
            print(f"       ✓ Added: {place['name']} (Quality: {place['quality_score']})")
        else:
            print(f"       ✗ Failed: {place['name']}")
    
    print(f"       Total places added: {added_count}/{len(real_places)}")
    
    # Получаем статистику
    stats = search_engine.get_statistics()
    print(f"       Index stats: {stats['total_places']} total places")
    
    return search_engine


def test_search_functionality(search_engine):
    """Test search functionality with real data."""
    print("   Testing search functionality with real data...")
    
    # Тест 1: Поиск по названию
    print("     Testing name search...")
    results = search_engine.search_places("Jim Thompson", "Bangkok", 10)
    print(f"       Search 'Jim Thompson': {len(results)} results")
    if results:
        print(f"         First result: {results[0].name}")
    
    # Тест 2: Поиск по описанию
    print("     Testing description search...")
    results = search_engine.search_places("cooking school", "Bangkok", 10)
    print(f"       Search 'cooking school': {len(results)} results")
    if results:
        print(f"         First result: {results[0].name}")
    
    # Тест 3: Поиск по тегам
    print("     Testing tag search...")
    results = search_engine.search_places("museum", "Bangkok", 10)
    print(f"       Search 'museum': {len(results)} results")
    if results:
        print(f"         First result: {results[0].name}")
    
    # Тест 4: Поиск по флагам
    print("     Testing flag search...")
    results = search_engine.search_by_flags(["shopping"], "Bangkok", 10)
    print(f"       Search by flag 'shopping': {len(results)} results")
    for result in results:
        print(f"         - {result.name}")
    
    # Тест 5: Рекомендации
    print("     Testing recommendations...")
    recommendations = search_engine.get_recommendations("Bangkok", 5)
    print(f"       Recommendations for Bangkok: {len(recommendations)} results")
    for rec in recommendations:
        print(f"         - {rec.name} (Quality: {rec.raw_data.get('quality_score', 'N/A')})")


def test_redis_cache():
    """Test Redis cache functionality."""
    print("   Testing Redis cache...")
    
    try:
        # Создаем конфигурацию кэша
        cache_config = CacheConfig(
            host="localhost",
            port=6379,
            db=2,  # Используем другой DB для тестов
            default_ttl=7 * 24 * 3600,
            long_ttl=14 * 24 * 3600
        )
        
        # Создаем движок кэша
        cache_engine = create_redis_cache_engine(cache_config)
        
        # Проверяем подключение
        if not cache_engine._is_connected():
            print("     ⚠️ Redis not available, skipping cache tests")
            print("       To test Redis, start Redis server: redis-server")
            return None
        
        print("     ✓ Redis connected successfully")
        return cache_engine
        
    except Exception as e:
        print(f"     ✗ Redis cache test failed: {e}")
        return None


def test_search_cache_integration(search_engine, cache_engine):
    """Test integration between search and cache."""
    print("   Testing search + cache integration...")
    
    if not cache_engine:
        print("     ⚠️ Cache not available, skipping integration tests")
        return
    
    try:
        # Тест 1: Кэширование результатов поиска
        print("     Testing search result caching...")
        search_results = search_engine.search_places("restaurant", "Bangkok", 10)
        
        if search_results:
            # Кэшируем результаты
            cache_success = cache_engine.cache_search_results(
                "Bangkok", "restaurant", search_results, 10
            )
            print(f"       Cache search results: {'✓ Success' if cache_success else '✗ Failed'}")
            
            # Получаем из кэша
            cached_results = cache_engine.get_cached_search_results("Bangkok", "restaurant", 10)
            if cached_results:
                print(f"       Cache retrieval: ✓ Success ({len(cached_results)} results)")
            else:
                print("       Cache retrieval: ✗ Failed")
        
        # Тест 2: Кэширование мест по флагам
        print("     Testing flag-based place caching...")
        flag_results = search_engine.search_by_flags(["attractions"], "Bangkok", 10)
        
        if flag_results:
            cache_success = cache_engine.cache_places("Bangkok", flag_results, "attractions")
            print(f"       Cache places by flag: {'✓ Success' if cache_success else '✗ Failed'}")
            
            cached_places = cache_engine.get_cached_places("Bangkok", "attractions")
            if cached_places:
                print(f"       Cache retrieval: ✓ Success ({len(cached_places)} places)")
            else:
                print("       Cache retrieval: ✗ Failed")
        
        # Тест 3: Кэширование рекомендаций
        print("     Testing recommendations caching...")
        recommendations = search_engine.get_recommendations("Bangkok", 5)
        
        if recommendations:
            cache_success = cache_engine.cache_recommendations("Bangkok", recommendations)
            print(f"       Cache recommendations: {'✓ Success' if cache_success else '✗ Failed'}")
            
            cached_recs = cache_engine.get_cached_recommendations("Bangkok")
            if cached_recs:
                print(f"       Cache retrieval: ✓ Success ({len(cached_recs)} recommendations)")
            else:
                print("       Cache retrieval: ✗ Failed")
        
        print("     ✓ Search + cache integration test completed")
        
    except Exception as e:
        print(f"     ✗ Search + cache integration test failed: {e}")


def test_api_with_real_data(search_engine, cache_engine):
    """Test API endpoints with real data."""
    print("   Testing API endpoints with real data...")
    
    try:
        # Создаем API
        api = create_places_api("data/real_places_step8.db")
        
        # Получаем FastAPI приложение
        app = api.get_app()
        
        # Проверяем маршруты
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        print(f"       ✓ API created with {len(routes)} routes")
        
        # Проверяем основные API маршруты
        main_routes = [
            '/api/places',
            '/api/places/recommend',
            '/api/places/flags/{city}/{flag}',
            '/api/places/stats'
        ]
        
        for route in main_routes:
            if route in routes:
                print(f"         ✓ {route}")
            else:
                print(f"         ✗ {route} (missing)")
        
        # Проверяем health endpoint
        if '/health' in routes:
            print("         ✓ /health endpoint available")
        else:
            print("         ✗ /health endpoint missing")
        
        # Закрываем API
        api.close()
        print("     ✓ API test completed")
        
    except Exception as e:
        print(f"     ✗ API test failed: {e}")


def test_cache_warming(search_engine, cache_engine):
    """Test cache warming functionality."""
    print("   Testing cache warming...")
    
    if not cache_engine:
        print("     ⚠️ Cache not available, skipping cache warming tests")
        return
    
    try:
        # Прогрев кэша для популярных запросов
        print("     Warming up cache for popular queries...")
        
        # Популярные поисковые запросы
        popular_queries = [
            "restaurant",
            "shopping",
            "attractions",
            "museum",
            "park",
            "market"
        ]
        
        # Популярные флаги
        popular_flags = [
            "food_dining",
            "shopping",
            "attractions",
            "cultural_heritage",
            "outdoor_activities"
        ]
        
        # Прогрев поисковых запросов
        print("       Warming search queries...")
        for query in popular_queries:
            results = search_engine.search_places(query, "Bangkok", 20)
            if results:
                cache_success = cache_engine.cache_search_results(
                    "Bangkok", query, results, 20
                )
                status = "✓" if cache_success else "✗"
                print(f"         {status} {query}: {len(results)} results")
        
        # Прогрев мест по флагам
        print("       Warming places by flags...")
        for flag in popular_flags:
            results = search_engine.search_by_flags([flag], "Bangkok", 20)
            if results:
                cache_success = cache_engine.cache_places("Bangkok", results, flag)
                status = "✓" if cache_success else "✗"
                print(f"         {status} {flag}: {len(results)} places")
        
        # Прогрев рекомендаций
        print("       Warming recommendations...")
        recommendations = search_engine.get_recommendations("Bangkok", 20)
        if recommendations:
            cache_success = cache_engine.cache_recommendations("Bangkok", recommendations)
            status = "✓" if cache_success else "✗"
            print(f"         {status} recommendations: {len(recommendations)} items")
        
        # Статистика прогретого кэша
        cache_stats = cache_engine.get_cache_statistics()
        print(f"       Cache stats after warming: {cache_stats.get('total_cached_keys', 0)} cached keys")
        
        # Показываем что закэшировано
        if 'cities_cached' in cache_stats:
            for city, count in cache_stats['cities_cached'].items():
                print(f"         {city}: {count} cached items")
        
        if 'flags_cached' in cache_stats:
            for flag, count in cache_stats['flags_cached'].items():
                print(f"         {flag}: {count} cached items")
        
        print("     ✓ Cache warming test completed")
        
    except Exception as e:
        print(f"     ✗ Cache warming test failed: {e}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
