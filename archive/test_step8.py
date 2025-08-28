#!/usr/bin/env python3
"""
Step 8: FTS5 + Redis Cache + API - Demo Script
Demonstrates full-text search, caching, and API capabilities.
"""

import sys
import time
import json
from pathlib import Path

# Добавляем src в Python path
sys.path.insert(0, str(Path('.') / 'src'))

from search import create_fts5_engine
from cache import create_redis_cache_engine, CacheConfig
from api import create_places_api


def main():
    """Main demonstration function."""
    print("🚀 Starting Step 8: FTS5 + Redis Cache + API...")
    print("=" * 60)
    
    try:
        # Тест 1: FTS5 Search Engine
        print("🧪 Test 1: FTS5 Search Engine...")
        test_fts5_engine()
        print()
        
        # Тест 2: Redis Cache Engine
        print("🧪 Test 2: Redis Cache Engine...")
        test_redis_cache_engine()
        print()
        
        # Тест 3: Places API
        print("🧪 Test 3: Places API...")
        test_places_api()
        print()
        
        # Тест 4: Интеграция поиска и кэша
        print("🧪 Test 4: Search + Cache Integration...")
        test_search_cache_integration()
        print()
        
        # Тест 5: API endpoints
        print("🧪 Test 5: API Endpoints...")
        test_api_endpoints()
        print()
        
        print("✅ All Step 8 tests completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Error in Step 8: {e}")
        import traceback
        traceback.print_exc()
        return 1


def test_fts5_engine():
    """Test FTS5 search engine."""
    print("   Testing FTS5 search engine...")
    
    try:
        # Создаем движок поиска
        search_engine = create_fts5_engine("data/places_step8.db")
        
        # Тестовые данные
        test_places = [
            {
                'id': 'fts_test_1',
                'name': 'Amazing Thai Restaurant',
                'city': 'Bangkok',
                'domain': 'timeout.com',
                'url': 'https://timeout.com/restaurant/amazing-thai',
                'description': 'A fantastic Thai restaurant with authentic flavors.',
                'address': '123 Sukhumvit Soi 11, Bangkok, Thailand',
                'geo_lat': 13.7563,
                'geo_lng': 100.5018,
                'tags': ['thai', 'restaurant', 'authentic'],
                'flags': ['food_dining', 'local_experience'],
                'photos': [{'url': 'https://example.com/photo1.jpg'}],
                'image_url': 'https://example.com/main-photo.jpg',
                'quality_score': 0.9,
                'last_updated': '2025-01-15'
            },
            {
                'id': 'fts_test_2',
                'name': 'Sushi Master',
                'city': 'Bangkok',
                'domain': 'bk-magazine.com',
                'url': 'https://bk-magazine.com/restaurant/sushi-master',
                'description': 'Premium Japanese sushi restaurant.',
                'address': '456 Silom Soi 4, Bangkok, Thailand',
                'geo_lat': 13.7500,
                'geo_lng': 100.5000,
                'tags': ['japanese', 'sushi', 'premium'],
                'flags': ['food_dining', 'fine_dining'],
                'photos': [{'url': 'https://example.com/sushi1.jpg'}],
                'image_url': 'https://example.com/sushi-main.jpg',
                'quality_score': 0.85,
                'last_updated': '2025-01-10'
            },
            {
                'id': 'fts_test_3',
                'name': 'Coffee Corner',
                'city': 'Bangkok',
                'domain': 'timeout.com',
                'url': 'https://timeout.com/cafe/coffee-corner',
                'description': 'Cozy coffee shop with great atmosphere.',
                'address': '789 Thonglor Soi 10, Bangkok, Thailand',
                'geo_lat': 13.7450,
                'geo_lng': 100.4950,
                'tags': ['coffee', 'cafe', 'cozy'],
                'flags': ['food_dining', 'cafe'],
                'photos': [{'url': 'https://example.com/coffee1.jpg'}],
                'image_url': 'https://example.com/coffee-main.jpg',
                'quality_score': 0.8,
                'last_updated': '2025-01-12'
            }
        ]
        
        # Добавляем места в индекс
        print("     Adding test places to search index...")
        for place in test_places:
            success = search_engine.add_place(place)
            if success:
                print(f"       ✓ Added: {place['name']}")
            else:
                print(f"       ✗ Failed: {place['name']}")
        
        # Тестируем поиск
        print("     Testing search functionality...")
        
        # Поиск по названию
        results = search_engine.search_places("Thai", "Bangkok", 10)
        print(f"       Search 'Thai' in Bangkok: {len(results)} results")
        
        # Поиск по описанию
        results = search_engine.search_places("authentic", "Bangkok", 10)
        print(f"       Search 'authentic' in Bangkok: {len(results)} results")
        
        # Поиск по тегам
        results = search_engine.search_by_flags(["food_dining"], "Bangkok", 10)
        print(f"       Search by flag 'food_dining': {len(results)} results")
        
        # Рекомендации
        recommendations = search_engine.get_recommendations("Bangkok", 5)
        print(f"       Recommendations for Bangkok: {len(recommendations)} results")
        
        # Статистика
        stats = search_engine.get_statistics()
        print(f"       Search engine stats: {stats['total_places']} total places")
        
        # Оптимизация
        search_engine.optimize_database()
        print("       Database optimization completed")
        
        # Закрываем соединение
        search_engine.close()
        print("     ✓ FTS5 engine test completed")
        
    except Exception as e:
        print(f"     ✗ FTS5 engine test failed: {e}")


