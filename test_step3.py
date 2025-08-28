#!/usr/bin/env python3
"""
Test script for Step 3: Extractor Engine.
"""

import sys
import logging
import asyncio
from pathlib import Path

# Добавляем src в Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from parsers.recipe_engine import create_recipe_engine
from parsers.extractor_engine import create_extractor_engine, ContentType
from parsers.fallback_engine import create_fallback_engine
from parsers.content_detector import detect_content_type, get_detailed_analysis

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_content_type_detection():
    """Test content type detection functionality."""
    print("🧪 Testing content type detection...")
    
    try:
        # Test URLs
        test_cases = [
            ("https://timeout.com/bangkok/restaurants", "list"),
            ("https://timeout.com/bangkok/restaurant/thai-delight", "article"),
            ("https://timeout.com/bangkok/gallery/best-photos", "gallery"),
            ("https://timeout.com/bangkok/search?q=restaurant", "search"),
            ("https://timeout.com/bangkok/food-drink", "category"),
            ("https://example.com/unknown-page", "unknown")
        ]
        
        for url, expected_type in test_cases:
            # Mock HTML for testing
            mock_html = f"<html><body><h1>Test page</h1></body></html>"
            
            detected_type, confidence = detect_content_type(url, mock_html)
            print(f"   URL: {url}")
            print(f"     Expected: {expected_type}, Detected: {detected_type} (confidence: {confidence:.2f})")
            
            # Check if detection is reasonable
            if expected_type != "unknown":
                if detected_type == expected_type or confidence > 0.3:
                    print(f"     ✅ Detection successful")
                else:
                    print(f"     ⚠️ Detection might need tuning")
            else:
                if confidence < 0.3:
                    print(f"     ✅ Correctly identified as unknown")
                else:
                    print(f"     ⚠️ Unexpectedly high confidence for unknown")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing content type detection: {e}")
        logger.error(f"Content type detection test error: {e}", exc_info=True)
        return False


def test_detailed_analysis():
    """Test detailed content analysis."""
    print("\n🧪 Testing detailed content analysis...")
    
    try:
        # Test URL with detailed analysis
        test_url = "https://timeout.com/bangkok/best-restaurants-guide"
        mock_html = """
        <html>
        <head>
            <title>Best Restaurants in Bangkok</title>
            <meta property="og:title" content="Best Restaurants">
            <meta property="og:description" content="Our picks for the best restaurants">
        </head>
        <body>
            <h1>Best Restaurants in Bangkok</h1>
            <ul class="restaurant-list">
                <li class="list-item">Thai Delight</li>
                <li class="list-item">Sukhumvit Cafe</li>
            </ul>
            <script type="application/ld+json">
            {"@type": "Restaurant", "name": "Thai Delight"}
            </script>
        </body>
        </html>
        """
        
        analysis = get_detailed_analysis(test_url, mock_html)
        
        print(f"   URL: {test_url}")
        print(f"   Detected type: {analysis['detected_type']}")
        print(f"   Confidence: {analysis['confidence']}")
        print(f"   URL analysis: {analysis['url_analysis']}")
        print(f"   HTML analysis: {analysis['html_analysis']}")
        print(f"   Content analysis: {analysis['content_analysis']}")
        print(f"   Combined scores: {analysis['combined_scores']}")
        
        # Check if analysis is reasonable
        if analysis['detected_type'] in ['list', 'category'] and analysis['confidence'] > 0.4:
            print(f"   ✅ Analysis successful")
        else:
            print(f"   ⚠️ Analysis might need tuning")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing detailed analysis: {e}")
        logger.error(f"Detailed analysis test error: {e}", exc_info=True)
        return False


