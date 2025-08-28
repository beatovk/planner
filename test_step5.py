#!/usr/bin/env python3
"""
Step 5: Tag Grammar v1 - Demo Script
Demonstrates tag grammar engine capabilities.
"""

import sys
import time
from pathlib import Path

# Добавляем src в Python path
sys.path.insert(0, str(Path('.') / 'src'))

from tags import create_tag_grammar_engine


def main():
    """Main demonstration function."""
    print("🚀 Starting Step 5: Tag Grammar v1...")
    print("=" * 50)
    
    try:
        # Создаем движок грамматики тегов
        print("🧪 Creating tag grammar engine...")
        engine = create_tag_grammar_engine()
        
        if not engine.grammar_data:
            print("❌ Failed to load grammar data")
            return 1
        
        print(f"✅ Grammar loaded: {len(engine.categories)} categories")
        print()
        
        # Тест 1: Базовая информация о тегах
        print("🧪 Test 1: Basic tag information...")
        test_basic_tag_info(engine)
        print()
        
        # Тест 2: A/B уровни и приоритеты
        print("🧪 Test 2: A/B levels and priorities...")
        test_levels_and_priorities(engine)
        print()
        
        # Тест 3: EN/TH синонимы
        print("🧪 Test 3: EN/TH synonyms...")
        test_en_th_synonyms(engine)
        print()
        
        # Тест 4: Нормализация тегов
        print("🧪 Test 4: Tag normalization...")
        test_tag_normalization(engine)
        print()
        
        # Тест 5: Валидация тегов
        print("🧪 Test 5: Tag validation...")
        test_tag_validation(engine)
        print()
        
        # Тест 6: Поиск тегов
        print("🧪 Test 6: Tag search...")
        test_tag_search(engine)
        print()
        
        # Тест 7: Связанные теги
        print("🧪 Test 7: Related tags...")
        test_related_tags(engine)
        print()
        
        # Тест 8: Статистика
        print("🧪 Test 8: Tag statistics...")
        test_tag_statistics(engine)
        print()
        
        # Тест 9: Комбинации тегов
        print("🧪 Test 9: Tag combinations...")
        test_tag_combinations(engine)
        print()
        
        # Тест 10: Производительность
        print("🧪 Test 10: Performance testing...")
        test_performance(engine)
        print()
        
        print("✅ All Step 5 tests completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Error in Step 5: {e}")
        import traceback
        traceback.print_exc()
        return 1


def test_basic_tag_info(engine):
    """Test basic tag information retrieval."""
    # Проверяем основные категории
    core_categories = ["food_dining", "nightlife", "shopping", "culture_arts", "wellness_health"]
    
    for category in core_categories:
        info = engine.get_tag_info(category)
        if info:
            print(f"   {category}: {info['level']} level, priority {info['priority']}")
            print(f"     Description: {info['description']}")
        else:
            print(f"   ❌ {category}: Not found")
    
    print(f"   Total categories: {len(engine.categories)}")


def test_levels_and_priorities(engine):
    """Test A/B levels and priority system."""
    print(f"   A-level tags: {len(engine.level_a_tags)}")
    print(f"   B-level tags: {len(engine.level_b_tags)}")
    
    # Показываем приоритеты A-уровня
    print("   A-level priorities:")
    for name, data in sorted(engine.level_a_tags.items(), key=lambda x: x[1]['priority']):
        print(f"     {name}: priority {data['priority']}")
    
    # Показываем приоритеты B-уровня
    print("   B-level priorities:")
    for name, data in sorted(engine.level_b_tags.items(), key=lambda x: x[1]['priority']):
        print(f"     {name}: priority {data['priority']}")


def test_en_th_synonyms(engine):
    """Test English and Thai synonyms."""
    # Тестируем EN синонимы
    print("   Testing EN synonyms:")
    en_test_cases = ["restaurant", "cafe", "bar", "club", "mall", "museum", "spa", "park", "hotel", "bts"]
    
    for test_case in en_test_cases:
        category = engine.find_tag_by_synonym(test_case)
        if category:
            level = engine.get_tag_level(category)
            priority = engine.get_tag_priority(category)
            print(f"     '{test_case}' → {category} ({level}, priority {priority})")
        else:
            print(f"     '{test_case}' → Not found")
    
    # Тестируем TH синонимы
    print("   Testing TH synonyms:")
    th_test_cases = ["ร้านอาหาร", "คาเฟ่", "บาร์", "คลับ", "ห้างสรรพสินค้า", "พิพิธภัณฑ์", "สปา", "สวนสาธารณะ", "โรงแรม", "รถไฟฟ้าบีทีเอส"]
    
    for test_case in th_test_cases:
        category = engine.find_tag_by_synonym(test_case)
        if category:
            level = engine.get_tag_level(category)
            priority = engine.get_tag_priority(category)
            print(f"     '{test_case}' → {category} ({level}, priority {priority})")
        else:
            print(f"     '{test_case}' → Not found")


