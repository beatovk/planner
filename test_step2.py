#!/usr/bin/env python3
"""
Test script for Step 2: Recipes v1.
"""

import sys
import logging
from pathlib import Path

# Добавляем src в Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from parsers.recipe_engine import create_recipe_engine, SourceRecipe
from parsers.extractors import create_extractor

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_recipe_loading():
    """Test recipe loading from YAML files."""
    print("🧪 Testing recipe loading...")
    
    try:
        # Создаем движок рецептов
        engine = create_recipe_engine()
        print(f"✅ Recipe engine created")
        
        # Получаем статистику
        stats = engine.get_recipe_stats()
        print(f"   Total recipes: {stats['total_recipes']}")
        print(f"   Domains: {stats['domains']}")
        print(f"   Total categories: {stats['total_categories']}")
        
        # Проверяем загруженные рецепты
        for domain, recipe in engine.recipes.items():
            print(f"\n📋 Recipe: {recipe.name} ({domain})")
            print(f"   Base URL: {recipe.base_url}")
            print(f"   Language: {recipe.language}")
            print(f"   Extraction priority: {recipe.extraction_priority}")
            print(f"   JSON-LD enabled: {recipe.jsonld_enabled}")
            print(f"   Open Graph enabled: {recipe.og_enabled}")
            print(f"   CSS enabled: {recipe.css_enabled}")
            print(f"   Categories: {len(recipe.categories)}")
            print(f"   Quality threshold: {recipe.min_quality_score}")
            
            # Показываем категории
            for i, cat in enumerate(recipe.categories[:3]):  # Показываем первые 3
                print(f"     {i+1}. {cat['name']} -> {cat['flags']}")
            if len(recipe.categories) > 3:
                print(f"     ... and {len(recipe.categories) - 3} more")
        
        return engine
        
    except Exception as e:
        print(f"❌ Error testing recipe loading: {e}")
        logger.error(f"Recipe loading test error: {e}", exc_info=True)
        return None


def test_recipe_validation():
    """Test recipe validation."""
    print("\n🧪 Testing recipe validation...")
    
    try:
        engine = create_recipe_engine()
        
        # Проверяем валидацию всех рецептов
        errors = engine.validate_all_recipes()
        
        if errors:
            print("❌ Recipe validation errors found:")
            for domain, domain_errors in errors.items():
                print(f"   {domain}:")
                for error in domain_errors:
                    print(f"     - {error}")
        else:
            print("✅ All recipes are valid!")
        
        return len(errors) == 0
        
    except Exception as e:
        print(f"❌ Error testing recipe validation: {e}")
        logger.error(f"Recipe validation test error: {e}", exc_info=True)
        return False


def test_extractor_creation():
    """Test extractor creation from recipes."""
    print("\n🧪 Testing extractor creation...")
    
    try:
        engine = create_recipe_engine()
        
        for domain, recipe in engine.recipes.items():
            print(f"\n🔧 Creating extractor for {recipe.name}...")
            
            # Создаем экстрактор
            extractor = create_extractor(recipe)
            print(f"   ✅ Extractor created")
            print(f"   Methods: {extractor.extractors}")
            
            # Проверяем методы извлечения
            methods = recipe.get_extraction_methods()
            print(f"   Priority order: {methods}")
            
            # Проверяем селекторы
            if recipe.css_enabled:
                print(f"   CSS container: {recipe.css_selectors.get('container', 'N/A')}")
                print(f"   CSS name: {recipe.css_selectors.get('name', 'N/A')}")
            
            if recipe.jsonld_enabled:
                print(f"   JSON-LD types: {recipe.jsonld_selectors.get('place_type', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing extractor creation: {e}")
        logger.error(f"Extractor creation test error: {e}", exc_info=True)
        return False


def test_recipe_operations():
    """Test recipe operations."""
    print("\n🧪 Testing recipe operations...")
    
    try:
        engine = create_recipe_engine()
        
        # Тестируем получение рецепта по домену
        timeout_recipe = engine.get_recipe('timeout.com')
        if timeout_recipe:
            print(f"✅ Found Timeout recipe: {timeout_recipe.name}")
            
            # Тестируем получение категорий
            categories = timeout_recipe.get_category_urls()
            print(f"   Categories: {len(categories)}")
            
            # Тестируем получение флагов для категории
            food_flags = timeout_recipe.get_flags_for_category('Food & Drink')
            print(f"   Food & Drink flags: {food_flags}")
            
            # Тестируем методы извлечения
            methods = timeout_recipe.get_extraction_methods()
            print(f"   Extraction methods: {methods}")
        
        # Тестируем получение рецепта по имени
        bk_recipe = engine.get_recipe_by_name('BK Magazine')
        if bk_recipe:
            print(f"✅ Found BK Magazine recipe: {bk_recipe.domain}")
        
        # Тестируем статистику
        stats = engine.get_recipe_stats()
        print(f"✅ Recipe stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing recipe operations: {e}")
        logger.error(f"Recipe operations test error: {e}", exc_info=True)
        return False


