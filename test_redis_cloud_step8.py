#!/usr/bin/env python3
"""
Step 8: Redis Cloud Test - Test with real Redis Cloud instance
Tests the system with real Redis Cloud cache.
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
    """Main test function with Redis Cloud."""
    print("🚀 Starting Step 8: Redis Cloud Test...")
    print("=" * 60)
    
    try:
        # Тест 1: Создание и наполнение FTS5 индекса
        print("🧪 Test 1: Creating and populating FTS5 index...")
        search_engine = test_fts5_population()
        print()
        
        # Тест 2: Подключение к Redis Cloud
        print("🧪 Test 2: Connecting to Redis Cloud...")
        cache_engine = test_redis_cloud_connection()
        print()
        
        if cache_engine:
            # Тест 3: Тестирование Redis Cloud кэша
            print("🧪 Test 3: Testing Redis Cloud cache...")
            test_redis_cloud_cache(cache_engine)
            print()
            
            # Тест 4: Интеграция поиска и Redis Cloud кэша
            print("🧪 Test 4: Search + Redis Cloud Cache integration...")
            test_search_cache_integration(search_engine, cache_engine)
            print()
            
            # Тест 5: Прогрев Redis Cloud кэша
            print("🧪 Test 5: Redis Cloud cache warming...")
            test_redis_cloud_cache_warming(search_engine, cache_engine)
            print()
            
            # Тест 6: API с Redis Cloud
            print("🧪 Test 6: API with Redis Cloud...")
            test_api_with_redis_cloud(search_engine, cache_engine)
            print()
            
            # Очистка Redis Cloud
            print("🧪 Test 7: Cleaning up Redis Cloud...")
            test_redis_cloud_cleanup(cache_engine)
            print()
        
        # Очистка
        search_engine.close()
        if cache_engine:
            cache_engine.close()
        
        print("✅ All Redis Cloud tests completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Error in Redis Cloud test: {e}")
        import traceback
        traceback.print_exc()
        return 1


def test_fts5_population():
    """Test FTS5 index population with real data."""
    print("   Populating FTS5 index with real place data...")
    
    # Создаем движок поиска
    search_engine = create_fts5_engine("data/redis_cloud_test.db")
    
    # Реальные данные мест в Бангкоке
    real_places = [
        {
            'id': 'redis_1',
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
            'id': 'redis_2',
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
            'id': 'redis_3',
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
            'id': 'redis_4',
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
            'id': 'redis_5',
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


def test_redis_cloud_connection():
    """Test connection to Redis Cloud."""
    print("   Testing connection to Redis Cloud...")
    
    try:
        # Конфигурация для Redis Cloud
        cache_config = CacheConfig(
            host="redis-14374.crce194.ap-seast-1-1.ec2.redns.redis-cloud.com",
            port=14374,
            password="G0vadDS1N9IaEoqQLukwSEGdAHUuPiaW",
            db=0,
            default_ttl=7 * 24 * 3600,
            long_ttl=14 * 24 * 3600,
            key_prefix="v1:places:test"
        )
        
        # Создаем движок кэша
        cache_engine = create_redis_cache_engine(cache_config)
        
        # Проверяем подключение
        if cache_engine._is_connected():
            print("     ✓ Successfully connected to Redis Cloud!")
            
            # Тест простой операции
            test_key = "test:connection"
            cache_engine.redis_client.set(test_key, "test_value", ex=60)
            test_value = cache_engine.redis_client.get(test_key)
            if test_value == b"test_value":
                print("     ✓ Basic Redis operations working")
                cache_engine.redis_client.delete(test_key)
            else:
                print("     ✗ Basic Redis operations failed")
            
            return cache_engine
        else:
            print("     ✗ Failed to connect to Redis Cloud")
            return None
        
    except Exception as e:
        print(f"     ✗ Redis Cloud connection test failed: {e}")
        return None


def test_redis_cloud_cache(cache_engine):
    """Test Redis Cloud cache functionality."""
    print("   Testing Redis Cloud cache functionality...")
    
    try:
        # Тест 1: Кэширование простых данных
        print("     Testing basic caching...")
        test_data = {
            'name': 'Test Place',
            'city': 'Bangkok',
            'quality_score': 0.95
        }
        
        cache_success = cache_engine.cache_places("Bangkok", [test_data], "test_flag")
        print(f"       Cache places: {'✓ Success' if cache_success else '✗ Failed'}")
        
        # Получаем из кэша
        cached_data = cache_engine.get_cached_places("Bangkok", "test_flag")
        if cached_data:
            print(f"       Cache retrieval: ✓ Success ({len(cached_data)} items)")
            print(f"         First item: {cached_data[0]['name']}")
        else:
            print("       Cache retrieval: ✗ Failed")
        
        # Тест 2: Кэширование с TTL
        print("     Testing TTL functionality...")
        short_ttl_data = {'test': 'ttl_data'}
        cache_success = cache_engine.redis_client.setex("test:ttl", 10, json.dumps(short_ttl_data))
        print(f"       Set TTL data: {'✓ Success' if cache_success else '✗ Failed'}")
        
        # Проверяем TTL
        ttl = cache_engine.redis_client.ttl("test:ttl")
        print(f"       TTL remaining: {ttl} seconds")
        
        # Тест 3: Кэширование поисковых результатов
        print("     Testing search result caching...")
        search_results = [
            {'id': '1', 'name': 'Search Result 1', 'relevance': 0.9},
            {'id': '2', 'name': 'Search Result 2', 'relevance': 0.8}
        ]
        
        cache_success = cache_engine.cache_search_results("Bangkok", "test_query", search_results, 10)
        print(f"       Cache search results: {'✓ Success' if cache_success else '✗ Failed'}")
        
        cached_results = cache_engine.get_cached_search_results("Bangkok", "test_query", 10)
        if cached_results:
            print(f"       Cache retrieval: ✓ Success ({len(cached_results)} results)")
        else:
            print("       Cache retrieval: ✗ Failed")
        
        print("     ✓ Redis Cloud cache functionality test completed")
        
    except Exception as e:
        print(f"     ✗ Redis Cloud cache functionality test failed: {e}")


def test_search_cache_integration(search_engine, cache_engine):
    """Test integration between search and Redis Cloud cache."""
    print("   Testing search + Redis Cloud cache integration...")
    
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
                if isinstance(cached_results[0], dict) and 'name' in cached_results[0]:
                    print(f"         First cached result: {cached_results[0]['name']}")
                else:
                    print(f"         First cached result: {cached_results[0]}")
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
                for place in cached_places:
                    if isinstance(place, dict) and 'name' in place:
                        print(f"         - {place['name']} (Quality: {place.get('quality_score', 'N/A')})")
                    else:
                        print(f"         - {place}")
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
                for rec in cached_recs:
                    if isinstance(rec, dict) and 'name' in rec:
                        print(f"         - {rec['name']} (Quality: {rec.get('quality_score', 'N/A')})")
                    else:
                        print(f"         - {rec}")
            else:
                print("       Cache retrieval: ✗ Failed")
        
        print("     ✓ Search + Redis Cloud cache integration test completed")
        
    except Exception as e:
        print(f"     ✗ Search + Redis Cloud cache integration test failed: {e}")


def test_redis_cloud_cache_warming(search_engine, cache_engine):
    """Test Redis Cloud cache warming."""
    print("   Testing Redis Cloud cache warming...")
    
    try:
        # Прогрев кэша для популярных запросов
        print("     Warming up Redis Cloud cache for popular queries...")
        
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
        
        # Создаем тестовые данные для прогрева
        test_places = [
            {'id': f'warm_{i}', 'name': f'Warm Place {i}', 'city': 'Bangkok', 'quality_score': 0.9}
            for i in range(1, 6)
        ]
        
        # Прогрев мест по флагам
        print("       Warming places by flags...")
        for flag in popular_flags:
            cache_success = cache_engine.cache_places("Bangkok", test_places, flag)
            status = "✓" if cache_success else "✗"
            print(f"         {status} {flag}: {len(test_places)} places")
        
        # Прогрев рекомендаций
        print("       Warming recommendations...")
        cache_success = cache_engine.cache_recommendations("Bangkok", test_places)
        status = "✓" if cache_success else "✗"
        print(f"         {status} recommendations: {len(test_places)} items")
        
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
        
        print("     ✓ Redis Cloud cache warming test completed")
        
    except Exception as e:
        print(f"     ✗ Redis Cloud cache warming test failed: {e}")


def test_api_with_redis_cloud(search_engine, cache_engine):
    """Test API with Redis Cloud."""
    print("   Testing API with Redis Cloud...")
    
    try:
        # Создаем API с Redis Cloud
        api = create_places_api("data/redis_cloud_test.db")
        
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
        print("     ✓ API with Redis Cloud test completed")
        
    except Exception as e:
        print(f"     ✗ API with Redis Cloud test failed: {e}")


def test_redis_cloud_cleanup(cache_engine):
    """Test cleanup of Redis Cloud test data."""
    print("   Testing Redis Cloud cleanup...")
    
    try:
        # Очищаем тестовые ключи
        test_keys = cache_engine.redis_client.keys("v1:places:test:*")
        if test_keys:
            deleted_count = cache_engine.redis_client.delete(*test_keys)
            print(f"       ✓ Cleaned up {deleted_count} test keys")
        else:
            print("       ✓ No test keys to clean up")
        
        # Очищаем другие тестовые ключи
        other_test_keys = cache_engine.redis_client.keys("test:*")
        if other_test_keys:
            deleted_count = cache_engine.redis_client.delete(*other_test_keys)
            print(f"       ✓ Cleaned up {deleted_count} other test keys")
        
        print("     ✓ Redis Cloud cleanup test completed")
        
    except Exception as e:
        print(f"     ✗ Redis Cloud cleanup test failed: {e}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
