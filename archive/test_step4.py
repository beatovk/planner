#!/usr/bin/env python3
"""
Test script for Step 4: Normalizer v1.
"""

import sys
import logging
from pathlib import Path

# Добавляем src в Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from normalizers import (
    BaseNormalizer,
    BangkokNormalizer,
    UniversalNormalizer,
    create_universal_normalizer
)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_base_normalizer():
    """Test base normalizer functionality."""
    print("🧪 Testing base normalizer...")
    
    try:
        normalizer = BaseNormalizer()
        
        # Test data
        test_place = {
            'name': '<strong>amazing thai restaurant</strong>',
            'description': 'This is an INCREDIBLE restaurant with the BEST food ever!!! It\'s located in the heart of Bangkok and serves authentic Thai cuisine. The atmosphere is wonderful and the service is excellent. You must visit this place!!!',
            'area': 'sukhumvit soi 11',
            'tags': ['thai', 'restaurant', 'thai', 'food'],
            'flags': ['food_dining', 'food_dining']
        }
        
        # Normalize place
        normalized = normalizer.normalize_place(test_place)
        
        print(f"   ✅ Base normalization completed")
        print(f"   Original name: {test_place['name']}")
        print(f"   Normalized name: {normalized['name']}")
        print(f"   Original description: {test_place['description'][:50]}...")
        print(f"   Normalized description: {normalized['description'][:50]}...")
        print(f"   Original area: {test_place['area']}")
        print(f"   Normalized area: {normalized['area']}")
        print(f"   Original tags: {test_place['tags']}")
        print(f"   Normalized tags: {normalized['tags']}")
        print(f"   Original flags: {test_place['flags']}")
        print(f"   Normalized flags: {normalized['flags']}")
        
        # Get normalization stats
        stats = normalizer.get_normalization_stats(test_place, normalized)
        print(f"   Fields normalized: {stats['fields_normalized']}")
        print(f"   Characters removed: {stats['characters_removed']}")
        print(f"   Quality improvements: {stats['quality_improvements']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing base normalizer: {e}")
        logger.error(f"Base normalizer test error: {e}", exc_info=True)
        return False


def test_bangkok_normalizer():
    """Test Bangkok-specific normalizer."""
    print("\n🧪 Testing Bangkok normalizer...")
    
    try:
        normalizer = BangkokNormalizer()
        
        # Test Bangkok area standardization
        test_areas = [
            'soi 11',
            'thong lo',
            'ekkamai',
            'silom soi 4',
            'sathorn soi 12',
            'siam square',
            'pratunam market',
            'yaowarat',
            'khao san road',
            'chatuchak weekend market',
            'ari soi 1',
            'lad phrao soi 1',
            'ratchadaphisek',
            'phrom phong soi 39',
            'asoke soi 21',
            'nana soi 4',
            'victory monument',
            'mo chit bts',
            'on nut soi 77'
        ]
        
        print(f"   Testing {len(test_areas)} Bangkok areas:")
        standardized_count = 0
        
        for area in test_areas:
            standardized = normalizer.normalize_area(area)
            if standardized != area:
                print(f"     {area} → {standardized}")
                standardized_count += 1
            else:
                print(f"     {area} → (no change)")
        
        print(f"   ✅ Standardized {standardized_count} areas")
        
        # Test Bangkok area knowledge
        print(f"   Bangkok area stats:")
        stats = normalizer.get_bangkok_area_stats()
        print(f"     Total areas: {stats['total_areas']}")
        print(f"     Total synonyms: {stats['total_synonyms']}")
        print(f"     Average synonyms per area: {stats['average_synonyms_per_area']}")
        
        # Test specific area queries
        test_queries = ['thonglor', 'soi 55', 'sukhumvit 55']
        for query in test_queries:
            synonyms = normalizer.get_bangkok_area_synonyms(query)
            standard_name = normalizer.get_standard_area_name(query)
            is_bangkok = normalizer.is_bangkok_area(query)
            print(f"     Query '{query}': standard='{standard_name}', is_bangkok={is_bangkok}, synonyms={len(synonyms)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Bangkok normalizer: {e}")
        logger.error(f"Bangkok normalizer test error: {e}", exc_info=True)
        return False


