#!/usr/bin/env python3
"""
Tag Grammar Engine for Bangkok Places Parser.
"""

import logging
import yaml
from typing import Dict, Any, List, Optional, Union, Tuple, Set
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class TagGrammarEngine:
    """Engine for processing tag grammar with A/B levels and EN/TH synonyms."""
    
    def __init__(self, grammar_file: Optional[str] = None):
        """Initialize tag grammar engine."""
        self.grammar_file = grammar_file or "config/tags/tag_grammar.yaml"
        self.grammar_data = {}
        self.categories = {}
        self.rules = []
        self.combinations = []
        self.validation = {}
        
        # Load grammar
        self.load_grammar()
        
        # Build lookup tables
        self._build_lookup_tables()
    
    def load_grammar(self) -> bool:
        """Load tag grammar from YAML file."""
        try:
            grammar_path = Path(self.grammar_file)
            if not grammar_path.exists():
                logger.error(f"Grammar file not found: {self.grammar_file}")
                return False
            
            with open(grammar_path, 'r', encoding='utf-8') as file:
                self.grammar_data = yaml.safe_load(file)
            
            # Extract components
            self.categories = self.grammar_data.get('categories', {})
            self.rules = self.grammar_data.get('rules', [])
            self.combinations = self.grammar_data.get('combinations', [])
            self.validation = self.grammar_data.get('validation', {})
            
            logger.info(f"Loaded tag grammar: {len(self.categories)} categories, {len(self.rules)} rules")
            return True
            
        except Exception as e:
            logger.error(f"Error loading grammar: {e}")
            return False
    
    def _build_lookup_tables(self):
        """Build efficient lookup tables for fast tag processing."""
        # Synonym to category mapping
        self.synonym_to_category = {}
        self.tag_to_category = {}
        
        for category_name, category_data in self.categories.items():
            # Map category name to category data
            self.tag_to_category[category_name] = category_data
            
            # Map EN synonyms to category
            for synonym in category_data.get('en_synonyms', []):
                self.synonym_to_category[synonym.lower()] = category_name
            
            # Map TH synonyms to category
            for synonym in category_data.get('th_synonyms', []):
                self.synonym_to_category[synonym.lower()] = category_name
        
        # Level-based lookups
        self.level_a_tags = {name: data for name, data in self.categories.items() if data.get('level') == 'A'}
        self.level_b_tags = {name: data for name, data in self.categories.items() if data.get('level') == 'B'}
        
        # Priority-based lookups
        self.priority_sorted_tags = sorted(
            self.categories.items(),
            key=lambda x: x[1].get('priority', 999)
        )
    
    def get_tag_info(self, tag: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tag."""
        # Try direct category match
        if tag in self.categories:
            return self.categories[tag]
        
        # Try synonym match
        tag_lower = tag.lower()
        if tag_lower in self.synonym_to_category:
            category_name = self.synonym_to_category[tag_lower]
            return self.categories[category_name]
        
        return None
    
    def get_tag_level(self, tag: str) -> Optional[str]:
        """Get the level (A or B) of a tag."""
        tag_info = self.get_tag_info(tag)
        return tag_info.get('level') if tag_info else None
    
    def get_tag_priority(self, tag: str) -> Optional[int]:
        """Get the priority of a tag."""
        tag_info = self.get_tag_info(tag)
        return tag_info.get('priority') if tag_info else None
    
    def is_level_a_tag(self, tag: str) -> bool:
        """Check if a tag is level A."""
        return self.get_tag_level(tag) == 'A'
    
    def is_level_b_tag(self, tag: str) -> bool:
        """Check if a tag is level B."""
        return self.get_tag_level(tag) == 'B'
    
    def get_tag_synonyms(self, tag: str, language: str = 'en') -> List[str]:
        """Get synonyms for a tag in specified language."""
        tag_info = self.get_tag_info(tag)
        if not tag_info:
            return []
        
        if language.lower() == 'th':
            return tag_info.get('th_synonyms', [])
        else:
            return tag_info.get('en_synonyms', [])
    
    def find_tag_by_synonym(self, synonym: str) -> Optional[str]:
        """Find tag category by synonym."""
        synonym_lower = synonym.lower()
        return self.synonym_to_category.get(synonym_lower)
    
    def normalize_tags(self, tags: List[str]) -> List[str]:
        """Normalize a list of tags using grammar rules."""
        normalized = []
        
        for tag in tags:
            if not tag:
                continue
            
            # Try to find the canonical tag
            canonical_tag = self._find_canonical_tag(tag)
            if canonical_tag:
                normalized.append(canonical_tag)
            else:
                # Keep original if no match found
                normalized.append(tag)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in normalized:
            if tag.lower() not in seen:
                seen.add(tag.lower())
                unique_tags.append(tag)
        
        return unique_tags
    
    def _find_canonical_tag(self, tag: str) -> Optional[str]:
        """Find the canonical tag for a given input."""
        # Direct match
        if tag in self.categories:
            return tag
        
        # Synonym match
        tag_lower = tag.lower()
        if tag_lower in self.synonym_to_category:
            return self.synonym_to_category[tag_lower]
        
        # Partial match (for cases like "restaurant" matching "food_dining")
        for category_name, category_data in self.categories.items():
            en_synonyms = category_data.get('en_synonyms', [])
            th_synonyms = category_data.get('th_synonyms', [])
            
            if tag_lower in [s.lower() for s in en_synonyms + th_synonyms]:
                return category_name
        
        return None
    
    def validate_tags(self, tags: List[str]) -> Dict[str, Any]:
        """Validate tags according to grammar rules."""
        validation = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': [],
            'stats': {
                'total_tags': len(tags),
                'level_a_count': 0,
                'level_b_count': 0,
                'unknown_tags': 0
            }
        }
        
        # Check tag count limits
        max_tags = self.validation.get('max_tags_per_place', 8)
        min_tags = self.validation.get('min_tags_per_place', 1)
        required_level_a = self.validation.get('required_level_a_tags', 1)
        
        if len(tags) > max_tags:
            validation['errors'].append(f"Too many tags: {len(tags)} > {max_tags}")
            validation['is_valid'] = False
        
        if len(tags) < min_tags:
            validation['warnings'].append(f"Too few tags: {len(tags)} < {min_tags}")
        
        # Analyze each tag
        level_a_tags = []
        level_b_tags = []
        unknown_tags = []
        
        for tag in tags:
            tag_info = self.get_tag_info(tag)
            if tag_info:
                level = tag_info.get('level')
                if level == 'A':
                    level_a_tags.append(tag)
                    validation['stats']['level_a_count'] += 1
                elif level == 'B':
                    level_b_tags.append(tag)
                    validation['stats']['level_b_count'] += 1
            else:
                unknown_tags.append(tag)
                validation['stats']['unknown_tags'] += 1
        
        # Check level A requirements
        if len(level_a_tags) < required_level_a:
            validation['errors'].append(f"Not enough level A tags: {len(level_a_tags)} < {required_level_a}")
            validation['is_valid'] = False
        
        # Check for unknown tags
        if unknown_tags:
            validation['warnings'].append(f"Unknown tags: {unknown_tags}")
            
            # Suggest alternatives for unknown tags
            for unknown_tag in unknown_tags:
                suggestions = self._suggest_tags(unknown_tag)
                if suggestions:
                    validation['suggestions'].append(f"'{unknown_tag}' → {suggestions}")
        
        # Check tag combinations
        combination_score = self._calculate_combination_score(tags)
        if combination_score > 1.0:
            validation['suggestions'].append(f"Good tag combination! Score: {combination_score:.2f}")
        
        return validation
    
    def _suggest_tags(self, unknown_tag: str) -> List[str]:
        """Suggest alternative tags for unknown tag."""
        suggestions = []
        unknown_lower = unknown_tag.lower()
        
        # Find similar tags by string similarity
        for category_name, category_data in self.categories.items():
            # Check EN synonyms
            for synonym in category_data.get('en_synonyms', []):
                if self._calculate_similarity(unknown_lower, synonym.lower()) > 0.6:
                    suggestions.append(category_name)
                    break
            
            # Check TH synonyms
            for synonym in category_data.get('th_synonyms', []):
                if self._calculate_similarity(unknown_lower, synonym.lower()) > 0.6:
                    suggestions.append(category_name)
                    break
        
        return list(set(suggestions))[:3]  # Return top 3 suggestions
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using simple algorithm."""
        if not str1 or not str2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _calculate_combination_score(self, tags: List[str]) -> float:
        """Calculate combination score for tags."""
        score = 1.0
        
        for combination in self.combinations:
            combination_tags = combination.get('tags', [])
            weight = combination.get('weight', 1.0)
            
            # Check if this combination is present
            if all(tag in tags for tag in combination_tags):
                score *= weight
        
        return score
    
    def get_related_tags(self, tag: str, max_related: int = 5) -> List[str]:
        """Get related tags for a given tag."""
        tag_info = self.get_tag_info(tag)
        if not tag_info:
            return []
        
        # Find tags with similar priority and level
        level = tag_info.get('level')
        priority = tag_info.get('priority', 999)
        
        related = []
        for category_name, category_data in self.categories.items():
            if category_name == tag:
                continue
            
            if category_data.get('level') == level:
                # Same level, check priority proximity
                cat_priority = category_data.get('priority', 999)
                if abs(cat_priority - priority) <= 2:
                    related.append(category_name)
        
        # Sort by priority and return top results
        related.sort(key=lambda x: self.categories[x].get('priority', 999))
        return related[:max_related]
    
    def get_tag_statistics(self) -> Dict[str, Any]:
        """Get comprehensive tag statistics."""
        stats = {
            'total_categories': len(self.categories),
            'level_a_count': len(self.level_a_tags),
            'level_b_count': len(self.level_b_tags),
            'total_synonyms': sum(len(cat.get('en_synonyms', [])) + len(cat.get('th_synonyms', [])) for cat in self.categories.values()),
            'average_synonyms_per_category': 0,
            'priority_distribution': {},
            'language_distribution': {
                'en_synonyms': sum(len(cat.get('en_synonyms', [])) for cat in self.categories.values()),
                'th_synonyms': sum(len(cat.get('th_synonyms', [])) for cat in self.categories.values())
            }
        }
        
        # Calculate average synonyms
        if stats['total_categories'] > 0:
            stats['average_synonyms_per_category'] = round(stats['total_synonyms'] / stats['total_categories'], 2)
        
        # Priority distribution
        for category_name, category_data in self.categories.items():
            priority = category_data.get('priority', 0)
            if priority not in stats['priority_distribution']:
                stats['priority_distribution'][priority] = 0
            stats['priority_distribution'][priority] += 1
        
        return stats
    
    def search_tags(self, query: str, language: str = 'en', max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for tags by query."""
        results = []
        query_lower = query.lower()
        
        for category_name, category_data in self.categories.items():
            score = 0.0
            
            # Check category name
            if query_lower in category_name.lower():
                score += 2.0
            
            # Check description
            description = category_data.get('description', '')
            if query_lower in description.lower():
                score += 1.0
            
            # Check synonyms
            synonyms = category_data.get(f'{language.lower()}_synonyms', [])
            for synonym in synonyms:
                if query_lower in synonym.lower():
                    score += 1.5
                    break
            
            if score > 0:
                results.append({
                    'tag': category_name,
                    'score': score,
                    'level': category_data.get('level'),
                    'priority': category_data.get('priority'),
                    'description': description
                })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:max_results]
    
    def reload_grammar(self) -> bool:
        """Reload grammar from file."""
        logger.info("Reloading tag grammar...")
        return self.load_grammar()


# Фабрика для создания движка грамматики тегов
def create_tag_grammar_engine(grammar_file: Optional[str] = None) -> TagGrammarEngine:
    """Create and return a tag grammar engine instance."""
    return TagGrammarEngine(grammar_file)
