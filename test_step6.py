#!/usr/bin/env python3
"""
Step 6: Dedup v1 - Demo Script
Demonstrates deduplication engine capabilities.
"""

import sys
import time
from pathlib import Path

# Добавляем src в Python path
sys.path.insert(0, str(Path('.') / 'src'))

from dedup import create_dedup_engine


def main():
    """Main demonstration function."""
    print("🚀 Starting Step 6: Dedup v1...")
    print("=" * 50)
    
    try:
        # Создаем движок дедупликации
        print("🧪 Creating deduplication engine...")
        engine = create_dedup_engine(fuzzy_threshold=0.86, geo_tolerance=0.001)
        
        print("✅ Deduplication engine created")
        print()
        
        # Тест 1: Базовые сценарии дедупликации
        print("🧪 Test 1: Basic deduplication scenarios...")
        test_basic_scenarios(engine)
        print()
        
        # Тест 2: Identity key дедупликация
        print("🧪 Test 2: Identity key deduplication...")
        test_identity_key_dedup(engine)
        print()
        
        # Тест 3: Fuzzy name matching
        print("🧪 Test 3: Fuzzy name matching...")
        test_fuzzy_name_matching(engine)
        print()
        
        # Тест 4: Address matching
        print("🧪 Test 4: Address matching...")
        test_address_matching(engine)
        print()
        
        # Тест 5: Geographic proximity
        print("🧪 Test 5: Geographic proximity...")
        test_geo_proximity(engine)
        print()
        
        # Тест 6: Комплексные сценарии
        print("🧪 Test 6: Complex scenarios...")
        test_complex_scenarios(engine)
        print()
        
        # Тест 7: Группы дубликатов
        print("🧪 Test 7: Duplicate groups...")
        test_duplicate_groups(engine)
        print()
        
        # Тест 8: Статистика и отчеты
        print("🧪 Test 8: Statistics and reports...")
        test_statistics_and_reports(engine)
        print()
        
        # Тест 9: Производительность
        print("🧪 Test 9: Performance testing...")
        test_performance(engine)
        print()
        
        # Тест 10: Настройка параметров
        print("🧪 Test 10: Parameter tuning...")
        test_parameter_tuning()
        print()
        
        print("✅ All Step 6 tests completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Error in Step 6: {e}")
        import traceback
        traceback.print_exc()
        return 1


def test_basic_scenarios(engine):
    """Test basic deduplication scenarios."""
    # Сценарий 1: Точное дублирование
    place1 = {
        'id': 'restaurant_1',
        'name': 'Amazing Thai Restaurant',
        'city': 'Bangkok',
        'domain': 'timeout.com',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'address': '123 Sukhumvit Soi 11, Bangkok',
        'url': 'https://timeout.com/restaurant/amazing-thai'
    }
    
    # Добавляем первое место
    is_duplicate, duplicate_id = engine.add_place(place1)
    print(f"   Adding place 1: {'DUPLICATE' if is_duplicate else 'UNIQUE'}")
    
    # Добавляем то же место снова
    is_duplicate, duplicate_id = engine.add_place(place1)
    print(f"   Adding place 1 again: {'DUPLICATE' if is_duplicate else 'UNIQUE'} (matches: {duplicate_id})")
    
    # Сценарий 2: Разные места
    place2 = {
        'id': 'restaurant_2',
        'name': 'Sushi Master',
        'city': 'Bangkok',
        'domain': 'timeout.com',
        'geo_lat': 13.7500,
        'geo_lng': 100.5000,
        'address': '456 Silom Soi 4, Bangkok',
        'url': 'https://timeout.com/restaurant/sushi-master'
    }
    
    is_duplicate, duplicate_id = engine.add_place(place2)
    print(f"   Adding place 2: {'DUPLICATE' if is_duplicate else 'UNIQUE'}")
    
    # Статистика
    stats = engine.get_dedup_statistics()
    print(f"   Stats: {stats['total_processed']} unique, {stats['duplicates_found']} duplicates")