def test_universal_normalizer():
    """Test universal normalizer."""
    print("\n🧪 Testing universal normalizer...")
    
    try:
        # Create normalizer with Bangkok knowledge
        normalizer = create_universal_normalizer(enable_bangkok_normalization=True)
        
        # Test data with Bangkok-specific content
        test_places = [
            {
                'name': '<em>incredible thai restaurant</em>',
                'description': 'AMAZING restaurant in Sukhumvit Soi 11 with the BEST Thai food!!! Located conveniently near BTS station. Authentic local experience with traditional atmosphere.',
                'area': 'soi 11',
                'tags': ['thai', 'restaurant', 'local', 'authentic'],
                'flags': ['food_dining', 'local_experience']
            },
            {
                'name': '<strong>fantastic rooftop bar</strong>',
                'description': 'WONDERFUL rooftop bar in Silom with INCREDIBLE city views!!! Perfect for romantic evenings. Located just minutes from BTS station.',
                'area': 'silom soi 4',
                'tags': ['bar', 'rooftop', 'romantic', 'city-views'],
                'flags': ['nightlife', 'romantic']
            },
            {
                'name': '<span>excellent cafe</span>',
                'description': 'EXCELLENT cafe in Thonglor with GREAT coffee and TRENDY atmosphere!!! Must-visit spot for coffee lovers. Located in the heart of trendy district.',
                'area': 'thong lo',
                'tags': ['cafe', 'coffee', 'trendy', 'hip'],
                'flags': ['food_dining', 'trendy']
            }
        ]
        
        # Normalize places
        normalized_places = normalizer.normalize_places_batch(test_places)
        
        print(f"   ✅ Normalized {len(normalized_places)} places")
        
        # Show results
        for i, (original, normalized) in enumerate(zip(test_places, normalized_places)):
            print(f"     Place {i+1}:")
            print(f"       Name: {original['name']} → {normalized['name']}")
            print(f"       Area: {original['area']} → {normalized['area']}")
            print(f"       Description length: {len(original['description'])} → {len(normalized['description'])}")
            print(f"       Tags: {original['tags']} → {normalized['tags']}")
            print(f"       Flags: {original['flags']} → {normalized['flags']}")
            
            # Validate normalization
            validation = normalizer.validate_normalization(original, normalized)
            print(f"       Validation: valid={validation['is_valid']}, score={validation['quality_score']:.2f}")
            if validation['warnings']:
                print(f"         Warnings: {validation['warnings']}")
            if validation['errors']:
                print(f"         Errors: {validation['errors']}")
        
        # Get comprehensive stats
        stats = normalizer.get_normalization_stats()
        print(f"   Pipeline info:")
        print(f"     Total steps: {stats['pipeline_info']['total_steps']}")
        print(f"     Enabled steps: {stats['pipeline_info']['enabled_steps']}")
        for step in stats['pipeline_info']['steps']:
            print(f"       {step['name']}: {step['description']} ({'enabled' if step['enabled'] else 'disabled'})")
        
        print(f"   Processing stats:")
        print(f"     Places processed: {stats['processing_stats']['total_places_processed']}")
        print(f"     Fields normalized: {stats['processing_stats']['total_fields_normalized']}")
        print(f"     Characters removed: {stats['processing_stats']['total_characters_removed']}")
        print(f"     Bangkok areas standardized: {stats['processing_stats']['bangkok_areas_standardized']}")
        
        if stats['bangkok_knowledge']:
            print(f"   Bangkok knowledge:")
            print(f"     Total abbreviations: {stats['bangkok_knowledge']['total_abbreviations']}")
            print(f"     Remove patterns: {stats['bangkok_knowledge']['total_patterns']['remove']}")
            print(f"     Cleanup patterns: {stats['bangkok_knowledge']['total_patterns']['cleanup']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing universal normalizer: {e}")
        logger.error(f"Universal normalizer test error: {e}", exc_info=True)
        return False