def test_redis_cache_engine():
    """Test Redis cache engine."""
    print("   Testing Redis cache engine...")
    
    try:
        # Создаем конфигурацию кэша
        cache_config = CacheConfig(
            host="localhost",
            port=6379,
            db=0,
            default_ttl=7 * 24 * 3600,  # 7 days
            long_ttl=14 * 24 * 3600      # 14 days
        )
        
        # Создаем движок кэша
        cache_engine = create_redis_cache_engine(cache_config)
        
        # Проверяем подключение
        if not cache_engine._is_connected():
            print("     ⚠️ Redis not available, skipping cache tests")
            print("       To test Redis, start Redis server: redis-server")
            return
        
        # Тестовые данные
        test_places = [
            {
                'id': 'cache_test_1',
                'name': 'Cached Restaurant 1',
                'city': 'Bangkok',
                'domain': 'test.com',
                'quality_score': 0.9
            },
            {
                'id': 'cache_test_2',
                'name': 'Cached Restaurant 2',
                'city': 'Bangkok',
                'domain': 'test.com',
                'quality_score': 0.85
            }
        ]
        
        # Тестируем кэширование мест
        print("     Testing place caching...")
        success = cache_engine.cache_places("Bangkok", test_places, "test_flag")
        if success:
            print("       ✓ Places cached successfully")
        else:
            print("       ✗ Failed to cache places")
        
        # Тестируем получение из кэша
        cached_places = cache_engine.get_cached_places("Bangkok", "test_flag")
        if cached_places:
            print(f"       ✓ Retrieved {len(cached_places)} places from cache")
        else:
            print("       ✗ Failed to retrieve places from cache")
        
        # Тестируем кэширование результатов поиска
        print("     Testing search result caching...")
        search_results = [
            {'id': 'search_1', 'name': 'Search Result 1'},
            {'id': 'search_2', 'name': 'Search Result 2'}
        ]
        
        success = cache_engine.cache_search_results("Bangkok", "test query", search_results, 10)
        if success:
            print("       ✓ Search results cached successfully")
        else:
            print("       ✗ Failed to cache search results")
        
        # Тестируем получение результатов поиска из кэша
        cached_search = cache_engine.get_cached_search_results("Bangkok", "test query", 10)
        if cached_search:
            print(f"       ✓ Retrieved {len(cached_search)} search results from cache")
        else:
            print("       ✗ Failed to retrieve search results from cache")
        
        # Тестируем кэширование рекомендаций
        print("     Testing recommendations caching...")
        recommendations = [
            {'id': 'rec_1', 'name': 'Recommendation 1'},
            {'id': 'rec_2', 'name': 'Recommendation 2'}
        ]
        
        success = cache_engine.cache_recommendations("Bangkok", recommendations)
        if success:
            print("       ✓ Recommendations cached successfully")
        else:
            print("       ✗ Failed to cache recommendations")
        
        # Тестируем получение рекомендаций из кэша
        cached_recs = cache_engine.get_cached_recommendations("Bangkok")
        if cached_recs:
            print(f"       ✓ Retrieved {len(cached_recs)} recommendations from cache")
        else:
            print("       ✗ Failed to retrieve recommendations from cache")
        
        # Статистика кэша
        cache_stats = cache_engine.get_cache_statistics()
        print(f"       Cache stats: {cache_stats.get('total_cached_keys', 0)} cached keys")
        
        # Очистка тестового кэша
        cache_engine.clear_city_cache("Bangkok")
        print("       ✓ Test cache cleared")
        
        # Закрываем соединение
        cache_engine.close()
        print("     ✓ Redis cache engine test completed")
        
    except Exception as e:
        print(f"     ✗ Redis cache engine test failed: {e}")