def test_identity_key_dedup(engine):
    """Test identity key based deduplication."""
    # Места с одинаковыми core данными, но разными адресами
    place1 = {
        'id': 'restaurant_3',
        'name': 'Thai Delight',
        'city': 'Bangkok',
        'domain': 'timeout.com',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'address': '123 Sukhumvit Soi 11, Bangkok',
        'url': 'https://timeout.com/restaurant/thai-delight'
    }
    
    place2 = {
        'id': 'restaurant_4',
        'name': 'Thai Delight',
        'city': 'Bangkok',
        'domain': 'timeout.com',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'address': '789 Thonglor Soi 10, Bangkok',  # Разный адрес
        'url': 'https://timeout.com/restaurant/thai-delight-2'
    }
    
    # Добавляем первое место
    is_duplicate, duplicate_id = engine.add_place(place1)
    print(f"   Adding Thai Delight 1: {'DUPLICATE' if is_duplicate else 'UNIQUE'}")
    
    # Добавляем второе место (должно быть дубликатом по identity key)
    is_duplicate, duplicate_id = engine.add_place(place2)
    print(f"   Adding Thai Delight 2: {'DUPLICATE' if is_duplicate else 'UNIQUE'} (matches: {duplicate_id})")
    
    # Статистика
    stats = engine.get_dedup_statistics()
    print(f"   Identity matches: {stats['identity_matches']}")


def test_fuzzy_name_matching(engine):
    """Test fuzzy name matching."""
    # Места с похожими именами
    place1 = {
        'id': 'restaurant_5',
        'name': 'Amazing Thai Restaurant',
        'city': 'Bangkok',
        'domain': 'timeout.com',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'address': '123 Sukhumvit Soi 11, Bangkok',
        'url': 'https://timeout.com/restaurant/amazing-thai'
    }
    
    place2 = {
        'id': 'restaurant_6',
        'name': 'Amazing Thai Restaurnt',  # Опечатка: пропущена 'a'
        'city': 'Bangkok',
        'domain': 'timeout.com',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'address': '123 Sukhumvit Soi 11, Bangkok',
        'url': 'https://timeout.com/restaurant/amazing-thai-2'
    }
    
    # Добавляем первое место
    is_duplicate, duplicate_id = engine.add_place(place1)
    print(f"   Adding 'Amazing Thai Restaurant': {'DUPLICATE' if is_duplicate else 'UNIQUE'}")
    
    # Добавляем второе место (должно быть дубликатом по fuzzy matching)
    is_duplicate, duplicate_id = engine.add_place(place2)
    print(f"   Adding 'Amazing Thai Restaurnt': {'DUPLICATE' if is_duplicate else 'UNIQUE'} (matches: {duplicate_id})")
    
    # Статистика
    stats = engine.get_dedup_statistics()
    print(f"   Fuzzy matches: {stats['fuzzy_matches']}")


def test_address_matching(engine):
    """Test address based deduplication."""
    # Места с одинаковыми адресами, но разными именами
    place1 = {
        'id': 'restaurant_7',
        'name': 'Thai Spice',
        'city': 'Bangkok',
        'domain': 'timeout.com',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'address': '123 Sukhumvit Soi 11, Bangkok, Thailand',
        'url': 'https://timeout.com/restaurant/thai-spice'
    }
    
    place2 = {
        'id': 'restaurant_8',
        'name': 'Bangkok Bites',
        'city': 'Bangkok',
        'domain': 'bk-magazine.com',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'address': '123 Sukhumvit Soi 11, Bangkok, Thailand',  # Тот же адрес
        'url': 'https://bk-magazine.com/restaurant/bangkok-bites'
    }
    
    # Добавляем первое место
    is_duplicate, duplicate_id = engine.add_place(place1)
    print(f"   Adding Thai Spice: {'DUPLICATE' if is_duplicate else 'UNIQUE'}")
    
    # Добавляем второе место (должно быть дубликатом по адресу)
    is_duplicate, duplicate_id = engine.add_place(place2)
    print(f"   Adding Bangkok Bites: {'DUPLICATE' if is_duplicate else 'UNIQUE'} (matches: {duplicate_id})")
    
    # Статистика
    stats = engine.get_dedup_statistics()
    print(f"   Address matches: {stats['address_matches']}")


