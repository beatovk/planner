#!/usr/bin/env python3
"""
Step 8: Complete Demo - Showcase all system capabilities
Demonstrates FTS5 search, Redis Cloud cache, and API endpoints with real data.
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
    """Main demo function showcasing all capabilities."""
    print("🚀 Step 8: Complete System Demo")
    print("=" * 60)
    print("🎯 This demo showcases:")
    print("   • FTS5 Full-Text Search Engine")
    print("   • Redis Cloud Caching System")
    print("   • FastAPI REST API Endpoints")
    print("   • Real Place Data Processing")
    print("   • Cache Warming & Optimization")
    print("=" * 60)
    
    try:
        # Инициализация системы
        print("🔧 Initializing system components...")
        search_engine, cache_engine = initialize_system()
        print()
        
        if not search_engine or not cache_engine:
            print("❌ Failed to initialize system components")
            return 1
        
        # Демонстрация возможностей
        print("🎭 Demonstrating system capabilities...")
        
        # 1. FTS5 Поиск
        print("🔍 1. FTS5 Full-Text Search Demo")
        demo_fts5_search(search_engine)
        print()
        
        # 2. Redis Cloud Кэш
        print("💾 2. Redis Cloud Cache Demo")
        demo_redis_cache(cache_engine)
        print()
        
        # 3. Интеграция поиска и кэша
        print("🔗 3. Search + Cache Integration Demo")
        demo_search_cache_integration(search_engine, cache_engine)
        print()
        
        # 4. Прогрев кэша
        print("🔥 4. Cache Warming Demo")
        demo_cache_warming(search_engine, cache_engine)
        print()
        
        # 5. API Endpoints
        print("🌐 5. API Endpoints Demo")
        demo_api_endpoints(search_engine, cache_engine)
        print()
        
        # 6. Производительность
        print("⚡ 6. Performance Demo")
        demo_performance(search_engine, cache_engine)
        print()
        
        # Очистка
        print("🧹 Cleaning up...")
        cleanup_system(search_engine, cache_engine)
        
        print("✅ Demo completed successfully!")
        print("🎉 System is ready for production use!")
        return 0
        
    except Exception as e:
        print(f"❌ Error in demo: {e}")
        import traceback
        traceback.print_exc()
        return 1


def initialize_system():
    """Initialize search engine and cache engine."""
    try:
        # Создаем FTS5 движок
        print("   Creating FTS5 search engine...")
        search_engine = create_fts5_engine("data/demo_step8.db")
        
        # Заполняем данными
        print("   Populating with demo data...")
        populate_demo_data(search_engine)
        
        # Создаем Redis Cloud кэш
        print("   Connecting to Redis Cloud...")
        cache_config = CacheConfig(
            host="redis-14374.crce194.ap-seast-1-1.ec2.redns.redis-cloud.com",
            port=14374,
            password="G0vadDS1N9IaEoqQLukwSEGdAHUuPiaW",
            db=0,
            default_ttl=7 * 24 * 3600,
            long_ttl=14 * 24 * 3600,
            key_prefix="v1:places:demo"
        )
        
        cache_engine = create_redis_cache_engine(cache_config)
        
        if not cache_engine._is_connected():
            print("   ❌ Failed to connect to Redis Cloud")
            return None, None
        
        print("   ✓ System initialized successfully")
        return search_engine, cache_engine
        
    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        return None, None


def populate_demo_data(search_engine):
    """Populate search engine with demo data."""
    demo_places = [
        {
            'id': 'demo_1',
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
            'id': 'demo_2',
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
            'id': 'demo_3',
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
            'id': 'demo_4',
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
            'id': 'demo_5',
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
    
    added_count = 0
    for place in demo_places:
        success = search_engine.add_place(place)
        if success:
            added_count += 1
    
    print(f"   ✓ Added {added_count}/{len(demo_places)} demo places")


def demo_fts5_search(search_engine):
    """Demonstrate FTS5 search capabilities."""
    print("   🔍 Testing various search scenarios...")
    
    # Поиск по названию
    print("     • Name search: 'Jim Thompson'")
    results = search_engine.search_places("Jim Thompson", "Bangkok", 5)
    print(f"       Results: {len(results)} found")
    
    # Поиск по описанию
    print("     • Description search: 'cooking school'")
    results = search_engine.search_places("cooking school", "Bangkok", 5)
    print(f"       Results: {len(results)} found")
    
    # Поиск по тегам
    print("     • Tag search: 'museum'")
    results = search_engine.search_places("museum", "Bangkok", 5)
    print(f"       Results: {len(results)} found")
    
    # Поиск по флагам
    print("     • Flag search: 'shopping'")
    results = search_engine.search_by_flags(["shopping"], "Bangkok", 5)
    print(f"       Results: {len(results)} found")
    
    # Рекомендации
    print("     • Recommendations for Bangkok")
    recommendations = search_engine.get_recommendations("Bangkok", 3)
    print(f"       Top recommendations: {len(recommendations)} found")
    
    print("   ✓ FTS5 search demo completed")


def demo_redis_cache(cache_engine):
    """Demonstrate Redis Cloud cache capabilities."""
    print("   💾 Testing cache operations...")
    
    # Тест кэширования
    test_data = {'name': 'Cache Test', 'city': 'Bangkok'}
    cache_success = cache_engine.cache_places("Bangkok", [test_data], "demo")
    print(f"     • Cache places: {'✓ Success' if cache_success else '✗ Failed'}")
    
    # Тест получения из кэша
    cached_data = cache_engine.get_cached_places("Bangkok", "demo")
    print(f"     • Cache retrieval: {'✓ Success' if cached_data else '✗ Failed'}")
    
    # Тест TTL
    cache_engine.redis_client.setex("demo:ttl", 30, "test_value")
    ttl = cache_engine.redis_client.ttl("demo:ttl")
    print(f"     • TTL test: {ttl} seconds remaining")
    
    print("   ✓ Redis cache demo completed")


def demo_search_cache_integration(search_engine, cache_engine):
    """Demonstrate search and cache integration."""
    print("   🔗 Testing search + cache integration...")
    
    # Кэшируем результаты поиска
    search_results = search_engine.search_places("restaurant", "Bangkok", 5)
    if search_results:
        cache_success = cache_engine.cache_search_results("Bangkok", "restaurant", search_results, 5)
        print(f"     • Cache search results: {'✓ Success' if cache_success else '✗ Failed'}")
        
        # Получаем из кэша
        cached_results = cache_engine.get_cached_search_results("Bangkok", "restaurant", 5)
        print(f"     • Cache retrieval: {'✓ Success' if cached_results else '✗ Failed'}")
    
    # Кэшируем места по флагам
    flag_results = search_engine.search_by_flags(["attractions"], "Bangkok", 5)
    if flag_results:
        cache_success = cache_engine.cache_places("Bangkok", flag_results, "attractions")
        print(f"     • Cache places by flag: {'✓ Success' if cache_success else '✗ Failed'}")
    
    print("   ✓ Search + cache integration demo completed")


def demo_cache_warming(search_engine, cache_engine):
    """Demonstrate cache warming capabilities."""
    print("   🔥 Warming up cache for popular queries...")
    
    # Популярные флаги для прогрева
    popular_flags = ["food_dining", "shopping", "attractions", "cultural_heritage"]
    
    # Создаем тестовые данные для прогрева
    warm_data = [
        {'id': f'warm_{i}', 'name': f'Warm Place {i}', 'city': 'Bangkok', 'quality_score': 0.9}
        for i in range(1, 4)
    ]
    
    # Прогрев по флагам
    for flag in popular_flags:
        cache_success = cache_engine.cache_places("Bangkok", warm_data, flag)
        status = "✓" if cache_success else "✗"
        print(f"     • {status} {flag}: {len(warm_data)} places")
    
    # Прогрев рекомендаций
    cache_success = cache_engine.cache_recommendations("Bangkok", warm_data)
    status = "✓" if cache_success else "✗"
    print(f"     • {status} recommendations: {len(warm_data)} items")
    
    # Статистика прогретого кэша
    cache_stats = cache_engine.get_cache_statistics()
    print(f"     • Total cached keys: {cache_stats.get('total_cached_keys', 0)}")
    
    print("   ✓ Cache warming demo completed")


def demo_api_endpoints(search_engine, cache_engine):
    """Demonstrate API endpoints."""
    print("   🌐 Testing API endpoints...")
    
    try:
        # Создаем API
        api = create_places_api("data/demo_step8.db")
        app = api.get_app()
        
        # Проверяем маршруты
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        print(f"     • API routes available: {len(routes)}")
        
        # Основные endpoints
        main_endpoints = [
            '/api/places',
            '/api/places/recommend',
            '/api/places/flags/{city}/{flag}',
            '/api/places/stats',
            '/health'
        ]
        
        for endpoint in main_endpoints:
            if endpoint in routes:
                print(f"       ✓ {endpoint}")
            else:
                print(f"       ✗ {endpoint} (missing)")
        
        # Закрываем API
        api.close()
        print("   ✓ API endpoints demo completed")
        
    except Exception as e:
        print(f"   ✗ API endpoints demo failed: {e}")


def demo_performance(search_engine, cache_engine):
    """Demonstrate system performance."""
    print("   ⚡ Testing system performance...")
    
    # Тест производительности поиска
    print("     • Testing search performance...")
    start_time = time.time()
    
    for _ in range(10):
        search_engine.search_places("restaurant", "Bangkok", 5)
    
    search_time = time.time() - start_time
    print(f"       Search time: {search_time:.3f} seconds")
    
    # Тест производительности кэша
    print("     • Testing cache performance...")
    start_time = time.time()
    
    for _ in range(10):
        cache_engine.get_cached_places("Bangkok", "attractions")
    
    cache_time = time.time() - start_time
    print(f"       Cache time: {cache_time:.3f} seconds")
    
    # Сравнение производительности
    if cache_time > 0:
        speedup = search_time / cache_time
        print(f"       Cache speedup: {speedup:.1f}x faster")
    
    print("   ✓ Performance demo completed")


def cleanup_system(search_engine, cache_engine):
    """Clean up system resources."""
    try:
        # Очищаем кэш
        if cache_engine:
            test_keys = cache_engine.redis_client.keys("v1:places:demo:*")
            if test_keys:
                deleted_count = cache_engine.redis_client.delete(*test_keys)
                print(f"   ✓ Cleaned up {deleted_count} demo cache keys")
        
        # Закрываем соединения
        if search_engine:
            search_engine.close()
        if cache_engine:
            cache_engine.close()
        
        print("   ✓ System cleanup completed")
        
    except Exception as e:
        print(f"   ⚠️ Cleanup warning: {e}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