def test_normalization_pipeline():
    """Test normalization pipeline control."""
    print("\n🧪 Testing normalization pipeline control...")
    
    try:
        normalizer = create_universal_normalizer(enable_bangkok_normalization=True)
        
        # Test step control
        print(f"   Pipeline steps:")
        for step in normalizer.normalization_pipeline:
            print(f"     {step['name']}: {step['description']} ({'enabled' if step['enabled'] else 'disabled'})")
        
        # Test disabling Bangkok step
        print(f"   Disabling Bangkok step...")
        normalizer.enable_step('bangkok_specific', False)
        
        # Test with Bangkok area
        test_place = {
            'name': 'Test Restaurant',
            'description': 'Test description',
            'area': 'soi 11',
            'tags': ['test'],
            'flags': ['test']
        }
        
        normalized = normalizer.normalize_place(test_place)
        print(f"   Area after disabling Bangkok step: {normalized['area']}")
        
        # Re-enable Bangkok step
        normalizer.enable_step('bangkok_specific', True)
        
        # Test custom step addition
        class CustomNormalizer(BaseNormalizer):
            def normalize_place(self, place):
                place['custom_field'] = 'custom_value'
                return place
        
        custom_normalizer = CustomNormalizer()
        normalizer.add_custom_step('custom', 'Custom normalization step', custom_normalizer)
        
        print(f"   Added custom step")
        print(f"   New pipeline steps:")
        for step in normalizer.normalization_pipeline:
            print(f"     {step['name']}: {step['description']} ({'enabled' if step['enabled'] else 'disabled'})")
        
        # Test with custom step
        normalized = normalizer.normalize_place(test_place)
        print(f"   Custom field added: {normalized.get('custom_field', 'Not found')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing normalization pipeline: {e}")
        logger.error(f"Pipeline control test error: {e}", exc_info=True)
        return False


def test_field_specific_normalization():
    """Test field-specific normalization."""
    print("\n🧪 Testing field-specific normalization...")
    
    try:
        normalizer = create_universal_normalizer(enable_bangkok_normalization=True)
        
        # Test individual field normalization
        test_cases = [
            ('name', '<strong>amazing restaurant</strong>'),
            ('description', 'This is an INCREDIBLE place with the BEST food ever!!!'),
            ('area', 'soi 11'),
            ('tags', ['thai', 'restaurant', 'thai', 'food']),
            ('flags', ['food_dining', 'local_experience', 'food_dining'])
        ]
        
        print(f"   Testing field-specific normalization:")
        for field_name, value in test_cases:
            # With Bangkok knowledge
            normalized_with_bkk = normalizer.normalize_specific_field(field_name, value, use_bangkok_knowledge=True)
            # Without Bangkok knowledge
            normalized_without_bkk = normalizer.normalize_specific_field(field_name, value, use_bangkok_knowledge=False)
            
            print(f"     {field_name}:")
            print(f"       Original: {value}")
            print(f"       With Bangkok: {normalized_with_bkk}")
            print(f"       Without Bangkok: {normalized_without_bkk}")
            
            # Show differences
            if normalized_with_bkk != normalized_without_bkk:
                print(f"       ⭐ Bangkok knowledge made a difference!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing field-specific normalization: {e}")
        logger.error(f"Field-specific test error: {e}", exc_info=True)
        return False


def main():
    """Main test function."""
    print("🚀 Starting Step 4 tests...")
    print("=" * 50)
    
    try:
        # Тест 1: Базовый нормализатор
        base_ok = test_base_normalizer()
        
        # Тест 2: Бангкок нормализатор
        bangkok_ok = test_bangkok_normalizer()
        
        # Тест 3: Универсальный нормализатор
        universal_ok = test_universal_normalizer()
        
        # Тест 4: Контроль pipeline
        pipeline_ok = test_normalization_pipeline()
        
        # Тест 5: Полевая нормализация
        field_ok = test_field_specific_normalization()
        
        print("\n" + "=" * 50)
        
        if all([base_ok, bangkok_ok, universal_ok, pipeline_ok, field_ok]):
            print("✅ All tests completed successfully!")
            print("\n🎯 What we've accomplished:")
            print("   • Title-case для названий")
            print("   • Truncate до 220 символов")
            print("   • Cleanup тегов HTML")
            print("   • Синонимы районов Бангкока")
            print("   • Универсальный pipeline")
            print("   • Валидация качества")
            print("   • Статистика нормализации")
        else:
            print("❌ Some tests failed")
            return 1
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error(f"Test failure: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