def test_geo_proximity(engine):
    """Test geographic proximity deduplication."""
    # Места с одинаковыми координатами, но разными адресами
    place1 = {
        'id': 'restaurant_9',
        'name': 'Riverside Thai',
        'city': 'Bangkok',
        'domain': 'timeout.com',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'address': '123 Sukhumvit Soi 11, Bangkok',
        'url': 'https://timeout.com/restaurant/riverside-thai'
    }
    
    place2 = {
        'id': 'restaurant_10',
        'name': 'Riverside Thai',
        'city': 'Bangkok',
        'domain': 'timeout.com',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'address': '123 Sukhumvit Soi 11, Bangkok, Thailand',  # Тот же адрес, но другой формат
        'url': 'https://timeout.com/restaurant/riverside-thai-2'
    }
    
    # Добавляем первое место
    is_duplicate, duplicate_id = engine.add_place(place1)
    print(f"   Adding Riverside Thai 1: {'DUPLICATE' if is_duplicate else 'UNIQUE'}")
    
    # Добавляем второе место (должно быть дубликатом по гео)
    is_duplicate, duplicate_id = engine.add_place(place2)
    print(f"   Adding Riverside Thai 2: {'DUPLICATE' if is_duplicate else 'UNIQUE'} (matches: {duplicate_id})")
    
    # Статистика
    stats = engine.get_dedup_statistics()
    print(f"   Geo matches: {stats['geo_matches']}")


def test_complex_scenarios(engine):
    """Test complex deduplication scenarios."""
    # Создаем набор мест с различными типами дублирования
    complex_places = [
        # Группа 1: Одинаковые core данные
        {
            'id': 'group1_1',
            'name': 'Best Thai Food',
            'city': 'Bangkok',
            'domain': 'timeout.com',
            'geo_lat': 13.7563,
            'geo_lng': 100.5018,
            'address': '123 Sukhumvit Soi 11, Bangkok',
            'url': 'https://timeout.com/restaurant/best-thai-1'
        },
        {
            'id': 'group1_2',
            'name': 'Best Thai Food',
            'city': 'Bangkok',
            'domain': 'timeout.com',
            'geo_lat': 13.7563,
            'geo_lng': 100.5018,
            'address': '456 Silom Soi 4, Bangkok',  # Разный адрес
            'url': 'https://timeout.com/restaurant/best-thai-2'
        },
        
        # Группа 2: Похожие имена
        {
            'id': 'group2_1',
            'name': 'Thai Delight Restaurant',
            'city': 'Bangkok',
            'domain': 'timeout.com',
            'geo_lat': 13.7500,
            'geo_lng': 100.5000,
            'address': '789 Thonglor Soi 10, Bangkok',
            'url': 'https://timeout.com/restaurant/thai-delight-1'
        },
        {
            'id': 'group2_2',
            'name': 'Thai Delight Restaurnt',  # Опечатка
            'city': 'Bangkok',
            'domain': 'timeout.com',
            'geo_lat': 13.7500,
            'geo_lng': 100.5000,
            'address': '789 Thonglor Soi 10, Bangkok',
            'url': 'https://timeout.com/restaurant/thai-delight-2'
        },
        
        # Группа 3: Одинаковые адреса
        {
            'id': 'group3_1',
            'name': 'Sushi Master',
            'city': 'Bangkok',
            'domain': 'timeout.com',
            'geo_lat': 13.7500,
            'geo_lng': 100.5000,
            'address': '456 Silom Soi 4, Bangkok, Thailand',
            'url': 'https://timeout.com/restaurant/sushi-master-1'
        },
        {
            'id': 'group3_2',
            'name': 'Japanese Kitchen',
            'city': 'Bangkok',
            'domain': 'bk-magazine.com',
            'geo_lat': 13.7500,
            'geo_lng': 100.5000,
            'address': '456 Silom Soi 4, Bangkok, Thailand',  # Тот же адрес
            'url': 'https://bk-magazine.com/restaurant/japanese-kitchen'
        }
    ]
    
    print("   Testing complex scenarios with multiple deduplication types...")
    
    places_added = []
    duplicates_found = 0
    
    for i, place_data in enumerate(complex_places, 1):
        is_duplicate, duplicate_id = engine.add_place(place_data)
        
        if is_duplicate:
            duplicates_found += 1
            print(f"     Place {i}: DUPLICATE (matches: {duplicate_id})")
        else:
            places_added.append(place_data['id'])
            print(f"     Place {i}: UNIQUE")
    
    print(f"   Results: {len(places_added)} unique, {duplicates_found} duplicates")
    
    # Статистика
    stats = engine.get_dedup_statistics()
    print(f"   Total stats: {stats['total_processed']} processed, {stats['duplicates_found']} duplicates")
    print(f"   Dedup rate: {stats['dedup_rate']:.2%}")


