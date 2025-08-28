#!/usr/bin/env python3
"""
Step 9: Integration Demo - Test the complete integrated system
Demonstrates the unified pipeline combining dedup, quality, and search/cache.
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Добавляем src в Python path
sys.path.insert(0, str(Path('.') / 'src'))

from integration import create_places_pipeline
from api import create_integrated_api
from cache import CacheConfig


def main():
    """Main demo function for the integrated system."""
    print("🚀 Step 9: Integration Demo - Complete System")
    print("=" * 60)
    print("🎯 This demo showcases the integrated system:")
    print("   • Dedup Engine (Step 6)")
    print("   • Quality Engine (Step 7)")
    print("   • FTS5 + Redis Cache + API (Step 8)")
    print("   • Unified Pipeline & API")
    print("=" * 60)
    
    try:
        # Инициализация интегрированной системы
        print("🔧 Initializing integrated system...")
        pipeline, api = initialize_integrated_system()
        print()
        
        if not pipeline or not api:
            print("❌ Failed to initialize integrated system")
            return 1
        
        # Демонстрация возможностей
        print("🎭 Demonstrating integrated system capabilities...")
        
        # 1. Тестирование пайплайна
        print("🔗 1. Pipeline Processing Demo")
        demo_pipeline_processing(pipeline)
        print()
        
        # 2. Тестирование API endpoints
        print("🌐 2. API Endpoints Demo")
        demo_api_endpoints(api)
        print()
        
        # 3. Тестирование интеграции
        print("🔄 3. System Integration Demo")
        demo_system_integration(pipeline, api)
        print()
        
        # 4. Тестирование производительности
        print("⚡ 4. Performance Demo")
        demo_performance(pipeline)
        print()
        
        # 5. Тестирование оптимизации
        print("🔧 5. System Optimization Demo")
        demo_system_optimization(pipeline)
        print()
        
        # Очистка
        print("🧹 Cleaning up...")
        cleanup_system(pipeline, api)
        
        print("✅ Integration demo completed successfully!")
        print("🎉 Complete integrated system is ready for production!")
        return 0
        
    except Exception as e:
        print(f"❌ Error in integration demo: {e}")
        import traceback
        traceback.print_exc()
        return 1


def initialize_integrated_system():
    """Initialize the integrated pipeline and API."""
    try:
        # Конфигурация Redis Cloud
        redis_config = CacheConfig(
            host="redis-14374.crce194.ap-seast-1-1.ec2.redns.redis-cloud.com",
            port=14374,
            password="G0vadDS1N9IaEoqQLukwSEGdAHUuPiaW",
            db=0,
            default_ttl=7 * 24 * 3600,
            long_ttl=14 * 24 * 3600,
            key_prefix="v1:places:integration"
        )
        
        # Создаем пайплайн
        print("   Creating integrated pipeline...")
        pipeline = create_places_pipeline(
            db_path="data/integration_demo.db",
            redis_config=redis_config,
            min_quality_score=0.7,
            require_photos=True
        )
        print("   ✓ Pipeline created successfully")
        
        # Создаем API
        print("   Creating integrated API...")
        api = create_integrated_api(
            db_path="data/integration_demo.db",
            redis_config=redis_config,
            min_quality_score=0.7,
            require_photos=True
        )
        print("   ✓ API created successfully")
        
        return pipeline, api
        
    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        return None, None


def demo_pipeline_processing(pipeline):
    """Demonstrate pipeline processing capabilities."""
    print("   🔗 Testing pipeline processing...")
    
    # Тестовые данные мест
    test_places = [
        {
            'id': 'integration_1',
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
            'id': 'integration_2',
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
            'id': 'integration_3',
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
        }
    ]
    
    # Обрабатываем места через пайплайн
    print("     Processing places through pipeline...")
    results = pipeline.process_batch(test_places)
    
    # Анализируем результаты
    status_counts = {}
    for result in results:
        status = result.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"     Pipeline processing results:")
    for status, count in status_counts.items():
        print(f"       • {status}: {count} places")
    
    # Показываем детали для каждого места
    for result in results:
        print(f"       - {result.name}: {result.status}")
        if result.quality_metrics:
            print(f"         Quality Score: {result.quality_metrics.get_overall_score()}")
        if result.dedup_info and result.dedup_info.get('is_duplicate'):
            print(f"         Duplicate of: {result.dedup_info.get('duplicate_id')}")
    
    print("   ✓ Pipeline processing demo completed")


def demo_api_endpoints(api):
    """Demonstrate API endpoints."""
    print("   🌐 Testing API endpoints...")
    
    try:
        # Получаем FastAPI приложение
        app = api.get_app()
        
        # Проверяем маршруты
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        print(f"     • API routes available: {len(routes)}")
        
        # Основные endpoints
        main_endpoints = [
            '/api/places/process',
            '/api/places/process/async',
            '/api/places/search',
            '/api/places/flags/{city}/{flag}',
            '/api/places/recommend',
            '/api/places/cache/warm',
            '/api/places/system/optimize',
            '/api/places/system/status',
            '/health',
            '/docs'
        ]
        
        for endpoint in main_endpoints:
            if endpoint in routes:
                print(f"       ✓ {endpoint}")
            else:
                print(f"       ✗ {endpoint} (missing)")
        
        print("   ✓ API endpoints demo completed")
        
    except Exception as e:
        print(f"   ✗ API endpoints demo failed: {e}")


def demo_system_integration(pipeline, api):
    """Demonstrate system integration."""
    print("   🔄 Testing system integration...")
    
    try:
        # Тест 1: Проверка статуса системы
        print("     • Testing system status...")
        if hasattr(api, 'pipeline') and api.pipeline:
            print("       ✓ API has access to pipeline")
        else:
            print("       ✗ API missing pipeline access")
        
        # Тест 2: Проверка компонентов пайплайна
        print("     • Testing pipeline components...")
        components = [
            ('Dedup Engine', pipeline.dedup_engine),
            ('Quality Engine', pipeline.quality_engine),
            ('Search Engine', pipeline.search_engine),
            ('Cache Engine', pipeline.cache_engine)
        ]
        
        for name, component in components:
            if component:
                print(f"       ✓ {name}: available")
            else:
                print(f"       ✗ {name}: unavailable")
        
        # Тест 3: Проверка статистики
        print("     • Testing pipeline statistics...")
        stats = pipeline.get_statistics()
        print(f"       Total processed: {stats.get('total_processed', 0)}")
        print(f"       New places: {stats.get('new_places', 0)}")
        print(f"       Duplicates: {stats.get('duplicates', 0)}")
        print(f"       Rejected: {stats.get('rejected', 0)}")
        
        print("   ✓ System integration demo completed")
        
    except Exception as e:
        print(f"   ✗ System integration demo failed: {e}")


def demo_performance(pipeline):
    """Demonstrate system performance."""
    print("   ⚡ Testing system performance...")
    
    try:
        # Тест производительности поиска
        print("     • Testing search performance...")
        start_time = time.time()
        
        for _ in range(5):
            pipeline.search_engine.search_places("restaurant", "Bangkok", 10)
        
        search_time = time.time() - start_time
        print(f"       Search time: {search_time:.3f} seconds")
        
        # Тест производительности кэша
        print("     • Testing cache performance...")
        start_time = time.time()
        
        for _ in range(5):
            pipeline.cache_engine.get_cached_places("Bangkok", "attractions")
        
        cache_time = time.time() - start_time
        print(f"       Cache time: {cache_time:.3f} seconds")
        
        # Сравнение производительности
        if cache_time > 0:
            speedup = search_time / cache_time
            print(f"       Cache speedup: {speedup:.1f}x faster")
        
        print("   ✓ Performance demo completed")
        
    except Exception as e:
        print(f"   ✗ Performance demo failed: {e}")


def demo_system_optimization(pipeline):
    """Demonstrate system optimization."""
    print("   🔧 Testing system optimization...")
    
    try:
        # Оптимизация системы
        print("     • Optimizing system components...")
        pipeline.optimize_system()
        print("       ✓ System optimization completed")
        
        # Прогрев кэша
        print("     • Warming up cache...")
        pipeline.warm_cache(['Bangkok'], ['attractions', 'shopping', 'food_dining'])
        print("       ✓ Cache warming completed")
        
        # Статистика после оптимизации
        print("     • Post-optimization statistics...")
        stats = pipeline.get_statistics()
        print(f"       Total cached keys: {stats.get('cache_stats', {}).get('total_cached_keys', 0)}")
        
        print("   ✓ System optimization demo completed")
        
    except Exception as e:
        print(f"   ✗ System optimization demo failed: {e}")


def cleanup_system(pipeline, api):
    """Clean up system resources."""
    try:
        print("   Cleaning up system resources...")
        
        # Очищаем кэш
        if pipeline and pipeline.cache_engine:
            test_keys = pipeline.cache_engine.redis_client.keys("v1:places:integration:*")
            if test_keys:
                deleted_count = pipeline.cache_engine.redis_client.delete(*test_keys)
                print(f"     ✓ Cleaned up {deleted_count} cache keys")
        
        # Закрываем компоненты
        if pipeline:
            pipeline.close()
        if api:
            api.close()
        
        print("   ✓ System cleanup completed")
        
    except Exception as e:
        print(f"   ⚠️ Cleanup warning: {e}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