def test_extractor_functionality():
    """Test extractor functionality with sample HTML."""
    print("\n🧪 Testing extractor functionality...")
    
    try:
        engine = create_recipe_engine()
        timeout_recipe = engine.get_recipe('timeout.com')
        
        if not timeout_recipe:
            print("❌ Timeout recipe not found")
            return False
        
        # Создаем экстрактор
        extractor = create_extractor(timeout_recipe)
        
        # Тестовый HTML
        test_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Restaurant</title>
            <meta property="og:title" content="Amazing Thai Restaurant">
            <meta property="og:description" content="Best Thai food in Bangkok">
            <meta property="og:image" content="https://example.com/image.jpg">
            <script type="application/ld+json">
            {
                "@type": "Restaurant",
                "name": "Thai Delight",
                "description": "Authentic Thai cuisine in Sukhumvit",
                "image": "https://example.com/thai.jpg",
                "url": "https://example.com/thai-delight"
            }
            </script>
        </head>
        <body>
            <div class="list-item">
                <h2 class="title">Sukhumvit Cafe</h2>
                <p class="description">Cozy cafe with great coffee</p>
                <img src="https://example.com/cafe.jpg" alt="Cafe">
                <a href="https://example.com/cafe">Visit Cafe</a>
                <span class="location">Sukhumvit</span>
            </div>
        </body>
        </html>
        """
        
        # Тестируем извлечение
        places = extractor.extract(test_html, "https://example.com/test")
        print(f"✅ Extracted {len(places)} places")
        
        for i, place in enumerate(places):
            print(f"   Place {i+1}:")
            print(f"     Name: {place.get('name', 'N/A')}")
            print(f"     Description: {place.get('description', 'N/A')[:50]}...")
            print(f"     Image: {place.get('image_url', 'N/A')}")
            print(f"     Source: {place.get('source', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing extractor functionality: {e}")
        logger.error(f"Extractor functionality test error: {e}", exc_info=True)
        return False


def test_recipe_export():
    """Test recipe export functionality."""
    print("\n🧪 Testing recipe export...")
    
    try:
        engine = create_recipe_engine()
        
        # Экспортируем рецепт Timeout
        output_path = "test_timeout_export.yaml"
        success = engine.export_recipe('timeout.com', output_path)
        
        if success:
            print(f"✅ Recipe exported to: {output_path}")
            
            # Проверяем что файл создан
            if Path(output_path).exists():
                print(f"   File size: {Path(output_path).stat().st_size} bytes")
                
                # Удаляем тестовый файл
                Path(output_path).unlink()
                print(f"   Test file cleaned up")
            else:
                print(f"❌ Export file not found")
                return False
        else:
            print(f"❌ Recipe export failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing recipe export: {e}")
        logger.error(f"Recipe export test error: {e}", exc_info=True)
        return False


def main():
    """Main test function."""
    print("🚀 Starting Step 2 tests...")
    print("=" * 50)
    
    try:
        # Тест 1: Загрузка рецептов
        engine = test_recipe_loading()
        if not engine:
            return 1
        
        # Тест 2: Валидация рецептов
        validation_ok = test_recipe_validation()
        
        # Тест 3: Создание экстракторов
        extractor_ok = test_extractor_creation()
        
        # Тест 4: Операции с рецептами
        operations_ok = test_recipe_operations()
        
        # Тест 5: Функциональность экстракторов
        functionality_ok = test_extractor_functionality()
        
        # Тест 6: Экспорт рецептов
        export_ok = test_recipe_export()
        
        print("\n" + "=" * 50)
        
        if all([validation_ok, extractor_ok, operations_ok, functionality_ok, export_ok]):
            print("✅ All tests completed successfully!")
            print("\n🎯 What we've accomplished:")
            print("   • YAML recipe system for sources")
            print("   • Timeout Bangkok recipe (JSON-LD priority)")
            print("   • BK Magazine recipe (CSS priority)")
            print("   • Recipe validation engine")
            print("   • Universal extractor with multiple methods")
            print("   • JSON-LD, Open Graph, and CSS extractors")
            print("   • Recipe export functionality")
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
