#!/usr/bin/env python3
"""
Unit tests for Tag Grammar Engine.
"""

import sys
import unittest
from pathlib import Path

# Добавляем src в Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tags import create_tag_grammar_engine


class TestTagGrammarEngine(unittest.TestCase):
    """Test cases for Tag Grammar Engine."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = create_tag_grammar_engine()

        # Test tag sets
        self.test_tags = [
            # Valid A-level tags
            "food_dining",
            "nightlife",
            "shopping",
            "culture_arts",
            "wellness_health",
            # Valid B-level tags
            "outdoor_recreation",
            "business_services",
            "education_training",
            "accommodation",
            "transportation",
            # EN synonyms
            "restaurant",
            "cafe",
            "bar",
            "club",
            "mall",
            "market",
            "museum",
            "gallery",
            "spa",
            "massage",
            "park",
            "garden",
            "hotel",
            "resort",
            "bts",
            "mrt",
            # TH synonyms
            "ร้านอาหาร",
            "คาเฟ่",
            "บาร์",
            "คลับ",
            "ห้างสรรพสินค้า",
            "ตลาด",
            "พิพิธภัณฑ์",
            "แกลเลอรี่",
            "สปา",
            "นวด",
            "สวนสาธารณะ",
            "สวน",
            "โรงแรม",
            "รีสอร์ท",
            "รถไฟฟ้าบีทีเอส",
            "รถไฟฟ้ามหานคร",
        ]

        # Test phrases for validation
        self.test_phrases = [
            # Valid combinations
            ["food_dining", "nightlife"],
            ["culture_arts", "shopping"],
            ["wellness_health", "outdoor_recreation"],
            ["business_services", "transportation"],
            # Mixed level tags
            ["food_dining", "outdoor_recreation", "accommodation"],
            ["nightlife", "business_services", "education_training"],
            # Synonym-based tags
            ["restaurant", "bar", "park"],
            ["cafe", "museum", "hotel"],
            ["spa", "garden", "bts"],
            # TH synonym-based tags
            ["ร้านอาหาร", "คลับ", "สวนสาธารณะ"],
            ["คาเฟ่", "พิพิธภัณฑ์", "โรงแรม"],
            # Edge cases
            ["food_dining"],  # Single tag
            ["food_dining", "food_dining"],  # Duplicate
            ["unknown_tag"],  # Unknown tag
            ["food_dining", "unknown_tag", "nightlife"],  # Mixed valid/invalid
        ]

    def test_grammar_loading(self):
        """Test that grammar loads correctly."""
        self.assertTrue(self.engine.load_grammar())
        self.assertGreater(len(self.engine.categories), 0)
        self.assertGreater(len(self.engine.rules), 0)
        self.assertGreater(len(self.engine.combinations), 0)

    def test_category_structure(self):
        """Test category structure and data."""
        for category_name, category_data in self.engine.categories.items():
            # Check required fields
            self.assertIn("level", category_data)
            self.assertIn("description", category_data)
            self.assertIn("priority", category_data)
            self.assertIn("en_synonyms", category_data)
            self.assertIn("th_synonyms", category_data)

            # Check level values
            self.assertIn(category_data["level"], ["A", "B"])

            # Check priority is positive
            self.assertGreater(category_data["priority"], 0)

            # Check synonyms are lists
            self.assertIsInstance(category_data["en_synonyms"], list)
            self.assertIsInstance(category_data["th_synonyms"], list)

    def test_level_distribution(self):
        """Test A/B level distribution."""
        level_a_count = len(self.engine.level_a_tags)
        level_b_count = len(self.engine.level_b_tags)
        total_categories = len(self.engine.categories)

        self.assertEqual(level_a_count + level_b_count, total_categories)
        self.assertGreater(level_a_count, 0)
        self.assertGreater(level_b_count, 0)

        # A-level tags should have higher priority (lower numbers)
        for a_tag, a_data in self.engine.level_a_tags.items():
            for b_tag, b_data in self.engine.level_b_tags.items():
                self.assertLess(a_data["priority"], b_data["priority"])

    def test_priority_ordering(self):
        """Test priority ordering within levels."""
        # A-level priorities should be 1-5
        a_priorities = [data["priority"] for data in self.engine.level_a_tags.values()]
        self.assertEqual(min(a_priorities), 1)
        self.assertEqual(max(a_priorities), 5)

        # B-level priorities should be 6-10
        b_priorities = [data["priority"] for data in self.engine.level_b_tags.values()]
        self.assertEqual(min(b_priorities), 6)
        self.assertEqual(max(b_priorities), 10)

    def test_synonym_mapping(self):
        """Test synonym to category mapping."""
        # Test EN synonyms
        self.assertEqual(self.engine.find_tag_by_synonym("restaurant"), "food_dining")
        self.assertEqual(self.engine.find_tag_by_synonym("cafe"), "food_dining")
        self.assertEqual(self.engine.find_tag_by_synonym("bar"), "food_dining")
        self.assertEqual(self.engine.find_tag_by_synonym("club"), "nightlife")
        self.assertEqual(self.engine.find_tag_by_synonym("mall"), "shopping")
        self.assertEqual(self.engine.find_tag_by_synonym("museum"), "culture_arts")
        self.assertEqual(self.engine.find_tag_by_synonym("spa"), "wellness_health")
        self.assertEqual(self.engine.find_tag_by_synonym("park"), "outdoor_recreation")
        self.assertEqual(self.engine.find_tag_by_synonym("hotel"), "accommodation")
        self.assertEqual(self.engine.find_tag_by_synonym("bts"), "transportation")

        # Test TH synonyms
        self.assertEqual(self.engine.find_tag_by_synonym("ร้านอาหาร"), "food_dining")
        self.assertEqual(self.engine.find_tag_by_synonym("คาเฟ่"), "food_dining")
        self.assertEqual(self.engine.find_tag_by_synonym("คลับ"), "nightlife")
        self.assertEqual(self.engine.find_tag_by_synonym("ห้างสรรพสินค้า"), "shopping")
        self.assertEqual(self.engine.find_tag_by_synonym("พิพิธภัณฑ์"), "culture_arts")
        self.assertEqual(self.engine.find_tag_by_synonym("สปา"), "wellness_health")
        self.assertEqual(
            self.engine.find_tag_by_synonym("สวนสาธารณะ"), "outdoor_recreation"
        )
        self.assertEqual(self.engine.find_tag_by_synonym("โรงแรม"), "accommodation")
        self.assertEqual(
            self.engine.find_tag_by_synonym("รถไฟฟ้าบีทีเอส"), "transportation"
        )

    def test_tag_info_retrieval(self):
        """Test tag information retrieval."""
        # Test direct category access
        food_info = self.engine.get_tag_info("food_dining")
        self.assertIsNotNone(food_info)
        self.assertEqual(food_info["level"], "A")
        self.assertEqual(food_info["priority"], 1)

        # Test synonym access
        restaurant_info = self.engine.get_tag_info("restaurant")
        self.assertIsNotNone(restaurant_info)
        self.assertEqual(restaurant_info["level"], "A")

        # Test TH synonym access
        th_food_info = self.engine.get_tag_info("ร้านอาหาร")
        self.assertIsNotNone(th_food_info)
        self.assertEqual(th_food_info["level"], "A")

        # Test unknown tag
        unknown_info = self.engine.get_tag_info("unknown_tag")
        self.assertIsNone(unknown_info)

    def test_tag_level_detection(self):
        """Test tag level detection."""
        # A-level tags
        self.assertTrue(self.engine.is_level_a_tag("food_dining"))
        self.assertTrue(self.engine.is_level_a_tag("nightlife"))
        self.assertTrue(self.engine.is_level_a_tag("shopping"))
        self.assertTrue(self.engine.is_level_a_tag("culture_arts"))
        self.assertTrue(self.engine.is_level_a_tag("wellness_health"))

        # B-level tags
        self.assertTrue(self.engine.is_level_b_tag("outdoor_recreation"))
        self.assertTrue(self.engine.is_level_b_tag("business_services"))
        self.assertTrue(self.engine.is_level_b_tag("education_training"))
        self.assertTrue(self.engine.is_level_b_tag("accommodation"))
        self.assertTrue(self.engine.is_level_b_tag("transportation"))

        # Synonyms should also work
        self.assertTrue(self.engine.is_level_a_tag("restaurant"))
        self.assertTrue(self.engine.is_level_a_tag("ร้านอาหาร"))
        self.assertTrue(self.engine.is_level_b_tag("park"))
        self.assertTrue(self.engine.is_level_b_tag("สวนสาธารณะ"))

    def test_tag_priority_retrieval(self):
        """Test tag priority retrieval."""
        # A-level priorities
        self.assertEqual(self.engine.get_tag_priority("food_dining"), 1)
        self.assertEqual(self.engine.get_tag_priority("nightlife"), 2)
        self.assertEqual(self.engine.get_tag_priority("shopping"), 3)
        self.assertEqual(self.engine.get_tag_priority("culture_arts"), 4)
        self.assertEqual(self.engine.get_tag_priority("wellness_health"), 5)

        # B-level priorities
        self.assertEqual(self.engine.get_tag_priority("outdoor_recreation"), 6)
        self.assertEqual(self.engine.get_tag_priority("business_services"), 7)
        self.assertEqual(self.engine.get_tag_priority("education_training"), 8)
        self.assertEqual(self.engine.get_tag_priority("accommodation"), 9)
        self.assertEqual(self.engine.get_tag_priority("transportation"), 10)

        # Synonyms should work
        self.assertEqual(self.engine.get_tag_priority("restaurant"), 1)
        self.assertEqual(self.engine.get_tag_priority("ร้านอาหาร"), 1)

    def test_synonym_retrieval(self):
        """Test synonym retrieval by language."""
        # EN synonyms
        en_synonyms = self.engine.get_tag_synonyms("food_dining", "en")
        self.assertIn("restaurant", en_synonyms)
        self.assertIn("cafe", en_synonyms)
        self.assertIn("bar", en_synonyms)

        # TH synonyms
        th_synonyms = self.engine.get_tag_synonyms("food_dining", "th")
        self.assertIn("ร้านอาหาร", th_synonyms)
        self.assertIn("คาเฟ่", th_synonyms)
        self.assertIn("บาร์", th_synonyms)

        # Default language should be EN
        default_synonyms = self.engine.get_tag_synonyms("food_dining")
        self.assertEqual(default_synonyms, en_synonyms)

    def test_tag_normalization(self):
        """Test tag normalization."""
        # Test synonym normalization
        normalized = self.engine.normalize_tags(["restaurant", "cafe", "bar"])
        self.assertEqual(normalized, ["food_dining"])

        # Test mixed language normalization
        normalized = self.engine.normalize_tags(["restaurant", "ร้านอาหาร", "cafe"])
        self.assertEqual(normalized, ["food_dining"])

        # Test unknown tags are preserved
        normalized = self.engine.normalize_tags(["restaurant", "unknown_tag", "cafe"])
        self.assertEqual(normalized, ["food_dining", "unknown_tag"])

        # Test duplicate removal
        normalized = self.engine.normalize_tags(["restaurant", "restaurant", "cafe"])
        self.assertEqual(normalized, ["food_dining"])

    def test_tag_validation(self):
        """Test tag validation."""
        # Valid tag set
        validation = self.engine.validate_tags(["food_dining", "nightlife"])
        self.assertTrue(validation["is_valid"])
        self.assertEqual(validation["stats"]["level_a_count"], 2)
        self.assertEqual(validation["stats"]["level_b_count"], 0)
        self.assertEqual(validation["stats"]["unknown_tags"], 0)

        # Too many tags
        many_tags = ["food_dining"] * 10
        validation = self.engine.validate_tags(many_tags)
        self.assertFalse(validation["is_valid"])
        self.assertIn("Too many tags", validation["errors"][0])

        # No tags
        validation = self.engine.validate_tags([])
        self.assertIn("Too few tags", validation["warnings"][0])

        # No level A tags
        validation = self.engine.validate_tags(
            ["outdoor_recreation", "business_services"]
        )
        self.assertFalse(validation["is_valid"])
        self.assertIn("Not enough level A tags", validation["errors"][0])

        # Unknown tags
        validation = self.engine.validate_tags(["food_dining", "unknown_tag"])
        self.assertIn("Unknown tags", validation["warnings"][0])
        self.assertGreater(len(validation["suggestions"]), 0)

    def test_tag_combinations(self):
        """Test tag combination scoring."""
        # Good combination
        validation = self.engine.validate_tags(["food_dining", "nightlife"])
        self.assertTrue(
            any(
                "Good tag combination" in suggestion
                for suggestion in validation["suggestions"]
            )
        )

        # Another good combination
        validation = self.engine.validate_tags(["culture_arts", "shopping"])
        self.assertTrue(
            any(
                "Good tag combination" in suggestion
                for suggestion in validation["suggestions"]
            )
        )

        # Regular combination
        validation = self.engine.validate_tags(["food_dining", "outdoor_recreation"])
        # Should not have combination suggestion
        combination_suggestions = [
            s for s in validation["suggestions"] if "Good tag combination" in s
        ]
        self.assertEqual(len(combination_suggestions), 0)

    def test_tag_search(self):
        """Test tag search functionality."""
        # Search by English query
        results = self.engine.search_tags("restaurant", "en")
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["tag"], "food_dining")
        self.assertGreater(results[0]["score"], 0)

        # Search by Thai query
        results = self.engine.search_tags("ร้านอาหาร", "th")
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["tag"], "food_dining")

        # Search by partial query
        results = self.engine.search_tags("food", "en")
        self.assertGreater(len(results), 0)

        # Search with no results
        results = self.engine.search_tags("xyz123", "en")
        self.assertEqual(len(results), 0)

    def test_related_tags(self):
        """Test related tag retrieval."""
        # Get related tags for food_dining
        related = self.engine.get_related_tags("food_dining")
        self.assertGreater(len(related), 0)

        # Related tags should be same level (A)
        for related_tag in related:
            self.assertTrue(self.engine.is_level_a_tag(related_tag))

        # Priority should be close
        food_priority = self.engine.get_tag_priority("food_dining")
        for related_tag in related:
            related_priority = self.engine.get_tag_priority(related_tag)
            self.assertLessEqual(abs(related_priority - food_priority), 2)

    def test_tag_statistics(self):
        """Test tag statistics generation."""
        stats = self.engine.get_tag_statistics()

        # Check required fields
        self.assertIn("total_categories", stats)
        self.assertIn("level_a_count", stats)
        self.assertIn("level_b_count", stats)
        self.assertIn("total_synonyms", stats)
        self.assertIn("average_synonyms_per_category", stats)
        self.assertIn("priority_distribution", stats)
        self.assertIn("language_distribution", stats)

        # Check values
        self.assertEqual(stats["total_categories"], len(self.engine.categories))
        self.assertEqual(stats["level_a_count"], len(self.engine.level_a_tags))
        self.assertEqual(stats["level_b_count"], len(self.engine.level_b_tags))

        # Check language distribution
        self.assertGreater(stats["language_distribution"]["en_synonyms"], 0)
        self.assertGreater(stats["language_distribution"]["th_synonyms"], 0)

        # Check priority distribution
        self.assertGreater(len(stats["priority_distribution"]), 0)

    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Empty tag list
        normalized = self.engine.normalize_tags([])
        self.assertEqual(normalized, [])

        # None tags
        normalized = self.engine.normalize_tags([None, "food_dining", None])
        self.assertEqual(normalized, ["food_dining"])

        # Empty string tags
        normalized = self.engine.normalize_tags(["", "food_dining", ""])
        self.assertEqual(normalized, ["food_dining"])

        # Case insensitive matching
        normalized = self.engine.normalize_tags(["RESTAURANT", "CAFE"])
        self.assertEqual(normalized, ["food_dining"])

        # Mixed case
        normalized = self.engine.normalize_tags(["Restaurant", "Cafe"])
        self.assertEqual(normalized, ["food_dining"])

    def test_performance(self):
        """Test performance with large tag sets."""
        # Large tag set
        large_tag_set = [
            "food_dining",
            "nightlife",
            "shopping",
            "culture_arts",
            "wellness_health",
        ] * 100

        # Should handle large sets efficiently
        start_time = self.engine._get_timestamp()
        normalized = self.engine.normalize_tags(large_tag_set)
        end_time = self.engine._get_timestamp()

        # Should complete in reasonable time (less than 1 second)
        self.assertLess(end_time - start_time, 1.0)

        # Should normalize correctly
        self.assertEqual(len(normalized), 5)  # 5 unique categories

    def test_grammar_reload(self):
        """Test grammar reloading."""
        # Store original data
        original_categories = len(self.engine.categories)

        # Reload grammar
        success = self.engine.reload_grammar()
        self.assertTrue(success)

        # Data should be the same
        self.assertEqual(len(self.engine.categories), original_categories)

    def test_invalid_grammar_file(self):
        """Test handling of invalid grammar file."""
        # Create engine with non-existent file
        invalid_engine = create_tag_grammar_engine("non_existent_file.yaml")

        # Should handle gracefully
        self.assertEqual(len(invalid_engine.categories), 0)
        self.assertEqual(len(invalid_engine.rules), 0)

    def test_synonym_edge_cases(self):
        """Test synonym handling edge cases."""
        # Test synonyms with special characters
        test_synonyms = ["restaurant-123", "cafe_456", "bar.789"]
        for synonym in test_synonyms:
            # Should not crash
            result = self.engine.find_tag_by_synonym(synonym)
            # Result might be None for non-existent synonyms

        # Test very long synonyms
        long_synonym = "a" * 1000
        result = self.engine.find_tag_by_synonym(long_synonym)
        # Should not crash

    def test_validation_edge_cases(self):
        """Test validation edge cases."""
        # Very long tag names
        long_tag = "a" * 1000
        validation = self.engine.validate_tags([long_tag])
        # Should not crash

        # Special characters in tags
        special_tags = ["tag@123", "tag#456", "tag$789"]
        validation = self.engine.validate_tags(special_tags)
        # Should not crash

    def test_combination_edge_cases(self):
        """Test combination scoring edge cases."""
        # Empty combination list
        score = self.engine._calculate_combination_score([])
        self.assertEqual(score, 1.0)

        # Single tag
        score = self.engine._calculate_combination_score(["food_dining"])
        self.assertEqual(score, 1.0)

        # Unknown tags
        score = self.engine._calculate_combination_score(["unknown1", "unknown2"])
        self.assertEqual(score, 1.0)

    def test_similarity_calculation(self):
        """Test string similarity calculation."""
        # Identical strings
        similarity = self.engine._calculate_similarity("restaurant", "restaurant")
        self.assertEqual(similarity, 1.0)

        # Similar strings
        similarity = self.engine._calculate_similarity("restaurant", "restaurants")
        self.assertGreater(similarity, 0.5)

        # Different strings
        similarity = self.engine._calculate_similarity("restaurant", "hotel")
        self.assertEqual(similarity, 0.0)

        # Empty strings
        similarity = self.engine._calculate_similarity("", "restaurant")
        self.assertEqual(similarity, 0.0)

        similarity = self.engine._calculate_similarity("restaurant", "")
        self.assertEqual(similarity, 0.0)

    def test_canonical_tag_finding(self):
        """Test canonical tag finding."""
        # Direct match
        canonical = self.engine._find_canonical_tag("food_dining")
        self.assertEqual(canonical, "food_dining")

        # Synonym match
        canonical = self.engine._find_canonical_tag("restaurant")
        self.assertEqual(canonical, "food_dining")

        # TH synonym match
        canonical = self.engine._find_canonical_tag("ร้านอาหาร")
        self.assertEqual(canonical, "food_dining")

        # No match
        canonical = self.engine._find_canonical_tag("unknown_tag")
        self.assertIsNone(canonical)

    def test_lookup_table_integrity(self):
        """Test lookup table integrity."""
        # All categories should be in tag_to_category
        for category_name in self.engine.categories:
            self.assertIn(category_name, self.engine.tag_to_category)

        # All synonyms should map to valid categories
        for synonym, category in self.engine.synonym_to_category.items():
            self.assertIn(category, self.engine.categories)

        # Level lookups should be consistent
        for category_name, category_data in self.engine.categories.items():
            level = category_data.get("level")
            if level == "A":
                self.assertIn(category_name, self.engine.level_a_tags)
            elif level == "B":
                self.assertIn(category_name, self.engine.level_b_tags)

    def test_priority_consistency(self):
        """Test priority consistency across levels."""
        # A-level priorities should be 1-5
        a_priorities = set()
        for category_data in self.engine.level_a_tags.values():
            priority = category_data.get("priority")
            a_priorities.add(priority)
            self.assertLessEqual(priority, 5)
            self.assertGreaterEqual(priority, 1)

        # B-level priorities should be 6-10
        b_priorities = set()
        for category_data in self.engine.level_b_tags.values():
            priority = category_data.get("priority")
            b_priorities.add(priority)
            self.assertLessEqual(priority, 10)
            self.assertGreaterEqual(priority, 6)

        # No overlap between A and B priorities
        self.assertEqual(len(a_priorities.intersection(b_priorities)), 0)

    def test_synonym_uniqueness(self):
        """Test synonym uniqueness across categories."""
        all_en_synonyms = []
        all_th_synonyms = []

        for category_data in self.engine.categories.values():
            all_en_synonyms.extend(category_data.get("en_synonyms", []))
            all_th_synonyms.extend(category_data.get("th_synonyms", []))

        # Check for duplicates (case insensitive)
        en_lower = [s.lower() for s in all_en_synonyms]
        th_lower = [s.lower() for s in all_th_synonyms]

        self.assertEqual(
            len(en_lower), len(set(en_lower)), "Duplicate EN synonyms found"
        )
        self.assertEqual(
            len(th_lower), len(set(th_lower)), "Duplicate TH synonyms found"
        )

    def test_grammar_version(self):
        """Test grammar version and metadata."""
        self.assertIn("version", self.engine.grammar_data)
        self.assertIn("description", self.engine.grammar_data)

        version = self.engine.grammar_data["version"]
        self.assertEqual(version, "1.0")

        description = self.engine.grammar_data["description"]
        self.assertIn("Tag grammar", description)
        self.assertIn("Bangkok places", description)


if __name__ == "__main__":
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestTagGrammarEngine)

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