def test_duplicate_groups(engine):
    """Test duplicate group detection."""
    print("   Analyzing duplicate groups...")
    
    # Получаем группы дубликатов
    duplicate_groups = engine.get_duplicate_groups()
    
    if duplicate_groups:
        print(f"   Found {len(duplicate_groups)} duplicate groups:")
        
        for i, group in enumerate(duplicate_groups, 1):
            print(f"     Group {i}: {len(group)} places")
            
            # Показываем детали группы
            for place_id in group[:3]:  # Показываем первые 3
                place = engine.processed_places[place_id]
                print(f"       - {place_id}: {place.name} ({place.city})")
            
            if len(group) > 3:
                print(f"       ... and {len(group) - 3} more")
    else:
        print("   No duplicate groups found")
    
    # Статистика по группам
    stats = engine.get_dedup_statistics()
    print(f"   Total duplicates in groups: {stats['total_duplicates']}")


def test_statistics_and_reports(engine):
    """Test statistics and reporting functionality."""
    print("   Generating comprehensive statistics...")
    
    # Получаем детальную статистику
    stats = engine.get_dedup_statistics()
    
    print(f"   Processing Statistics:")
    print(f"     Total processed: {stats['total_processed']}")
    print(f"     Duplicates found: {stats['duplicates_found']}")
    print(f"     Dedup rate: {stats['dedup_rate']:.2%}")
    
    print(f"   Match Types:")
    print(f"     Identity matches: {stats['identity_matches']}")
    print(f"     Fuzzy matches: {stats['fuzzy_matches']}")
    print(f"     Address matches: {stats['address_matches']}")
    print(f"     Geo matches: {stats['geo_matches']}")
    
    print(f"   Group Analysis:")
    print(f"     Duplicate groups: {stats['duplicate_groups']}")
    print(f"     Total duplicates: {stats['total_duplicates']}")
    
    # Экспорт отчета
    print("   Exporting duplicate report...")
    export_file = "dedup_report_step6.txt"
    engine.export_duplicates(export_file)
    print(f"     Report exported to: {export_file}")


