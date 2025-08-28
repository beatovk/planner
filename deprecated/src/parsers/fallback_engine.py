#!/usr/bin/env python3
"""
Intelligent fallback engine for data extraction.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup
import json
import re

from .extractors import JSONLDExtractor, OpenGraphExtractor, CSSExtractor

logger = logging.getLogger(__name__)


class FallbackEngine:
    """Intelligent fallback engine with priority-based extraction."""
    
    def __init__(self, recipe: Any):
        """Initialize fallback engine with recipe."""
        self.recipe = recipe
        self.jsonld_extractor = JSONLDExtractor(recipe) if recipe.jsonld_enabled else None
        self.og_extractor = OpenGraphExtractor(recipe) if recipe.og_enabled else None
        self.css_extractor = CSSExtractor(recipe) if recipe.css_enabled else None
        
        # Fallback priority order
        self.fallback_order = self._build_fallback_order()
        
        # Confidence scores for different methods
        self.confidence_scores = {
            'jsonld': 0.95,      # Highest confidence - structured data
            'og': 0.85,          # High confidence - meta tags
            'css': 0.70          # Lower confidence - HTML parsing
        }
    
    def _build_fallback_order(self) -> List[str]:
        """Build fallback order based on recipe priority."""
        priority = self.recipe.extraction_priority
        
        if priority == 'jsonld':
            return ['jsonld', 'og', 'css']
        elif priority == 'og':
            return ['og', 'jsonld', 'css']
        else:  # css priority
            return ['css', 'jsonld', 'og']
    
    def extract_with_fallback(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Extract places with intelligent fallback."""
        all_places = []
        extraction_log = []
        
        # Try each method in priority order
        for method in self.fallback_order:
            if not self._is_method_available(method):
                continue
            
            try:
                places = self._extract_with_method(method, html, url)
                if places:
                    # Add method metadata
                    for place in places:
                        place['extraction_method'] = method
                        place['confidence_score'] = self.confidence_scores.get(method, 0.5)
                    
                    all_places.extend(places)
                    extraction_log.append(f"{method}: {len(places)} places")
                    
                    # If we got good results, we might not need to continue
                    if self._should_stop_fallback(method, places):
                        break
                        
            except Exception as e:
                logger.warning(f"Method {method} failed: {e}")
                extraction_log.append(f"{method}: failed")
        
        # Merge and deduplicate results
        merged_places = self._merge_extraction_results(all_places)
        
        logger.info(f"Fallback extraction complete: {' | '.join(extraction_log)} -> {len(merged_places)} unique places")
        return merged_places
    
    def _is_method_available(self, method: str) -> bool:
        """Check if extraction method is available."""
        if method == 'jsonld':
            return self.jsonld_extractor is not None
        elif method == 'og':
            return self.og_extractor is not None
        elif method == 'css':
            return self.css_extractor is not None
        return False
    
    def _extract_with_method(self, method: str, html: str, url: str) -> List[Dict[str, Any]]:
        """Extract places using specific method."""
        if method == 'jsonld':
            return self.jsonld_extractor.extract(html, url)
        elif method == 'og':
            return self.og_extractor.extract(html, url)
        elif method == 'css':
            return self.css_extractor.extract(html, url)
        return []
    
    def _should_stop_fallback(self, method: str, places: List[Dict[str, Any]]) -> bool:
        """Determine if we should stop fallback extraction."""
        # If we got good results from high-confidence method, stop
        if method == 'jsonld' and len(places) > 0:
            return True
        
        # If we got multiple places from any method, probably sufficient
        if len(places) >= 3:
            return True
        
        return False
    
    def _merge_extraction_results(self, all_places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge and deduplicate extraction results from different methods."""
        if not all_places:
            return []
        
        # Group places by similarity
        place_groups = self._group_similar_places(all_places)
        
        # Merge each group into a single place
        merged_places = []
        for group in place_groups:
            merged_place = self._merge_place_group(group)
            if merged_place:
                merged_places.append(merged_place)
        
        return merged_places
    
    def _group_similar_places(self, places: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group places that likely represent the same entity."""
        groups = []
        processed = set()
        
        for i, place in enumerate(places):
            if i in processed:
                continue
            
            # Start a new group
            group = [place]
            processed.add(i)
            
            # Find similar places
            for j, other_place in enumerate(places[i+1:], i+1):
                if j in processed:
                    continue
                
                if self._are_places_similar(place, other_place):
                    group.append(other_place)
                    processed.add(j)
            
            groups.append(group)
        
        return groups
    
    def _are_places_similar(self, place1: Dict[str, Any], place2: Dict[str, Any]) -> bool:
        """Check if two places likely represent the same entity."""
        # Check name similarity
        name1 = place1.get('name', '').lower()
        name2 = place2.get('name', '').lower()
        
        # Exact name match
        if name1 == name2:
            return True
        
        # High similarity (e.g., "Thai Delight" vs "Thai Delight Restaurant")
        if self._calculate_name_similarity(name1, name2) > 0.8:
            return True
        
        # Check URL similarity
        url1 = place1.get('url', '')
        url2 = place2.get('url', '')
        
        if url1 and url2 and url1 == url2:
            return True
        
        # Check if they're from the same extraction method
        method1 = place1.get('extraction_method', '')
        method2 = place2.get('extraction_method', '')
        
        if method1 == method2:
            # Same method, check for other similarities
            desc1 = place1.get('description', '').lower()
            desc2 = place2.get('description', '').lower()
            
            if desc1 and desc2 and self._calculate_text_similarity(desc1, desc2) > 0.7:
                return True
        
        return False
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names."""
        if not name1 or not name2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text descriptions."""
        if not text1 or not text2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _merge_place_group(self, group: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Merge a group of similar places into one."""
        if not group:
            return None
        
        if len(group) == 1:
            return group[0]
        
        # Sort by confidence score
        group.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        # Start with the highest confidence place
        merged = group[0].copy()
        
        # Merge additional information from other places
        for place in group[1:]:
            merged = self._merge_place_data(merged, place)
        
        # Update metadata
        merged['merged_from'] = len(group)
        merged['extraction_methods'] = list(set(p.get('extraction_method', '') for p in group))
        merged['confidence_score'] = max(p.get('confidence_score', 0) for p in group)
        
        return merged
    
    def _merge_place_data(self, primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
        """Merge secondary place data into primary place."""
        merged = primary.copy()
        
        # Merge description if primary is missing or secondary is longer
        if not merged.get('description') and secondary.get('description'):
            merged['description'] = secondary['description']
        elif merged.get('description') and secondary.get('description'):
            if len(secondary['description']) > len(merged['description']):
                merged['description'] = secondary['description']
        
        # Merge image if primary is missing
        if not merged.get('image_url') and secondary.get('image_url'):
            merged['image_url'] = secondary['image_url']
        
        # Merge area if primary is missing
        if not merged.get('area') and secondary.get('area'):
            merged['area'] = secondary['area']
        
        # Merge tags
        tags1 = set(merged.get('tags', []))
        tags2 = set(secondary.get('tags', []))
        merged['tags'] = list(tags1.union(tags2))
        
        # Merge flags
        flags1 = set(merged.get('flags', []))
        flags2 = set(secondary.get('flags', []))
        merged['flags'] = list(flags1.union(flags2))
        
        # Merge metadata
        metadata1 = merged.get('metadata', {})
        metadata2 = secondary.get('metadata', {})
        merged['metadata'] = {**metadata1, **metadata2}
        
        return merged
    
    def get_extraction_summary(self, places: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary of extraction results."""
        if not places:
            return {'total_places': 0}
        
        # Count by method
        method_counts = {}
        confidence_scores = []
        
        for place in places:
            method = place.get('extraction_method', 'unknown')
            method_counts[method] = method_counts.get(method, 0) + 1
            
            confidence = place.get('confidence_score', 0)
            confidence_scores.append(confidence)
        
        # Calculate statistics
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        min_confidence = min(confidence_scores) if confidence_scores else 0
        max_confidence = max(confidence_scores) if confidence_scores else 0
        
        return {
            'total_places': len(places),
            'method_counts': method_counts,
            'confidence_stats': {
                'average': round(avg_confidence, 3),
                'minimum': round(min_confidence, 3),
                'maximum': round(max_confidence, 3)
            },
            'fallback_order': self.fallback_order,
            'methods_available': {
                'jsonld': self.jsonld_extractor is not None,
                'og': self.og_extractor is not None,
                'css': self.css_extractor is not None
            }
        }


# Фабрика для создания fallback движка
def create_fallback_engine(recipe: Any) -> FallbackEngine:
    """Create and return a fallback engine instance."""
    return FallbackEngine(recipe)