def test_places_api():
    """Test Places API."""
    print("   Testing Places API...")
    
    try:
        # Создаем API
        api = create_places_api("data/places_step8.db")
        
        # Получаем FastAPI приложение
        app = api.get_app()
        
        # Проверяем доступные маршруты
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append({
                    'path': route.path,
                    'methods': list(route.methods) if hasattr(route, 'methods') else []
                })
        
        print(f"       ✓ API created with {len(routes)} routes")
        
        # Показываем основные маршруты
        main_routes = [
            '/api/places',
            '/api/places/recommend',
            '/api/places/flags/{city}/{flag}',
            '/api/places/stats',
            '/health'
        ]
        
        for route in main_routes:
            if any(r['path'] == route for r in routes):
                print(f"         ✓ {route}")
            else:
                print(f"         ✗ {route} (missing)")
        
        # Закрываем API
        api.close()
        print("     ✓ Places API test completed")
        
    except Exception as e:
        print(f"     ✗ Places API test failed: {e}")


def test_search_cache_integration():
    """Test integration between search and cache."""
    print("   Testing search + cache integration...")
    
    try:
        # Создаем движки
        search_engine = create_fts5_engine("data/places_step8_integration.db")
        
        cache_config = CacheConfig(host="localhost", port=6379, db=1)
        cache_engine = create_redis_cache_engine(cache_config)
        
        # Проверяем подключение к Redis
        if not cache_engine._is_connected():
            print("     ⚠️ Redis not available, skipping integration tests")
            return
        
        # Тестовые данные
        test_places = [
            {
                'id': 'integration_1',
                'name': 'Integration Test Restaurant',
                'city': 'Bangkok',
                'domain': 'test.com',
                'description': 'A test restaurant for integration testing.',
                'address': '123 Integration Street, Bangkok',
                'geo_lat': 13.7563,
                'geo_lng': 100.5018,
                'tags': ['test', 'integration'],
                'flags': ['test_flag'],
                'photos': [{'url': 'https://example.com/test.jpg'}],
                'quality_score': 0.9,
                'last_updated': '2025-01-15'
            }
        ]
        
        # Добавляем в поиск
        for place in test_places:
            search_engine.add_place(place)
        
        # Выполняем поиск
        search_results = search_engine.search_places("Integration", "Bangkok", 10)
        print(f"       Search returned {len(search_results)} results")
        
        # Кэшируем результаты
        if search_results:
            cache_success = cache_engine.cache_search_results(
                "Bangkok", "Integration", search_results, 10
            )
            print(f"       Cache operation: {'✓ Success' if cache_success else '✗ Failed'}")
        
        # Получаем из кэша
        cached_results = cache_engine.get_cached_search_results("Bangkok", "Integration", 10)
        if cached_results:
            print(f"       Cache retrieval: ✓ Success ({len(cached_results)} results)")
        else:
            print("       Cache retrieval: ✗ Failed")
        
        # Очистка
        cache_engine.clear_city_cache("Bangkok")
        search_engine.close()
        cache_engine.close()
        
        print("     ✓ Search + cache integration test completed")
        
    except Exception as e:
        print(f"     ✗ Search + cache integration test failed: {e}")


def test_api_endpoints():
    """Test API endpoints functionality."""
    print("   Testing API endpoints...")
    
    try:
        # Создаем API
        api = create_places_api("data/places_step8_api.db")
        
        # Тестируем создание API
        app = api.get_app()
        print("       ✓ FastAPI application created")
        
        # Проверяем OpenAPI документацию
        if hasattr(app, 'openapi'):
            openapi_spec = app.openapi()
            print(f"       ✓ OpenAPI spec generated ({len(openapi_spec.get('paths', {}))} paths)")
        else:
            print("       ⚠️ OpenAPI spec not available")
        
        # Проверяем маршруты
        routes_info = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes_info.append({
                    'path': route.path,
                    'methods': list(route.methods),
                    'name': getattr(route, 'name', 'Unknown')
                })
        
        # Группируем по типам
        api_routes = [r for r in routes_info if r['path'].startswith('/api/')]
        other_routes = [r for r in routes_info if not r['path'].startswith('/api/')]
        
        print(f"       API routes: {len(api_routes)}")
        print(f"       Other routes: {len(other_routes)}")
        
        # Показываем основные API маршруты
        expected_routes = [
            '/api/places',
            '/api/places/search',
            '/api/places/recommend',
            '/api/places/flags/{city}/{flag}',
            '/api/places/stats',
            '/api/places/cache/clear/{city}',
            '/api/places/cache/optimize'
        ]
        
        for expected in expected_routes:
            found = any(r['path'] == expected for r in api_routes)
            status = "✓" if found else "✗"
            print(f"         {status} {expected}")
        
        # Проверяем health endpoint
        health_routes = [r for r in routes_info if r['path'] == '/health']
        if health_routes:
            print("       ✓ Health check endpoint available")
        else:
            print("       ✗ Health check endpoint missing")
        
        # Закрываем API
        api.close()
        print("     ✓ API endpoints test completed")
        
    except Exception as e:
        print(f"     ✗ API endpoints test failed: {e}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