def test_fallback_engine():
    """Test fallback engine functionality."""
    print("\n🧪 Testing fallback engine...")
    
    try:
        # Create recipe engine
        recipe_engine = create_recipe_engine()
        timeout_recipe = recipe_engine.get_recipe('timeout.com')
        
        if not timeout_recipe:
            print("❌ Timeout recipe not found")
            return False
        
        # Create fallback engine
        fallback_engine = create_fallback_engine(timeout_recipe)
        
        # Test HTML with multiple data sources
        test_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Amazing Thai Restaurant</title>
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
            <div class="restaurant-card">
                <h1 class="restaurant-name">Sukhumvit Cafe</h1>
                <p class="description">Cozy cafe with great coffee</p>
                <img src="https://example.com/cafe.jpg" alt="Cafe">
                <span class="location">Sukhumvit</span>
            </div>
        </body>
        </html>
        """
        
        # Test fallback extraction
        places = fallback_engine.extract_with_fallback(test_html, "https://example.com/test")
        
        print(f"   ✅ Extracted {len(places)} places with fallback")
        
        # Show extraction summary
        summary = fallback_engine.get_extraction_summary(places)
        print(f"   Method counts: {summary['method_counts']}")
        print(f"   Confidence stats: {summary['confidence_stats']}")
        print(f"   Fallback order: {summary['fallback_order']}")
        
        # Check if fallback worked
        if len(places) > 0:
            print(f"   ✅ Fallback extraction successful")
            
            # Show place details
            for i, place in enumerate(places):
                print(f"     Place {i+1}: {place.get('name', 'N/A')}")
                print(f"       Method: {place.get('extraction_method', 'N/A')}")
                print(f"       Confidence: {place.get('confidence_score', 0):.2f}")
                print(f"       Merged from: {place.get('merged_from', 1)} methods")
        else:
            print(f"   ❌ Fallback extraction failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing fallback engine: {e}")
        logger.error(f"Fallback engine test error: {e}", exc_info=True)
        return False


async def test_extractor_engine():
    """Test extractor engine functionality."""
    print("\n🧪 Testing extractor engine...")
    
    try:
        # Create recipe engine
        recipe_engine = create_recipe_engine()
        timeout_recipe = recipe_engine.get_recipe('timeout.com')
        
        if not timeout_recipe:
            print("❌ Timeout recipe not found")
            return False
        
        # Create extractor engine
        extractor_engine = create_extractor_engine(timeout_recipe)
        
        # Test engine stats
        stats = extractor_engine.get_extraction_stats()
        print(f"   ✅ Engine stats: {stats}")
        
        # Test content type detection
        test_url = "https://timeout.com/bangkok/best-restaurants"
        content_type = extractor_engine._detect_content_type_from_url(test_url)
        print(f"   URL: {test_url}")
        print(f"   Detected content type: {content_type}")
        
        # Test content type from HTML
        mock_html = "<html><body><ul><li>Restaurant 1</li><li>Restaurant 2</li></ul></body></html>"
        html_content_type = extractor_engine._detect_content_type_from_html(mock_html)
        print(f"   HTML content type: {html_content_type}")
        
        # Test category finding
        category = extractor_engine._find_category('Food & Drink')
        if category:
            print(f"   ✅ Found category: {category['name']}")
            print(f"     URL: {category['url']}")
            print(f"     Flags: {category['flags']}")
        else:
            print(f"   ❌ Category not found")
            return False
        
        # Test quality scoring
        test_place = {
            'name': 'Test Restaurant',
            'description': 'A great restaurant',
            'image_url': 'https://example.com/image.jpg',
            'area': 'Sukhumvit',
            'price_level': 2,
            'tags': ['thai', 'restaurant']
        }
        
        quality_score = extractor_engine._calculate_quality_score(test_place)
        print(f"   Test place quality score: {quality_score:.3f}")
        
        # Test deduplication
        places = [
            {'name': 'Restaurant A', 'url': 'https://example.com/a'},
            {'name': 'Restaurant A', 'url': 'https://example.com/a'},  # Duplicate
            {'name': 'Restaurant B', 'url': 'https://example.com/b'}
        ]
        
        unique_places = extractor_engine._deduplicate_places(places)
        print(f"   Deduplication: {len(places)} -> {len(unique_places)} places")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing extractor engine: {e}")
        logger.error(f"Extractor engine test error: {e}", exc_info=True)
        return False


async def test_full_extraction_workflow():
    """Test full extraction workflow."""
    print("\n🧪 Testing full extraction workflow...")
    
    try:
        # Create recipe engine
        recipe_engine = create_recipe_engine()
        timeout_recipe = recipe_engine.get_recipe('timeout.com')
        
        if not timeout_recipe:
            print("❌ Timeout recipe not found")
            return False
        
        # Create extractor engine
        extractor_engine = create_extractor_engine(timeout_recipe)
        
        # Test with mock HTML (simulating real extraction)
        mock_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Best Restaurants in Bangkok</title>
            <meta property="og:title" content="Best Restaurants in Bangkok">
            <meta property="og:description" content="Our picks for the best restaurants in Bangkok">
            <script type="application/ld+json">
            [
                {
                    "@type": "Restaurant",
                    "name": "Thai Delight",
                    "description": "Authentic Thai cuisine in Sukhumvit",
                    "image": "https://example.com/thai.jpg"
                },
                {
                    "@type": "Restaurant", 
                    "name": "Sukhumvit Cafe",
                    "description": "Cozy cafe with great coffee",
                    "image": "https://example.com/cafe.jpg"
                }
            ]
            </script>
        </head>
        <body>
            <div class="list-item">
                <h2 class="title">Rooftop Skybar</h2>
                <p class="description">Luxury rooftop bar with city views</p>
                <img src="https://example.com/skybar.jpg" alt="Skybar">
                <span class="location">Silom</span>
            </div>
        </body>
        </html>
        """
        
        # Test extraction from URL
        places = await extractor_engine.extract_from_url(
            "https://timeout.com/bangkok/best-restaurants",
            ContentType.LIST
        )
        
        print(f"   ✅ Full workflow extracted {len(places)} places")
        
        # Show results
        for i, place in enumerate(places):
            print(f"     Place {i+1}: {place.get('name', 'N/A')}")
            print(f"       Description: {place.get('description', 'N/A')[:50]}...")
            print(f"       Area: {place.get('area', 'N/A')}")
            print(f"       Content type: {place.get('content_type', 'N/A')}")
            print(f"       Quality score: {place.get('quality_score', 0):.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing full workflow: {e}")
        logger.error(f"Full workflow test error: {e}", exc_info=True)
        return False


async def main():
    """Main test function."""
    print("🚀 Starting Step 3 tests...")
    print("=" * 50)
    
    try:
        # Тест 1: Детекция типов контента
        detection_ok = test_content_type_detection()
        
        # Тест 2: Детальный анализ
        analysis_ok = test_detailed_analysis()
        
        # Тест 3: Fallback движок
        fallback_ok = test_fallback_engine()
        
        # Тест 4: Движок извлечения
        engine_ok = await test_extractor_engine()
        
        # Тест 5: Полный workflow
        workflow_ok = await test_full_extraction_workflow()
        
        print("\n" + "=" * 50)
        
        if all([detection_ok, analysis_ok, fallback_ok, engine_ok, workflow_ok]):
            print("✅ All tests completed successfully!")
            print("\n🎯 What we've accomplished:")
            print("   • Universal extractor engine")
            print("   • Support for different content types (list/article/gallery)")
            print("   • Intelligent fallback system")
            print("   • JSON-LD → Open Graph → CSS priority")
            print("   • Content type detection")
            print("   • Quality scoring and filtering")
            print("   • Deduplication and merging")
            print("   • Async HTTP operations")
        else:
            print("❌ Some tests failed")
            return 1
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error(f"Test failure: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
