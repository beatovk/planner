#!/usr/bin/env python3
"""
Step 7: Quality v1 - Demo Script
Demonstrates quality assessment engine capabilities.
"""

import sys
import time
from pathlib import Path

# Добавляем src в Python path
sys.path.insert(0, str(Path('.') / 'src'))

from quality import create_quality_engine, QualityLevel


def main():
    """Main demonstration function."""
    print("🚀 Starting Step 7: Quality v1...")
    print("=" * 50)
    
    try:
        # Создаем движок качества
        print("🧪 Creating quality engine...")
        engine = create_quality_engine(min_completeness=0.7, require_photo=True)
        
        print("✅ Quality engine created")
        print()
        
        # Тест 1: Базовые сценарии качества
        print("🧪 Test 1: Basic quality scenarios...")
        test_basic_quality_scenarios(engine)
        print()
        
        # Тест 2: Расчет полноты данных
        print("🧪 Test 2: Data completeness calculation...")
        test_completeness_calculation(engine)
        print()
        
        # Тест 3: Оценка качества фото
        print("🧪 Test 3: Photo quality assessment...")
        test_photo_quality_assessment(engine)
        print()
        
        # Тест 4: Свежесть данных
        print("🧪 Test 4: Data freshness evaluation...")
        test_data_freshness_evaluation(engine)
        print()
        
        # Тест 5: Надежность источников
        print("🧪 Test 5: Source reliability assessment...")
        test_source_reliability_assessment(engine)
        print()
        
        # Тест 6: Валидация данных
        print("🧪 Test 6: Data validation scoring...")
        test_data_validation_scoring(engine)
        print()
        
        # Тест 7: Общий QualityScore
        print("🧪 Test 7: Overall QualityScore calculation...")
        test_overall_quality_score(engine)
        print()
        
        # Тест 8: Принятие/отклонение мест
        print("🧪 Test 8: Place acceptance/rejection...")
        test_place_acceptance_rejection(engine)
        print()
        
        # Тест 9: Статистика и отчеты
        print("🧪 Test 9: Quality statistics and reports...")
        test_quality_statistics_and_reports(engine)
        print()
        
        # Тест 10: Настройка параметров
        print("🧪 Test 10: Parameter configuration...")
        test_parameter_configuration()
        print()
        
        print("✅ All Step 7 tests completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Error in Step 7: {e}")
        import traceback
        traceback.print_exc()
        return 1


