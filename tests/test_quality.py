#!/usr/bin/env python3
"""
Unit tests for Quality Engine.
"""

import sys
import unittest
from pathlib import Path

# Добавляем src в Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quality import create_quality_engine, QualityLevel


class TestQualityEngine(unittest.TestCase):
    """Test cases for Quality Engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = create_quality_engine(min_completeness=0.7, require_photo=True)
        
        # Test data sets
        self.test_places = [
            # Place 1: Excellent quality
            {
                'id': 'place_1',
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
            },
            
            # Place 2: Good quality (missing some optional fields)
            {
                'id': 'place_2',
                'name': 'Thai Delight Cafe',
                'city': 'Bangkok',
                'domain': 'bk-magazine.com',
                'url': 'https://bk-magazine.com/cafe/thai-delight',
                'description': 'Cozy cafe serving delicious Thai coffee and snacks.',
                'address': '456 Silom Soi 4, Bangkok, Thailand',
                'geo_lat': 13.7500,
                'geo_lng': 100.5000,
                'tags': ['cafe', 'thai', 'coffee'],
                'flags': ['food_dining'],
                'photos': [{'url': 'https://example.com/cafe-photo.jpg'}],
                'image_url': 'https://example.com/cafe-main.jpg',
                'last_updated': '2024-12-20'
            },
            
            # Place 3: Acceptable quality (missing important fields)
            {
                'id': 'place_3',
                'name': 'Quick Thai Food',
                'city': 'Bangkok',
                'domain': 'timeout.com',
                'url': 'https://timeout.com/restaurant/quick-thai',
                'description': 'Fast Thai food for busy people.',
                'address': '789 Thonglor Soi 10, Bangkok',
                'tags': ['thai', 'fast-food'],
                'photos': [],
                'image_url': 'https://example.com/quick-photo.jpg'
            },
            
            # Place 4: Poor quality (missing many fields)
            {
                'id': 'place_4',
                'name': 'Thai Place',
                'city': 'Bangkok',
                'domain': 'unknown.com',
                'url': 'https://unknown.com/thai-place',
                'description': 'Thai food.',
                'photos': [],
                'last_updated': '2020-05-15'
            },
            
            # Place 5: Unacceptable quality (missing required fields)
            {
                'id': 'place_5',
                'name': '',
                'city': 'Bangkok',
                'domain': 'test.com',
                'url': 'invalid-url',
                'photos': []
            },
            
            # Place 6: No photos (should be rejected if require_photo=True)
            {
                'id': 'place_6',
                'name': 'Photo-Free Restaurant',
                'city': 'Bangkok',
                'domain': 'timeout.com',
                'url': 'https://timeout.com/restaurant/photo-free',
                'description': 'Great food but no photos available.',
                'address': '123 Test Street, Bangkok',
                'geo_lat': 13.7563,
                'geo_lng': 100.5018,
                'tags': ['restaurant', 'thai'],
                'photos': [],
                'last_updated': '2025-01-10'
            },
            
            # Place 7: High-quality photos
            {
                'id': 'place_7',
                'name': 'Photo Perfect Restaurant',
                'city': 'Bangkok',
                'domain': 'timeout.com',
                'url': 'https://timeout.com/restaurant/photo-perfect',
                'description': 'Restaurant with perfect photos.',
                'address': '456 Photo Street, Bangkok',
                'geo_lat': 13.7563,
                'geo_lng': 100.5018,
                'tags': ['restaurant', 'photography'],
                'photos': [
                    {
                        'url': 'https://example.com/high-res.jpg',
                        'width': 1920,
                        'height': 1080,
                        'alt_text': 'Beautiful restaurant interior'
                    },
                    {
                        'url': 'https://example.com/food-photo.jpg',
                        'width': 1600,
                        'height': 1200,
                        'alt_text': 'Delicious Thai food'
                    }
                ],
                'image_url': 'https://example.com/hd-main-photo.jpg',
                'last_updated': '2025-01-20'
            }
        ]
    
    def test_quality_engine_creation(self):
        """Test quality engine creation."""
        # Test default parameters
        engine = create_quality_engine()
        self.assertEqual(engine.min_completeness, 0.7)
        self.assertTrue(engine.require_photo)
        
        # Test custom parameters
        custom_engine = create_quality_engine(min_completeness=0.8, require_photo=False)
        self.assertEqual(custom_engine.min_completeness, 0.8)
        self.assertFalse(custom_engine.require_photo)
    
    def test_quality_metrics_creation(self):
        """Test quality metrics creation and calculation."""
        from quality import QualityMetrics
        
        # Test default metrics
        metrics = QualityMetrics()
        self.assertEqual(metrics.completeness, 0.0)
        self.assertEqual(metrics.photo_score, 0.0)
        self.assertEqual(metrics.get_overall_score(), 0.0)
        self.assertEqual(metrics.get_quality_level(), QualityLevel.UNACCEPTABLE)
        
        # Test custom metrics
        custom_metrics = QualityMetrics(
            completeness=0.9,
            photo_score=0.8,
            data_freshness=0.9,
            source_reliability=0.9,
            validation_score=0.9
        )
        
        overall_score = custom_metrics.get_overall_score()
        self.assertGreater(overall_score, 0.8)
        self.assertEqual(custom_metrics.get_quality_level(), QualityLevel.EXCELLENT)
    
    def test_completeness_calculation(self):
        """Test completeness score calculation."""
        # Test excellent completeness
        place_data = self.test_places[0]  # Excellent quality
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        self.assertGreater(metrics.completeness, 0.8)
        self.assertGreater(metrics.completeness, self.engine.min_completeness)
        
        # Test poor completeness
        place_data = self.test_places[3]  # Poor quality
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        self.assertLess(metrics.completeness, 0.8)
    
    def test_photo_score_calculation(self):
        """Test photo score calculation."""
        # Test place with multiple high-quality photos
        place_data = self.test_places[6]  # High-quality photos
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        self.assertGreater(metrics.photo_score, 0.7)
        
        # Test place with no photos
        place_data = self.test_places[5]  # No photos
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        self.assertEqual(metrics.photo_score, 0.0)
        
        # Test place with basic photos
        place_data = self.test_places[1]  # Basic photos
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        self.assertGreater(metrics.photo_score, 0.0)
        self.assertLess(metrics.photo_score, 0.8)
    
    def test_data_freshness_calculation(self):
        """Test data freshness score calculation."""
        # Test recent data
        place_data = self.test_places[0]  # 2025 data
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        self.assertGreater(metrics.data_freshness, 0.8)
        
        # Test old data
        place_data = self.test_places[3]  # 2020 data
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        self.assertLess(metrics.data_freshness, 0.6)
        
        # Test unknown freshness
        place_data = self.test_places[2]  # No last_updated
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        self.assertEqual(metrics.data_freshness, 0.5)
    
    def test_source_reliability_calculation(self):
        """Test source reliability score calculation."""
        # Test high-reliability source
        place_data = self.test_places[0]  # timeout.com
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        self.assertGreater(metrics.source_reliability, 0.8)
        
        # Test unknown source
        place_data = self.test_places[3]  # unknown.com
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        self.assertEqual(metrics.source_reliability, 0.5)
        
        # Test HTTPS bonus
        place_data = self.test_places[1]  # bk-magazine.com
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        # Should get bonus for HTTPS
        base_reliability = 0.85
        self.assertGreaterEqual(metrics.source_reliability, base_reliability)
    
    def test_validation_score_calculation(self):
        """Test validation score calculation."""
        # Test well-validated place
        place_data = self.test_places[0]  # Excellent quality
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        self.assertGreater(metrics.validation_score, 0.7)
        
        # Test poorly validated place
        place_data = self.test_places[4]  # Unacceptable quality
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        self.assertLess(metrics.validation_score, 0.5)
    
    def test_overall_quality_score(self):
        """Test overall quality score calculation."""
        # Test excellent place
        place_data = self.test_places[0]  # Excellent quality
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        overall_score = metrics.get_overall_score()
        self.assertGreater(overall_score, 0.8)
        self.assertEqual(metrics.get_quality_level(), QualityLevel.EXCELLENT)
        
        # Test poor place
        place_data = self.test_places[3]  # Poor quality
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        overall_score = metrics.get_overall_score()
        self.assertLess(overall_score, 0.7)
    
    def test_place_acceptability(self):
        """Test place acceptability determination."""
        # Test acceptable place
        place_data = self.test_places[0]  # Excellent quality
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        self.assertTrue(is_acceptable)
        
        # Test unacceptable place (low completeness)
        place_data = self.test_places[4]  # Unacceptable quality
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        self.assertFalse(is_acceptable)
        
        # Test place without photos (should be rejected if require_photo=True)
        place_data = self.test_places[5]  # No photos
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        self.assertFalse(is_acceptable)
    
    def test_photo_requirement_disabled(self):
        """Test behavior when photo requirement is disabled."""
        engine_no_photo = create_quality_engine(min_completeness=0.7, require_photo=False)
        
        # Test place without photos (should be accepted if require_photo=False)
        place_data = self.test_places[5]  # No photos
        is_acceptable, metrics, details = engine_no_photo.assess_place_quality(place_data)
        
        # Should be acceptable if other criteria are met
        if metrics.completeness >= 0.7 and metrics.get_overall_score() >= 0.6:
            self.assertTrue(is_acceptable)
    
    def test_completeness_threshold_adjustment(self):
        """Test completeness threshold adjustment."""
        # Test with higher threshold
        strict_engine = create_quality_engine(min_completeness=0.9, require_photo=True)
        
        # Test place that meets 0.7 but not 0.9
        place_data = self.test_places[2]  # Acceptable quality
        is_acceptable, metrics, details = strict_engine.assess_place_quality(place_data)
        
        # Should be rejected with higher threshold
        if metrics.completeness < 0.9:
            self.assertFalse(is_acceptable)
    
    def test_quality_details_generation(self):
        """Test quality details generation."""
        place_data = self.test_places[0]  # Excellent quality
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        # Check required fields
        self.assertIn('overall_score', details)
        self.assertIn('quality_level', details)
        self.assertIn('field_analysis', details)
        self.assertIn('recommendations', details)
        self.assertIn('warnings', details)
        
        # Check field analysis
        field_analysis = details['field_analysis']
        self.assertIn('name', field_analysis)
        self.assertIn('city', field_analysis)
        self.assertIn('description', field_analysis)
        
        # Check field presence
        name_analysis = field_analysis['name']
        self.assertTrue(name_analysis['present'])
        self.assertTrue(name_analysis['required'])
    
    def test_recommendations_and_warnings(self):
        """Test recommendations and warnings generation."""
        # Test place with issues
        place_data = self.test_places[3]  # Poor quality
        is_acceptable, metrics, details = self.engine.assess_place_quality(place_data)
        
        # Should have warnings
        self.assertGreater(len(details['warnings']), 0)
        
        # Should have recommendations
        self.assertGreater(len(details['recommendations']), 0)
        
        # Check specific warnings
        warnings = details['warnings']
        if metrics.completeness < self.engine.min_completeness:
            self.assertTrue(any('Completeness below threshold' in warning for warning in warnings))
    
    def test_statistics_tracking(self):
        """Test quality statistics tracking."""
        # Reset statistics
        self.engine.reset_statistics()
        
        # Assess a few places
        for place_data in self.test_places[:3]:
            self.engine.assess_place_quality(place_data)
        
        # Check statistics
        stats = self.engine.get_quality_statistics()
        
        self.assertEqual(stats['total_assessed'], 3)
        self.assertGreater(stats['total_assessed'], 0)
        self.assertGreaterEqual(stats['avg_completeness'], 0.0)
        self.assertGreaterEqual(stats['avg_photo_score'], 0.0)
        self.assertGreaterEqual(stats['avg_overall_score'], 0.0)
    
    def test_quality_summary(self):
        """Test quality summary generation."""
        # Assess some places first
        for place_data in self.test_places[:3]:
            self.engine.assess_place_quality(place_data)
        
        # Get summary
        summary = self.engine.get_quality_summary()
        
        # Check summary structure
        self.assertIn('total_assessed', summary)
        self.assertIn('acceptance_rate', summary)
        self.assertIn('rejection_rate', summary)
        self.assertIn('average_scores', summary)
        
        # Check average scores
        avg_scores = summary['average_scores']
        self.assertIn('completeness', avg_scores)
        self.assertIn('photo_score', avg_scores)
        self.assertIn('overall', avg_scores)
    
    def test_field_presence_detection(self):
        """Test field presence detection."""
        # Test string field
        place_data = {'name': 'Test Restaurant'}
        is_present = self.engine._is_field_present(place_data, 'name')
        self.assertTrue(is_present)
        
        # Test empty string
        place_data = {'name': ''}
        is_present = self.engine._is_field_present(place_data, 'name')
        self.assertFalse(is_present)
        
        # Test None value
        place_data = {'name': None}
        is_present = self.engine._is_field_present(place_data, 'name')
        self.assertFalse(is_present)
        
        # Test list field
        place_data = {'tags': ['tag1', 'tag2']}
        is_present = self.engine._is_field_present(place_data, 'tags')
        self.assertTrue(is_present)
        
        # Test empty list
        place_data = {'tags': []}
        is_present = self.engine._is_field_present(place_data, 'tags')
        self.assertFalse(is_present)
        
        # Test numeric field
        place_data = {'rating': 4.5}
        is_present = self.engine._is_field_present(place_data, 'rating')
        self.assertTrue(is_present)
    
    def test_url_validation(self):
        """Test URL validation."""
        # Test valid URLs
        valid_urls = [
            'https://example.com',
            'http://example.com',
            'https://www.example.com/path',
            'https://example.com:8080/path?param=value'
        ]
        
        for url in valid_urls:
            is_valid = self.engine._is_valid_url(url)
            self.assertTrue(is_valid, f"URL should be valid: {url}")
        
        # Test invalid URLs
        invalid_urls = [
            'not-a-url',
            'ftp://example.com',
            'example.com',
            'https://',
            ''
        ]
        
        for url in invalid_urls:
            is_valid = self.engine._is_field_present({'url': url}, 'url')
            self.assertFalse(is_valid, f"URL should be invalid: {url}")
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test with empty place data
        empty_place = {}
        is_acceptable, metrics, details = self.engine.assess_place_quality(empty_place)
        
        self.assertFalse(is_acceptable)
        self.assertEqual(metrics.completeness, 0.0)
        
        # Test with None values
        none_place = {
            'name': None,
            'city': None,
            'domain': None,
            'url': None
        }
        is_acceptable, metrics, details = self.engine.assess_place_quality(none_place)
        
        self.assertFalse(is_acceptable)
        
        # Test with very long strings
        long_place = {
            'name': 'A' * 1000,
            'city': 'Bangkok',
            'domain': 'test.com',
            'url': 'https://test.com',
            'description': 'B' * 2000
        }
        is_acceptable, metrics, details = self.engine.assess_place_quality(long_place)
        
        # Should handle gracefully
        self.assertIsInstance(metrics.completeness, float)
    
    def test_export_functionality(self):
        """Test quality report export functionality."""
        # Assess some places first
        for place_data in self.test_places[:3]:
            self.engine.assess_place_quality(place_data)
        
        # Export report
        export_file = "test_quality_report.txt"
        self.engine.export_quality_report(export_file, self.test_places[:3])
        
        # Check file was created
        import os
        self.assertTrue(os.path.exists(export_file))
        
        # Check file content
        with open(export_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("Quality Assessment Report", content)
            self.assertIn("Summary:", content)
            self.assertIn("Detailed Analysis:", content)
        
        # Clean up
        os.remove(export_file)
    
    def test_performance_with_large_dataset(self):
        """Test performance with larger dataset."""
        # Create larger dataset
        large_dataset = []
        for i in range(100):
            place_data = {
                'id': f'perf_test_{i}',
                'name': f'Restaurant {i}',
                'city': 'Bangkok',
                'domain': 'test.com',
                'url': f'https://test.com/restaurant/{i}',
                'description': f'Description for restaurant {i}',
                'address': f'Address {i}, Bangkok',
                'geo_lat': 13.7563 + (i * 0.001),
                'geo_lng': 100.5018 + (i * 0.001),
                'tags': [f'tag{i}'],
                'photos': [{'url': f'https://example.com/photo{i}.jpg'}],
                'last_updated': '2025-01-15'
            }
            large_dataset.append(place_data)
        
        # Measure performance
        import time
        start_time = time.time()
        
        for place_data in large_dataset:
            self.engine.assess_place_quality(place_data)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process 100 places in reasonable time (less than 1 second)
        self.assertLess(processing_time, 1.0)
        
        # Check results
        stats = self.engine.get_quality_statistics()
        self.assertEqual(stats['total_assessed'], 100)
        
        # Most should be acceptable
        self.assertGreater(stats['acceptance_rate'], 0.5)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestQualityEngine)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    # Exit with appropriate code
    sys.exit(len(result.failures) + len(result.errors))