def test_performance(engine):
    """Test performance with larger datasets."""
    print("   Testing performance with larger datasets...")
    
    # Создаем большой набор тестовых данных
    large_dataset = []
    for i in range(200):
        place_data = {
            'id': f'perf_test_{i}',
            'name': f'Restaurant {i}',
            'city': 'Bangkok',
            'domain': 'test.com',
            'geo_lat': 13.7563 + (i * 0.0001),  # Постепенно увеличиваем координаты
            'geo_lng': 100.5018 + (i * 0.0001),
            'address': f'Address {i}, Bangkok, Thailand',
            'url': f'https://test.com/restaurant/{i}'
        }
        large_dataset.append(place_data)
    
    print(f"     Dataset size: {len(large_dataset)} places")
    
    # Тест производительности
    start_time = time.time()
    
    for place_data in large_dataset:
        engine.add_place(place_data)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"     Processing time: {processing_time:.4f} seconds")
    print(f"     Average time per place: {(processing_time / len(large_dataset)) * 1000:.2f} ms")
    
    # Результаты
    stats = engine.get_dedup_statistics()
    print(f"     Results: {stats['total_processed']} unique, {stats['duplicates_found']} duplicates")
    
    # Производительность должна быть хорошей
    if processing_time < 1.0:
        print(f"     ✅ Performance: EXCELLENT (< 1 second)")
    elif processing_time < 2.0:
        print(f"     ✅ Performance: GOOD (< 2 seconds)")
    else:
        print(f"     ⚠️ Performance: SLOW ({processing_time:.2f} seconds)")


def test_parameter_tuning():
    """Test different parameter configurations."""
    print("   Testing parameter tuning...")
    
    # Тест 1: Строгий fuzzy threshold
    print("     Test 1: Strict fuzzy threshold (0.95)")
    strict_engine = create_dedup_engine(fuzzy_threshold=0.95, geo_tolerance=0.001)
    
    test_place1 = {
        'id': 'strict_test_1',
        'name': 'Amazing Thai Restaurant',
        'city': 'Bangkok',
        'domain': 'test.com',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'address': '123 Sukhumvit, Bangkok',
        'url': 'https://test.com/restaurant/amazing-thai'
    }
    
    test_place2 = {
        'id': 'strict_test_2',
        'name': 'Amazing Thai Restaurnt',  # Опечатка
        'city': 'Bangkok',
        'domain': 'test.com',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'address': '123 Sukhumvit, Bangkok',
        'url': 'https://test.com/restaurant/amazing-thai-2'
    }
    
    is_duplicate1, _ = strict_engine.add_place(test_place1)
    is_duplicate2, _ = strict_engine.add_place(test_place2)
    
    print(f"       Place 1: {'DUPLICATE' if is_duplicate1 else 'UNIQUE'}")
    print(f"       Place 2: {'DUPLICATE' if is_duplicate2 else 'UNIQUE'}")
    print(f"       Result: {'NOT DETECTED' if not is_duplicate2 else 'DETECTED'} (expected: NOT DETECTED)")
    
    # Тест 2: Строгий geo tolerance
    print("     Test 2: Strict geo tolerance (0.0001)")
    strict_geo_engine = create_dedup_engine(fuzzy_threshold=0.86, geo_tolerance=0.0001)
    
    test_place3 = {
        'id': 'geo_test_1',
        'name': 'Thai Restaurant',
        'city': 'Bangkok',
        'domain': 'test.com',
        'geo_lat': 13.7563,
        'geo_lng': 100.5018,
        'address': '123 Sukhumvit, Bangkok',
        'url': 'https://test.com/restaurant/thai-1'
    }
    
    test_place4 = {
        'id': 'geo_test_2',
        'name': 'Thai Restaurant',
        'city': 'Bangkok',
        'domain': 'test.com',
        'geo_lat': 13.7563,  # Тот же lat
        'geo_lng': 100.5018,  # Тот же lng
        'address': '123 Sukhumvit, Bangkok',
        'url': 'https://test.com/restaurant/thai-2'
    }
    
    is_duplicate3, _ = strict_geo_engine.add_place(test_place3)
    is_duplicate4, _ = strict_geo_engine.add_place(test_place4)
    
    print(f"       Place 3: {'DUPLICATE' if is_duplicate3 else 'UNIQUE'}")
    print(f"       Place 4: {'DUPLICATE' if is_duplicate4 else 'UNIQUE'}")
    print(f"       Result: {'NOT DETECTED' if not is_duplicate4 else 'DETECTED'} (expected: DETECTED)")
    
    print("     Parameter tuning completed")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