def test_tag_normalization(engine):
    """Test tag normalization functionality."""
    test_cases = [
        ["restaurant", "cafe", "bar"],
        ["restaurant", "ร้านอาหาร", "cafe"],
        ["restaurant", "unknown_tag", "cafe"],
        ["RESTAURANT", "CAFE", "BAR"],
        ["restaurant", "restaurant", "cafe"],
        ["", "restaurant", None, "cafe", ""]
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        normalized = engine.normalize_tags(test_case)
        print(f"   Case {i}: {test_case}")
        print(f"     → Normalized: {normalized}")


def test_tag_validation(engine):
    """Test tag validation functionality."""
    test_cases = [
        ["food_dining", "nightlife"],  # Valid
        ["food_dining"] * 10,  # Too many
        [],  # Too few
        ["outdoor_recreation", "business_services"],  # No level A
        ["food_dining", "unknown_tag"],  # Unknown tag
        ["food_dining", "nightlife", "shopping", "culture_arts"]  # Good combination
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"   Case {i}: {test_case}")
        validation = engine.validate_tags(test_case)
        
        print(f"     Valid: {validation['is_valid']}")
        if validation['errors']:
            print(f"     Errors: {validation['errors']}")
        if validation['warnings']:
            print(f"     Warnings: {validation['warnings']}")
        if validation['suggestions']:
            print(f"     Suggestions: {validation['suggestions']}")
        
        stats = validation['stats']
        print(f"     Stats: {stats['level_a_count']}A + {stats['level_b_count']}B + {stats['unknown_tags']}unknown")


def test_tag_search(engine):
    """Test tag search functionality."""
    search_queries = [
        ("restaurant", "en"),
        ("ร้านอาหาร", "th"),
        ("food", "en"),
        ("spa", "en"),
        ("park", "en"),
        ("xyz123", "en")  # No results expected
    ]
    
    for query, language in search_queries:
        print(f"   Search '{query}' ({language}):")
        results = engine.search_tags(query, language, max_results=3)
        
        if results:
            for result in results:
                print(f"     {result['tag']} (score: {result['score']:.2f}, level: {result['level']})")
        else:
            print(f"     No results found")


def test_related_tags(engine):
    """Test related tag functionality."""
    test_tags = ["food_dining", "nightlife", "shopping", "culture_arts", "wellness_health"]
    
    for tag in test_tags:
        related = engine.get_related_tags(tag, max_related=3)
        print(f"   {tag} related tags: {related}")


def test_tag_statistics(engine):
    """Test tag statistics generation."""
    stats = engine.get_tag_statistics()
    
    print(f"   Total categories: {stats['total_categories']}")
    print(f"   Level A: {stats['level_a_count']}")
    print(f"   Level B: {stats['level_b_count']}")
    print(f"   Total synonyms: {stats['total_synonyms']}")
    print(f"   Average synonyms per category: {stats['average_synonyms_per_category']}")
    
    print(f"   Language distribution:")
    print(f"     EN: {stats['language_distribution']['en_synonyms']}")
    print(f"     TH: {stats['language_distribution']['th_synonyms']}")
    
    print(f"   Priority distribution: {stats['priority_distribution']}")


def test_tag_combinations(engine):
    """Test tag combination scoring."""
    test_combinations = [
        ["food_dining", "nightlife"],  # Should score well
        ["culture_arts", "shopping"],  # Should score well
        ["wellness_health", "outdoor_recreation"],  # Should score well
        ["food_dining", "outdoor_recreation"],  # Regular score
        ["business_services", "transportation"],  # Should score well
        ["food_dining", "business_services"]  # Regular score
    ]
    
    for combination in test_combinations:
        validation = engine.validate_tags(combination)
        combination_suggestions = [s for s in validation['suggestions'] if "Good tag combination" in s]
        
        if combination_suggestions:
            print(f"   {combination} → Good combination!")
        else:
            print(f"   {combination} → Regular combination")


def test_performance(engine):
    """Test performance with large tag sets."""
    # Создаем большой набор тегов
    large_tag_set = []
    for i in range(1000):
        large_tag_set.extend(["food_dining", "nightlife", "shopping", "culture_arts", "wellness_health"])
    
    print(f"   Testing with {len(large_tag_set)} tags...")
    
    # Тест нормализации
    start_time = time.time()
    normalized = engine.normalize_tags(large_tag_set)
    normalize_time = time.time() - start_time
    
    # Тест валидации
    start_time = time.time()
    validation = engine.validate_tags(large_tag_set)
    validate_time = time.time() - start_time
    
    print(f"     Normalization: {normalize_time:.4f}s")
    print(f"     Validation: {validate_time:.4f}s")
    print(f"     Normalized to {len(normalized)} unique tags")
    print(f"     Validation valid: {validation['is_valid']}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