def test_basic_quality_scenarios(engine):
    """Test basic quality assessment scenarios."""
    # Сценарий 1: Отличное качество
    excellent_place = {
        'id': 'excellent_1',
        'name': 'Amazing Thai Restaurant',
        'city': 'Bangkok',
        'domain': 'timeout.com',
        'url': 'https://timeout.com/restaurant/amazing-thai',
        'description': 'A fantastic Thai restaurant with authentic flavors and great atmosphere.',
        'address': '123 Sukhumvit Soi 11, Bangkok, Thailand',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'tags': ['thai', 'restaurant', 'authentic'],
        'flags': ['food_dining', 'local_experience'],
        'photos': [
            {'url': 'https://example.com/photo1.jpg', 'width': 800, 'height': 600},
            {'url': 'https://example.com/photo2.jpg', 'width': 1200, 'height': 800}
        ],
        'image_url': 'https://example.com/main-photo.jpg',
        'phone': '+66-2-123-4567',
        'email': 'info@amazingthai.com',
        'website': 'https://amazingthai.com',
        'hours': '10:00-22:00',
        'price_level': '$$',
        'rating': 4.5,
        'last_updated': '2025-01-15'
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(excellent_place)
    print(f"   Excellent place: {'ACCEPTED' if is_acceptable else 'REJECTED'}")
    print(f"     Completeness: {metrics.completeness:.3f}")
    print(f"     Photo score: {metrics.photo_score:.3f}")
    print(f"     Overall score: {details['overall_score']:.3f}")
    print(f"     Quality level: {details['quality_level']}")
    
    # Сценарий 2: Плохое качество
    poor_place = {
        'id': 'poor_1',
        'name': 'Thai Place',
        'city': 'Bangkok',
        'domain': 'unknown.com',
        'url': 'https://unknown.com/thai-place',
        'description': 'Thai food.',
        'photos': [],
        'last_updated': '2020-05-15'
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(poor_place)
    print(f"   Poor place: {'ACCEPTED' if is_acceptable else 'REJECTED'}")
    print(f"     Completeness: {metrics.completeness:.3f}")
    print(f"     Photo score: {metrics.photo_score:.3f}")
    print(f"     Overall score: {details['overall_score']:.3f}")
    print(f"     Quality level: {details['quality_level']}")


def test_completeness_calculation(engine):
    """Test data completeness calculation."""
    print("   Testing completeness calculation with different field combinations...")
    
    # Тест с минимальными полями
    minimal_place = {
        'id': 'minimal_1',
        'name': 'Minimal Restaurant',
        'city': 'Bangkok',
        'domain': 'test.com',
        'url': 'https://test.com/restaurant/minimal'
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(minimal_place)
    print(f"     Minimal fields: completeness {metrics.completeness:.3f} (threshold: {engine.min_completeness})")
    
    # Тест с важными полями
    important_place = {
        'id': 'important_1',
        'name': 'Important Restaurant',
        'city': 'Bangkok',
        'domain': 'test.com',
        'url': 'https://test.com/restaurant/important',
        'description': 'A restaurant with important fields filled.',
        'address': '123 Important Street, Bangkok',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'tags': ['restaurant', 'thai'],
        'flags': ['food_dining']
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(important_place)
    print(f"     Important fields: completeness {metrics.completeness:.3f}")
    
    # Тест с опциональными полями
    optional_place = {
        'id': 'optional_1',
        'name': 'Optional Restaurant',
        'city': 'Bangkok',
        'domain': 'test.com',
        'url': 'https://test.com/restaurant/optional',
        'description': 'A restaurant with optional fields filled.',
        'address': '123 Optional Street, Bangkok',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'tags': ['restaurant', 'thai'],
        'flags': ['food_dining'],
        'phone': '+66-2-123-4567',
        'email': 'info@optional.com',
        'website': 'https://optional.com',
        'hours': '10:00-22:00',
        'price_level': '$$',
        'rating': 4.5
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(optional_place)
    print(f"     Optional fields: completeness {metrics.completeness:.3f}")


def test_photo_quality_assessment(engine):
    """Test photo quality assessment."""
    print("   Testing photo quality assessment...")
    
    # Тест без фото
    no_photo_place = {
        'id': 'no_photo_1',
        'name': 'No Photo Restaurant',
        'city': 'Bangkok',
        'domain': 'test.com',
        'url': 'https://test.com/restaurant/no-photo',
        'description': 'A restaurant without photos.',
        'address': '123 No Photo Street, Bangkok',
        'photos': [],
        'image_url': None
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(no_photo_place)
    print(f"     No photos: score {metrics.photo_score:.3f}, {'ACCEPTED' if is_acceptable else 'REJECTED'}")
    
    # Тест с базовыми фото
    basic_photo_place = {
        'id': 'basic_photo_1',
        'name': 'Basic Photo Restaurant',
        'city': 'Bangkok',
        'domain': 'test.com',
        'url': 'https://test.com/restaurant/basic-photo',
        'description': 'A restaurant with basic photos.',
        'address': '123 Basic Photo Street, Bangkok',
        'photos': [{'url': 'https://example.com/photo1.jpg'}],
        'image_url': 'https://example.com/main-photo.jpg'
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(basic_photo_place)
    print(f"     Basic photos: score {metrics.photo_score:.3f}, {'ACCEPTED' if is_acceptable else 'REJECTED'}")
    
    # Тест с высококачественными фото
    high_quality_photo_place = {
        'id': 'high_quality_1',
        'name': 'High Quality Photo Restaurant',
        'city': 'Bangkok',
        'domain': 'test.com',
        'url': 'https://test.com/restaurant/high-quality',
        'description': 'A restaurant with high-quality photos.',
        'address': '123 High Quality Street, Bangkok',
        'photos': [
            {
                'url': 'https://example.com/high-res1.jpg',
                'width': 1920,
                'height': 1080,
                'alt_text': 'Beautiful restaurant interior'
            },
            {
                'url': 'https://example.com/high-res2.jpg',
                'width': 1600,
                'height': 1200,
                'alt_text': 'Delicious food'
            }
        ],
        'image_url': 'https://example.com/hd-main-photo.jpg'
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(high_quality_photo_place)
    print(f"     High-quality photos: score {metrics.photo_score:.3f}, {'ACCEPTED' if is_acceptable else 'REJECTED'}")


def test_data_freshness_evaluation(engine):
    """Test data freshness evaluation."""
    print("   Testing data freshness evaluation...")
    
    # Тест с недавними данными
    recent_place = {
        'id': 'recent_1',
        'name': 'Recent Restaurant',
        'city': 'Bangkok',
        'domain': 'test.com',
        'url': 'https://test.com/restaurant/recent',
        'description': 'A recently updated restaurant.',
        'photos': [{'url': 'https://example.com/photo.jpg'}],
        'last_updated': '2025-01-20'
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(recent_place)
    print(f"     Recent data (2025): freshness {metrics.data_freshness:.3f}")
    
    # Тест со старыми данными
    old_place = {
        'id': 'old_1',
        'name': 'Old Restaurant',
        'city': 'Bangkok',
        'domain': 'test.com',
        'url': 'https://test.com/restaurant/old',
        'description': 'An old restaurant.',
        'photos': [{'url': 'https://example.com/photo.jpg'}],
        'last_updated': '2020-05-15'
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(old_place)
    print(f"     Old data (2020): freshness {metrics.data_freshness:.3f}")
    
    # Тест с неизвестной свежестью
    unknown_freshness_place = {
        'id': 'unknown_1',
        'name': 'Unknown Freshness Restaurant',
        'city': 'Bangkok',
        'domain': 'test.com',
        'url': 'https://test.com/restaurant/unknown',
        'description': 'A restaurant with unknown freshness.',
        'photos': [{'url': 'https://example.com/photo.jpg'}]
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(unknown_freshness_place)
    print(f"     Unknown freshness: freshness {metrics.data_freshness:.3f}")


def test_source_reliability_assessment(engine):
    """Test source reliability assessment."""
    print("   Testing source reliability assessment...")
    
    # Тест с надежным источником
    reliable_source_place = {
        'id': 'reliable_1',
        'name': 'Reliable Source Restaurant',
        'city': 'Bangkok',
        'domain': 'timeout.com',
        'url': 'https://timeout.com/restaurant/reliable',
        'description': 'A restaurant from a reliable source.',
        'photos': [{'url': 'https://example.com/photo.jpg'}]
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(reliable_source_place)
    print(f"     Reliable source (timeout.com): reliability {metrics.source_reliability:.3f}")
    
    # Тест с неизвестным источником
    unknown_source_place = {
        'id': 'unknown_source_1',
        'name': 'Unknown Source Restaurant',
        'city': 'Bangkok',
        'domain': 'unknown.com',
        'url': 'https://unknown.com/restaurant/unknown',
        'description': 'A restaurant from an unknown source.',
        'photos': [{'url': 'https://example.com/photo.jpg'}]
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(unknown_source_place)
    print(f"     Unknown source (unknown.com): reliability {metrics.source_reliability:.3f}")
    
    # Тест с HTTPS бонусом
    https_place = {
        'id': 'https_1',
        'name': 'HTTPS Restaurant',
        'city': 'Bangkok',
        'domain': 'bk-magazine.com',
        'url': 'https://bk-magazine.com/restaurant/https',
        'description': 'A restaurant with HTTPS URL.',
        'photos': [{'url': 'https://example.com/photo.jpg'}]
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(https_place)
    print(f"     HTTPS bonus (bk-magazine.com): reliability {metrics.source_reliability:.3f}")


def test_data_validation_scoring(engine):
    """Test data validation scoring."""
    print("   Testing data validation scoring...")
    
    # Тест с хорошо валидированными данными
    well_validated_place = {
        'id': 'well_validated_1',
        'name': 'Well Validated Restaurant',
        'city': 'Bangkok',
        'domain': 'test.com',
        'url': 'https://test.com/restaurant/well-validated',
        'description': 'A restaurant with well-validated data.',
        'address': '123 Well Validated Street, Bangkok, Thailand',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'tags': ['restaurant', 'thai', 'validated'],
        'photos': [{'url': 'https://example.com/photo.jpg'}]
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(well_validated_place)
    print(f"     Well validated: validation score {metrics.validation_score:.3f}")
    
    # Тест с плохо валидированными данными
    poorly_validated_place = {
        'id': 'poorly_validated_1',
        'name': '',
        'city': 'Bangkok',
        'domain': 'test.com',
        'url': 'invalid-url',
        'description': 'Short.',
        'photos': []
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(poorly_validated_place)
    print(f"     Poorly validated: validation score {metrics.validation_score:.3f}")


def test_overall_quality_score(engine):
    """Test overall quality score calculation."""
    print("   Testing overall quality score calculation...")
    
    # Тест с отличным качеством
    excellent_place = {
        'id': 'excellent_overall_1',
        'name': 'Excellent Overall Restaurant',
        'city': 'Bangkok',
        'domain': 'timeout.com',
        'url': 'https://timeout.com/restaurant/excellent',
        'description': 'A restaurant with excellent overall quality.',
        'address': '123 Excellent Street, Bangkok, Thailand',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'tags': ['restaurant', 'thai', 'excellent'],
        'flags': ['food_dining', 'local_experience'],
        'photos': [
            {
                'url': 'https://example.com/excellent1.jpg',
                'width': 1920,
                'height': 1080,
                'alt_text': 'Excellent restaurant'
            }
        ],
        'image_url': 'https://example.com/excellent-main.jpg',
        'phone': '+66-2-123-4567',
        'email': 'info@excellent.com',
        'website': 'https://excellent.com',
        'last_updated': '2025-01-20'
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(excellent_place)
    print(f"     Excellent quality: overall score {details['overall_score']:.3f}")
    print(f"       Completeness: {metrics.completeness:.3f}")
    print(f"       Photo score: {metrics.photo_score:.3f}")
    print(f"       Data freshness: {metrics.data_freshness:.3f}")
    print(f"       Source reliability: {metrics.source_reliability:.3f}")
    print(f"       Validation score: {metrics.validation_score:.3f}")
    print(f"       Quality level: {details['quality_level']}")


def test_place_acceptance_rejection(engine):
    """Test place acceptance and rejection logic."""
    print("   Testing place acceptance and rejection logic...")
    
    # Тест с местом, которое должно быть принято
    acceptable_place = {
        'id': 'acceptable_1',
        'name': 'Acceptable Restaurant',
        'city': 'Bangkok',
        'domain': 'timeout.com',
        'url': 'https://timeout.com/restaurant/acceptable',
        'description': 'A restaurant that should be accepted.',
        'address': '123 Acceptable Street, Bangkok',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'tags': ['restaurant', 'thai'],
        'photos': [{'url': 'https://example.com/photo.jpg'}],
        'last_updated': '2025-01-15'
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(acceptable_place)
    print(f"     Acceptable place: {'ACCEPTED' if is_acceptable else 'REJECTED'}")
    print(f"       Completeness: {metrics.completeness:.3f} (threshold: {engine.min_completeness})")
    print(f"       Photo score: {metrics.photo_score:.3f}")
    print(f"       Overall score: {details['overall_score']:.3f}")
    
    # Тест с местом без фото (должно быть отклонено)
    no_photo_place = {
        'id': 'no_photo_rejection_1',
        'name': 'No Photo Rejection Restaurant',
        'city': 'Bangkok',
        'domain': 'timeout.com',
        'url': 'https://timeout.com/restaurant/no-photo-rejection',
        'description': 'A restaurant without photos that should be rejected.',
        'address': '123 No Photo Street, Bangkok',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'tags': ['restaurant', 'thai'],
        'photos': [],
        'last_updated': '2025-01-15'
    }
    
    is_acceptable, metrics, details = engine.assess_place_quality(no_photo_place)
    print(f"     No photo place: {'ACCEPTED' if is_acceptable else 'REJECTED'}")
    print(f"       Photo score: {metrics.photo_score:.3f}")
    print(f"       Warnings: {details['warnings']}")


def test_quality_statistics_and_reports(engine):
    """Test quality statistics and reporting."""
    print("   Testing quality statistics and reporting...")
    
    # Оцениваем несколько мест для статистики
    test_places = [
        {
            'id': 'stats_1',
            'name': 'Statistics Restaurant 1',
            'city': 'Bangkok',
            'domain': 'timeout.com',
            'url': 'https://timeout.com/restaurant/stats1',
            'description': 'First restaurant for statistics.',
            'photos': [{'url': 'https://example.com/photo1.jpg'}],
            'last_updated': '2025-01-15'
        },
        {
            'id': 'stats_2',
            'name': 'Statistics Restaurant 2',
            'city': 'Bangkok',
            'domain': 'bk-magazine.com',
            'url': 'https://bk-magazine.com/restaurant/stats2',
            'description': 'Second restaurant for statistics.',
            'photos': [{'url': 'https://example.com/photo2.jpg'}],
            'last_updated': '2024-12-20'
        },
        {
            'id': 'stats_3',
            'name': 'Statistics Restaurant 3',
            'city': 'Bangkok',
            'domain': 'test.com',
            'url': 'https://test.com/restaurant/stats3',
            'description': 'Third restaurant for statistics.',
            'photos': [],
            'last_updated': '2020-05-15'
        }
    ]
    
    # Оцениваем качество
    for place_data in test_places:
        engine.assess_place_quality(place_data)
    
    # Получаем статистику
    stats = engine.get_quality_statistics()
    print(f"     Total assessed: {stats['total_assessed']}")
    print(f"     Accepted: {stats['accepted']}")
    print(f"     Rejected: {stats['rejected']}")
    print(f"     Acceptance rate: {stats['acceptance_rate']:.1%}")
    print(f"     Average completeness: {stats['avg_completeness']:.3f}")
    print(f"     Average photo score: {stats['avg_photo_score']:.3f}")
    print(f"     Average overall score: {stats['avg_overall_score']:.3f}")
    
    # Получаем сводку
    summary = engine.get_quality_summary()
    print(f"     Summary - Total: {summary['total_assessed']}")
    print(f"     Summary - Acceptance: {summary['acceptance_rate']}")
    print(f"     Summary - Rejection: {summary['rejection_rate']}")
    
    # Экспортируем отчет
    print("     Exporting quality report...")
    export_file = "quality_report_step7.txt"
    engine.export_quality_report(export_file, test_places)
    print(f"       Report exported to: {export_file}")


def test_parameter_configuration():
    """Test different parameter configurations."""
    print("   Testing different parameter configurations...")
    
    # Тест 1: Строгие требования к полноте
    print("     Test 1: Strict completeness requirements (0.9)")
    strict_engine = create_quality_engine(min_completeness=0.9, require_photo=True)
    
    test_place = {
        'id': 'strict_test_1',
        'name': 'Strict Test Restaurant',
        'city': 'Bangkok',
        'domain': 'timeout.com',
        'url': 'https://timeout.com/restaurant/strict-test',
        'description': 'A restaurant for strict testing.',
        'address': '123 Strict Street, Bangkok',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'tags': ['restaurant', 'thai'],
        'photos': [{'url': 'https://example.com/photo.jpg'}],
        'last_updated': '2025-01-15'
    }
    
    is_acceptable, metrics, details = strict_engine.assess_place_quality(test_place)
    print(f"       Completeness: {metrics.completeness:.3f} (threshold: 0.9)")
    print(f"       Result: {'ACCEPTED' if is_acceptable else 'REJECTED'}")
    
    # Тест 2: Отключение требования фото
    print("     Test 2: Photo requirement disabled")
    no_photo_engine = create_quality_engine(min_completeness=0.7, require_photo=False)
    
    no_photo_place = {
        'id': 'no_photo_test_1',
        'name': 'No Photo Test Restaurant',
        'city': 'Bangkok',
        'domain': 'timeout.com',
        'url': 'https://timeout.com/restaurant/no-photo-test',
        'description': 'A restaurant without photos for testing.',
        'address': '123 No Photo Street, Bangkok',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'tags': ['restaurant', 'thai'],
        'photos': [],
        'last_updated': '2025-01-15'
    }
    
    is_acceptable, metrics, details = no_photo_engine.assess_place_quality(no_photo_place)
    print(f"       Photo score: {metrics.photo_score:.3f}")
    print(f"       Result: {'ACCEPTED' if is_acceptable else 'REJECTED'}")
    
    # Тест 3: Очень строгие требования
    print("     Test 3: Very strict requirements (0.95)")
    very_strict_engine = create_quality_engine(min_completeness=0.95, require_photo=True)
    
    is_acceptable, metrics, details = very_strict_engine.assess_place_quality(test_place)
    print(f"       Completeness: {metrics.completeness:.3f} (threshold: 0.95)")
    print(f"       Result: {'ACCEPTED' if is_acceptable else 'REJECTED'}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
