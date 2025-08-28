#!/usr/bin/env python3
"""
Unit tests for Deduplication Engine.
"""

import sys
import unittest
from pathlib import Path

# Добавляем src в Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dedup import create_dedup_engine, DedupCandidate


class TestDedupEngine(unittest.TestCase):
    """Test cases for Deduplication Engine."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = create_dedup_engine(fuzzy_threshold=0.86, geo_tolerance=0.001)

        # Test data sets
        self.test_places = [
            # Place 1: Basic restaurant
            {
                "id": "place_1",
                "name": "Amazing Thai Restaurant",
                "city": "Bangkok",
                "domain": "timeout.com",
                "geo_lat": 13.7563,
                "geo_lng": 100.5018,
                "address": "123 Sukhumvit Soi 11, Bangkok, Thailand",
                "url": "https://timeout.com/bangkok/restaurant/amazing-thai",
            },
            # Place 2: Same restaurant, different name format
            {
                "id": "place_2",
                "name": "The Amazing Thai Restaurant",
                "city": "Bangkok",
                "domain": "timeout.com",
                "geo_lat": 13.7563,
                "geo_lng": 100.5018,
                "address": "123 Sukhumvit Soi 11, Bangkok, Thailand",
                "url": "https://timeout.com/bangkok/restaurant/amazing-thai-2",
            },
            # Place 3: Similar name, different location
            {
                "id": "place_3",
                "name": "Amazing Thai Restaurant",
                "city": "Bangkok",
                "domain": "timeout.com",
                "geo_lat": 13.7500,
                "geo_lng": 100.5000,
                "address": "456 Silom Soi 4, Bangkok, Thailand",
                "url": "https://timeout.com/bangkok/restaurant/amazing-thai-3",
            },
            # Place 4: Different restaurant, similar name
            {
                "id": "place_4",
                "name": "Amazing Thai Cafe",
                "city": "Bangkok",
                "domain": "bk-magazine.com",
                "geo_lat": 13.7563,
                "geo_lng": 100.5018,
                "address": "789 Thonglor Soi 10, Bangkok, Thailand",
                "url": "https://bk-magazine.com/bangkok/cafe/amazing-thai",
            },
            # Place 5: Same name, different city
            {
                "id": "place_5",
                "name": "Amazing Thai Restaurant",
                "city": "Chiang Mai",
                "domain": "timeout.com",
                "geo_lat": 18.7883,
                "geo_lng": 98.9853,
                "address": "123 Nimman Road, Chiang Mai, Thailand",
                "url": "https://timeout.com/chiang-mai/restaurant/amazing-thai",
            },
            # Place 6: Different domain, same content
            {
                "id": "place_6",
                "name": "Amazing Thai Restaurant",
                "city": "Bangkok",
                "domain": "bk-magazine.com",
                "geo_lat": 13.7563,
                "geo_lng": 100.5018,
                "address": "123 Sukhumvit Soi 11, Bangkok, Thailand",
                "url": "https://bk-magazine.com/bangkok/restaurant/amazing-thai",
            },
            # Place 7: Very similar name (fuzzy match)
            {
                "id": "place_7",
                "name": "Amazing Thai Restaurnt",  # Typo: missing 'a'
                "city": "Bangkok",
                "domain": "timeout.com",
                "geo_lat": 13.7563,
                "geo_lng": 100.5018,
                "address": "123 Sukhumvit Soi 11, Bangkok, Thailand",
                "url": "https://timeout.com/bangkok/restaurant/amazing-thai-7",
            },
            # Place 8: Different name, same address
            {
                "id": "place_8",
                "name": "Thai Delight Restaurant",
                "city": "Bangkok",
                "domain": "timeout.com",
                "geo_lat": 13.7563,
                "geo_lng": 100.5018,
                "address": "123 Sukhumvit Soi 11, Bangkok, Thailand",
                "url": "https://timeout.com/bangkok/restaurant/thai-delight",
            },
            # Place 9: Same name, different address format
            {
                "id": "place_9",
                "name": "Amazing Thai Restaurant",
                "city": "Bangkok",
                "domain": "timeout.com",
                "geo_lat": 13.7563,
                "geo_lng": 100.5018,
                "address": "123 Sukhumvit Soi 11, Bangkok, Thailand",
                "url": "https://timeout.com/bangkok/restaurant/amazing-thai-9",
            },
            # Place 10: Completely different
            {
                "id": "place_10",
                "name": "Sushi Master",
                "city": "Bangkok",
                "domain": "timeout.com",
                "geo_lat": 13.7500,
                "geo_lng": 100.5000,
                "address": "456 Silom Soi 4, Bangkok, Thailand",
                "url": "https://timeout.com/bangkok/restaurant/sushi-master",
            },
        ]

    def test_dedup_candidate_creation(self):
        """Test DedupCandidate creation and processing."""
        place_data = self.test_places[0]
        candidate = DedupCandidate(
            place_id=place_data["id"],
            name=place_data["name"],
            city=place_data["city"],
            domain=place_data["domain"],
            geo_lat=place_data["geo_lat"],
            geo_lng=place_data["geo_lng"],
            address=place_data["address"],
            url=place_data["url"],
            raw_data=place_data,
        )

        # Check basic fields
        self.assertEqual(candidate.place_id, "place_1")
        self.assertEqual(candidate.name, "Amazing Thai Restaurant")
        self.assertEqual(candidate.city, "Bangkok")
        self.assertEqual(candidate.domain, "timeout.com")

        # Check computed fields
        self.assertIsNotNone(candidate.identity_key)
        self.assertIsNotNone(candidate.address_hash)
        self.assertEqual(candidate.name_normalized, "amazing thai")

        # Check geo coordinates
        self.assertEqual(candidate.geo_lat, 13.7563)
        self.assertEqual(candidate.geo_lng, 100.5018)

    def test_name_normalization(self):
        """Test name normalization functionality."""
        test_cases = [
            ("The Amazing Thai Restaurant", "amazing thai"),
            ("Best Thai Cafe", "thai"),
            ("Famous Thai Bar", "thai"),
            ("Thai Delight", "thai delight"),
            ("Restaurant Thai", "restaurant thai"),
            ("Thai Restaurant", "thai"),
            ("   Amazing   Thai   ", "amazing thai"),
            ("", ""),
            (None, ""),
        ]

        for input_name, expected_normalized in test_cases:
            candidate = DedupCandidate(
                place_id="test",
                name=input_name or "",
                city="Bangkok",
                domain="test.com",
                geo_lat=None,
                geo_lng=None,
                address=None,
                url=None,
                raw_data={},
            )

            if input_name:
                self.assertEqual(candidate.name_normalized, expected_normalized)
            else:
                self.assertEqual(candidate.name_normalized, "")

    def test_identity_key_generation(self):
        """Test identity key generation."""
        # Same core data should generate same key
        place1 = DedupCandidate(
            place_id="test1",
            name="Amazing Thai Restaurant",
            city="Bangkok",
            domain="timeout.com",
            geo_lat=13.7563,
            geo_lng=100.5018,
            address="123 Sukhumvit",
            url="https://test.com",
            raw_data={},
        )

        place2 = DedupCandidate(
            place_id="test2",
            name="Amazing Thai Restaurant",
            city="Bangkok",
            domain="timeout.com",
            geo_lat=13.7563,
            geo_lng=100.5018,
            address="Different address",
            url="https://different.com",
            raw_data={},
        )

        # Same identity key (core fields + geo are same)
        self.assertEqual(place1.identity_key, place2.identity_key)

        # Different geo should generate different key
        place3 = DedupCandidate(
            place_id="test3",
            name="Amazing Thai Restaurant",
            city="Bangkok",
            domain="timeout.com",
            geo_lat=13.7500,  # Different lat
            geo_lng=100.5000,  # Different lng
            address="123 Sukhumvit",
            url="https://test.com",
            raw_data={},
        )

        self.assertNotEqual(place1.identity_key, place3.identity_key)

    def test_address_normalization(self):
        """Test address normalization functionality."""
        test_cases = [
            ("123 Sukhumvit Soi 11, Bangkok, Thailand", "123 sukhumvit soi 11"),
            ("456 Silom Road, Bangkok, Thailand", "456 silom"),
            ("789 Thonglor Soi 10, Bangkok", "789 thonglor soi 10"),
            ("Building A, Floor 3, Room 301", "building a floor 3 room 301"),
            ("", ""),
            (None, ""),
        ]

        for input_address, expected_normalized in test_cases:
            candidate = DedupCandidate(
                place_id="test",
                name="Test Place",
                city="Bangkok",
                domain="test.com",
                geo_lat=None,
                geo_lng=None,
                address=input_address,
                url=None,
                raw_data={},
            )

            if input_address:
                self.assertEqual(
                    candidate.address_hash, candidate.address_hash
                )  # Should be consistent
            else:
                self.assertEqual(candidate.address_hash, "")

    def test_basic_deduplication(self):
        """Test basic deduplication functionality."""
        # Add first place
        is_duplicate, duplicate_id = self.engine.add_place(self.test_places[0])
        self.assertFalse(is_duplicate)
        self.assertIsNone(duplicate_id)

        # Add same place again (should be duplicate)
        is_duplicate, duplicate_id = self.engine.add_place(self.test_places[0])
        self.assertTrue(is_duplicate)
        self.assertEqual(duplicate_id, "place_1")

        # Check stats
        stats = self.engine.get_dedup_statistics()
        self.assertEqual(stats["total_processed"], 1)
        self.assertEqual(stats["duplicates_found"], 1)
        self.assertEqual(stats["identity_matches"], 1)

    def test_identity_key_deduplication(self):
        """Test deduplication using identity keys."""
        # Add places with same core data but different addresses
        is_duplicate, duplicate_id = self.engine.add_place(
            self.test_places[0]
        )  # place_1
        self.assertFalse(is_duplicate)

        is_duplicate, duplicate_id = self.engine.add_place(
            self.test_places[1]
        )  # place_2 (same core data)
        self.assertTrue(is_duplicate)
        self.assertEqual(duplicate_id, "place_1")

        # Check stats
        stats = self.engine.get_dedup_statistics()
        self.assertEqual(stats["identity_matches"], 1)
        self.assertEqual(stats["total_processed"], 1)
        self.assertEqual(stats["duplicates_found"], 1)

    def test_fuzzy_name_deduplication(self):
        """Test deduplication using fuzzy name matching."""
        # Add place with typo in name
        is_duplicate, duplicate_id = self.engine.add_place(
            self.test_places[0]
        )  # place_1
        self.assertFalse(is_duplicate)

        is_duplicate, duplicate_id = self.engine.add_place(
            self.test_places[6]
        )  # place_7 (typo: "Restaurnt")
        self.assertTrue(is_duplicate)
        self.assertEqual(duplicate_id, "place_1")

        # Check stats
        stats = self.engine.get_dedup_statistics()
        self.assertEqual(stats["fuzzy_matches"], 1)

    def test_address_deduplication(self):
        """Test deduplication using address matching."""
        # Add places with same address but different names
        is_duplicate, duplicate_id = self.engine.add_place(
            self.test_places[0]
        )  # place_1
        self.assertFalse(is_duplicate)

        is_duplicate, duplicate_id = self.engine.add_place(
            self.test_places[7]
        )  # place_8 (same address, different name)
        self.assertTrue(is_duplicate)
        self.assertEqual(duplicate_id, "place_1")

        # Check stats
        stats = self.engine.get_dedup_statistics()
        self.assertEqual(stats["address_matches"], 1)

    def test_geo_deduplication(self):
        """Test deduplication using geographic proximity."""
        # Add places with same coordinates
        is_duplicate, duplicate_id = self.engine.add_place(
            self.test_places[0]
        )  # place_1
        self.assertFalse(is_duplicate)

        is_duplicate, duplicate_id = self.engine.add_place(
            self.test_places[8]
        )  # place_9 (same geo, different address format)
        self.assertTrue(is_duplicate)
        self.assertEqual(duplicate_id, "place_1")

        # Check stats
        stats = self.engine.get_dedup_statistics()
        self.assertEqual(stats["geo_matches"], 1)

    def test_complex_deduplication_scenarios(self):
        """Test complex deduplication scenarios."""
        # Add multiple places
        places_added = []
        duplicates_found = 0

        for place_data in self.test_places:
            is_duplicate, duplicate_id = self.engine.add_place(place_data)

            if is_duplicate:
                duplicates_found += 1
                self.assertIsNotNone(duplicate_id)
                self.assertIn(duplicate_id, places_added)
            else:
                places_added.append(place_data["id"])

        # Check results
        self.assertGreater(duplicates_found, 0)
        self.assertLess(len(places_added), len(self.test_places))

        # Check stats
        stats = self.engine.get_dedup_statistics()
        self.assertEqual(stats["total_processed"], len(places_added))
        self.assertEqual(stats["duplicates_found"], duplicates_found)
        self.assertGreater(stats["dedup_rate"], 0.0)

    def test_duplicate_groups(self):
        """Test duplicate group detection."""
        # Add all test places
        for place_data in self.test_places:
            self.engine.add_place(place_data)

        # Get duplicate groups
        duplicate_groups = self.engine.get_duplicate_groups()

        # Should have some duplicate groups
        self.assertGreater(len(duplicate_groups), 0)

        # Check that groups contain duplicates
        for group in duplicate_groups:
            self.assertGreater(len(group), 1)

            # All places in group should be similar
            first_place_id = group[0]
            first_place = self.engine.processed_places[first_place_id]

            for other_place_id in group[1:]:
                other_place = self.engine.processed_places[other_place_id]
                # Should have some similarity (name, address, or geo)
                self.assertTrue(
                    (first_place.name_normalized == other_place.name_normalized)
                    or (first_place.address_hash == other_place.address_hash)
                    or (first_place.identity_key == other_place.identity_key)
                )

    def test_different_cities_not_duplicates(self):
        """Test that places in different cities are not considered duplicates."""
        # Add place in Bangkok
        is_duplicate, duplicate_id = self.engine.add_place(
            self.test_places[0]
        )  # Bangkok
        self.assertFalse(is_duplicate)

        # Add same name in Chiang Mai (should not be duplicate)
        is_duplicate, duplicate_id = self.engine.add_place(
            self.test_places[4]
        )  # Chiang Mai
        self.assertFalse(is_duplicate)

        # Check stats
        stats = self.engine.get_dedup_statistics()
        self.assertEqual(stats["total_processed"], 2)
        self.assertEqual(stats["duplicates_found"], 0)

    def test_different_domains_not_duplicates(self):
        """Test that places from different domains are not automatically duplicates."""
        # Add place from timeout.com
        is_duplicate, duplicate_id = self.engine.add_place(
            self.test_places[0]
        )  # timeout.com
        self.assertFalse(is_duplicate)

        # Add same place from bk-magazine.com (should not be duplicate by default)
        is_duplicate, duplicate_id = self.engine.add_place(
            self.test_places[5]
        )  # bk-magazine.com
        self.assertFalse(is_duplicate)

        # Check stats
        stats = self.engine.get_dedup_statistics()
        self.assertEqual(stats["total_processed"], 2)
        self.assertEqual(stats["duplicates_found"], 0)

    def test_fuzzy_threshold_adjustment(self):
        """Test fuzzy threshold adjustment."""
        # Create engine with higher threshold
        strict_engine = create_dedup_engine(fuzzy_threshold=0.95, geo_tolerance=0.001)

        # Add place
        is_duplicate, duplicate_id = strict_engine.add_place(
            self.test_places[0]
        )  # place_1
        self.assertFalse(is_duplicate)

        # Add place with typo (should not be duplicate with higher threshold)
        is_duplicate, duplicate_id = strict_engine.add_place(
            self.test_places[6]
        )  # place_7 (typo)
        self.assertFalse(is_duplicate)  # Should not be considered duplicate

        # Check stats
        stats = strict_engine.get_dedup_statistics()
        self.assertEqual(stats["total_processed"], 2)
        self.assertEqual(stats["duplicates_found"], 0)

    def test_geo_tolerance_adjustment(self):
        """Test geographic tolerance adjustment."""
        # Create engine with very strict geo tolerance
        strict_geo_engine = create_dedup_engine(
            fuzzy_threshold=0.86, geo_tolerance=0.0001
        )

        # Add place
        is_duplicate, duplicate_id = strict_geo_engine.add_place(
            self.test_places[0]
        )  # place_1
        self.assertFalse(is_duplicate)

        # Add place with slightly different coordinates (should not be duplicate with strict tolerance)
        is_duplicate, duplicate_id = strict_geo_engine.add_place(
            self.test_places[8]
        )  # place_9 (same geo)
        self.assertFalse(
            is_duplicate
        )  # Should not be considered duplicate due to strict geo tolerance

        # Check stats
        stats = strict_geo_engine.get_dedup_statistics()
        self.assertEqual(stats["total_processed"], 2)
        self.assertEqual(stats["duplicates_found"], 0)

    def test_empty_and_none_values(self):
        """Test handling of empty and None values."""
        # Test with minimal data
        minimal_place = {
            "id": "minimal",
            "name": "",
            "city": "",
            "domain": "",
            "geo_lat": None,
            "geo_lng": None,
            "address": None,
            "url": None,
        }

        is_duplicate, duplicate_id = self.engine.add_place(minimal_place)
        self.assertFalse(is_duplicate)

        # Should handle gracefully
        stats = self.engine.get_dedup_statistics()
        self.assertEqual(stats["total_processed"], 1)

    def test_engine_clear_functionality(self):
        """Test engine clear functionality."""
        # Add some places
        self.engine.add_place(self.test_places[0])
        self.engine.add_place(self.test_places[1])

        # Check data exists
        self.assertGreater(len(self.engine.processed_places), 0)

        # Clear engine
        self.engine.clear()

        # Check data is cleared
        self.assertEqual(len(self.engine.processed_places), 0)
        self.assertEqual(len(self.engine.identity_groups), 0)
        self.assertEqual(len(self.engine.fuzzy_groups), 0)
        self.assertEqual(len(self.engine.address_groups), 0)

        # Check stats are reset
        stats = self.engine.get_dedup_statistics()
        self.assertEqual(stats["total_processed"], 0)
        self.assertEqual(stats["duplicates_found"], 0)

    def test_export_functionality(self):
        """Test duplicate export functionality."""
        # Add some places to create duplicates
        for place_data in self.test_places[:5]:
            self.engine.add_place(place_data)

        # Export duplicates
        export_file = "test_duplicates_report.txt"
        self.engine.export_duplicates(export_file)

        # Check file was created
        import os

        self.assertTrue(os.path.exists(export_file))

        # Check file content
        with open(export_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Duplicate Groups Report", content)
            self.assertIn("Statistics:", content)

        # Clean up
        os.remove(export_file)

    def test_performance_with_large_dataset(self):
        """Test performance with larger dataset."""
        # Create larger dataset
        large_dataset = []
        for i in range(100):
            place_data = {
                "id": f"large_place_{i}",
                "name": f"Restaurant {i}",
                "city": "Bangkok",
                "domain": "test.com",
                "geo_lat": 13.7563 + (i * 0.001),
                "geo_lng": 100.5018 + (i * 0.001),
                "address": f"Address {i}, Bangkok",
                "url": f"https://test.com/place/{i}",
            }
            large_dataset.append(place_data)

        # Measure performance
        import time

        start_time = time.time()

        for place_data in large_dataset:
            self.engine.add_place(place_data)

        end_time = time.time()
        processing_time = end_time - start_time

        # Should process 100 places in reasonable time (less than 1 second)
        self.assertLess(processing_time, 1.0)

        # Check results
        stats = self.engine.get_dedup_statistics()
        self.assertEqual(stats["total_processed"], 100)
        self.assertGreaterEqual(stats["duplicates_found"], 0)

    def test_edge_cases(self):
        """Test various edge cases."""
        # Test with very long names
        long_name_place = {
            "id": "long_name",
            "name": "A" * 1000,  # Very long name
            "city": "Bangkok",
            "domain": "test.com",
            "geo_lat": None,
            geo_lng: None,
            "address": None,
            "url": None,
        }

        is_duplicate, duplicate_id = self.engine.add_place(long_name_place)
        self.assertFalse(is_duplicate)

        # Test with special characters
        special_char_place = {
            "id": "special_chars",
            "name": "Restaurant @#$%^&*()",
            "city": "Bangkok",
            "domain": "test.com",
            "geo_lat": None,
            geo_lng: None,
            "address": "Address @#$%^&*()",
            "url": None,
        }

        is_duplicate, duplicate_id = self.engine.add_place(special_char_place)
        self.assertFalse(is_duplicate)

        # Should handle gracefully
        stats = self.engine.get_dedup_statistics()
        self.assertEqual(stats["total_processed"], 2)


if __name__ == "__main__":
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestDedupEngine)

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
