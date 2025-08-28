#!/usr/bin/env python3
"""
Base normalizer for data cleaning and standardization.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Union
# ABC and abstractmethod no longer needed

logger = logging.getLogger(__name__)


class BaseNormalizer:
    """Base class for data normalization."""
    
    def __init__(self):
        """Initialize base normalizer."""
        # Common cleaning patterns
        self.html_tags = re.compile(r'<[^>]+>')
        self.extra_spaces = re.compile(r'\s+')
        self.special_chars = re.compile(r'[^\w\s\-.,!?()&]')
        self.multiple_dots = re.compile(r'\.{2,}')
        self.multiple_dashes = re.compile(r'-{2,}')
        
        # Text length limits
        self.max_title_length = 100
        self.max_description_length = 220
        self.max_area_length = 50
        
        # Common abbreviations and their full forms
        self.abbreviations = {
            'st.': 'Street',
            'rd.': 'Road',
            'ave.': 'Avenue',
            'blvd.': 'Boulevard',
            'dr.': 'Drive',
            'ln.': 'Lane',
            'ct.': 'Court',
            'pl.': 'Place',
            'sq.': 'Square',
            'pkwy.': 'Parkway',
            'co.': 'Company',
            'corp.': 'Corporation',
            'inc.': 'Incorporated',
            'ltd.': 'Limited',
            'llc': 'LLC',
            'bkk': 'Bangkok',
            'th': 'Thailand'
        }
    
    def normalize_place(self, place: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a place dictionary."""
        try:
            normalized = place.copy()
            
            # Normalize basic fields
            if 'name' in normalized:
                normalized['name'] = self.normalize_title(normalized['name'])
            
            if 'description' in normalized:
                normalized['description'] = self.normalize_description(normalized['description'])
            
            if 'area' in normalized:
                normalized['area'] = self.normalize_area(normalized['area'])
            
            if 'tags' in normalized:
                normalized['tags'] = self.normalize_tags(normalized['tags'])
            
            if 'flags' in normalized:
                normalized['flags'] = self.normalize_flags(normalized['flags'])
            
            # Add normalization metadata
            normalized['normalized_at'] = self._get_timestamp()
            normalized['normalizer_version'] = '1.0'
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing place: {e}")
            return place
    
    def normalize_title(self, title: str) -> str:
        """Normalize place title."""
        if not title:
            return title
        
        # Clean HTML tags
        title = self.html_tags.sub('', title)
        
        # Remove extra spaces
        title = self.extra_spaces.sub(' ', title)
        
        # Strip whitespace
        title = title.strip()
        
        # Convert to title case
        title = self._to_title_case(title)
        
        # Expand abbreviations
        title = self._expand_abbreviations(title)
        
        # Truncate if too long
        if len(title) > self.max_title_length:
            title = title[:self.max_title_length].rsplit(' ', 1)[0] + '...'
        
        return title
    
    def normalize_description(self, description: str) -> str:
        """Normalize place description."""
        if not description:
            return description
        
        # Clean HTML tags
        description = self.html_tags.sub('', description)
        
        # Remove extra spaces
        description = self.extra_spaces.sub(' ', description)
        
        # Strip whitespace
        description = description.strip()
        
        # Clean special characters
        description = self.special_chars.sub('', description)
        
        # Clean multiple dots and dashes
        description = self.multiple_dots.sub('.', description)
        description = self.multiple_dashes.sub('-', description)
        
        # Truncate if too long
        if len(description) > self.max_description_length:
            description = description[:self.max_description_length].rsplit(' ', 1)[0] + '...'
        
        return description
    
    def normalize_area(self, area: str) -> str:
        """Normalize area/location field."""
        if not area:
            return area
        
        # Clean HTML tags
        area = self.html_tags.sub('', area)
        
        # Remove extra spaces
        area = self.extra_spaces.sub(' ', area)
        
        # Strip whitespace
        area = area.strip()
        
        # Convert to title case
        area = self._to_title_case(area)
        
        # Expand abbreviations
        area = self._expand_abbreviations(area)
        
        # Truncate if too long
        if len(area) > self.max_area_length:
            area = area[:self.max_area_length].rsplit(' ', 1)[0] + '...'
        
        return area
    
    def normalize_tags(self, tags: List[str]) -> List[str]:
        """Normalize tags list."""
        if not tags:
            return []
        
        normalized_tags = []
        
        for tag in tags:
            if tag:
                # Clean and normalize each tag
                normalized_tag = self._normalize_single_tag(tag)
                if normalized_tag:
                    normalized_tags.append(normalized_tag)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in normalized_tags:
            if tag.lower() not in seen:
                seen.add(tag.lower())
                unique_tags.append(tag)
        
        return unique_tags
    
    def normalize_flags(self, flags: List[str]) -> List[str]:
        """Normalize flags list."""
        if not flags:
            return []
        
        normalized_flags = []
        
        for flag in flags:
            if flag:
                # Clean and normalize each flag
                normalized_flag = self._normalize_single_flag(flag)
                if normalized_flag:
                    normalized_flags.append(normalized_flag)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_flags = []
        for flag in normalized_flags:
            if flag.lower() not in seen:
                seen.add(flag.lower())
                unique_flags.append(flag)
        
        return unique_flags
    
    def _normalize_single_tag(self, tag: str) -> Optional[str]:
        """Normalize a single tag."""
        if not tag:
            return None
        
        # Clean HTML tags
        tag = self.html_tags.sub('', tag)
        
        # Remove extra spaces
        tag = self.extra_spaces.sub(' ', tag)
        
        # Strip whitespace
        tag = tag.strip()
        
        # Convert to lowercase for consistency
        tag = tag.lower()
        
        # Remove special characters except hyphens and underscores
        tag = re.sub(r'[^\w\s\-_]', '', tag)
        
        # Replace spaces with hyphens
        tag = tag.replace(' ', '-')
        
        return tag if tag else None
    
    def _normalize_single_flag(self, flag: str) -> Optional[str]:
        """Normalize a single flag."""
        if not flag:
            return None
        
        # Clean HTML tags
        flag = self.html_tags.sub('', flag)
        
        # Remove extra spaces
        flag = self.extra_spaces.sub(' ', flag)
        
        # Strip whitespace
        flag = flag.strip()
        
        # Convert to lowercase for consistency
        flag = flag.lower()
        
        # Remove special characters except hyphens and underscores
        flag = re.sub(r'[^\w\s\-_]', '', flag)
        
        # Replace spaces with underscores
        flag = flag.replace(' ', '_')
        
        return flag if flag else None
    
    def _to_title_case(self, text: str) -> str:
        """Convert text to title case with smart handling."""
        if not text:
            return text
        
        # Split into words
        words = text.split()
        
        # Process each word
        title_words = []
        for i, word in enumerate(words):
            # Skip common words that should be lowercase (except first word)
            if i > 0 and word.lower() in ['a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']:
                title_words.append(word.lower())
            else:
                # Capitalize first letter, lowercase the rest
                if word:
                    title_words.append(word[0].upper() + word[1:].lower())
                else:
                    title_words.append(word)
        
        return ' '.join(title_words)
    
    def _expand_abbreviations(self, text: str) -> str:
        """Expand common abbreviations."""
        if not text:
            return text
        
        # Replace abbreviations
        for abbrev, full_form in self.abbreviations.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            text = re.sub(pattern, full_form, text, flags=re.IGNORECASE)
        
        return text
    
    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()
    
    def normalize_specific_field(self, field_name: str, value: Any) -> Any:
        """Normalize a specific field."""
        if field_name == 'name':
            return self.normalize_title(str(value) if value else '')
        elif field_name == 'description':
            return self.normalize_description(str(value) if value else '')
        elif field_name == 'area':
            return self.normalize_area(str(value) if value else '')
        elif field_name == 'tags':
            return self.normalize_tags(value if isinstance(value, list) else [])
        elif field_name == 'flags':
            return self.normalize_flags(value if isinstance(value, list) else [])
        else:
            return value
    
    def get_normalization_stats(self, original: Dict[str, Any], normalized: Dict[str, Any]) -> Dict[str, Any]:
        """Get statistics about normalization changes."""
        stats = {
            'fields_normalized': 0,
            'characters_removed': 0,
            'length_changes': {},
            'quality_improvements': []
        }
        
        for field in ['name', 'description', 'area']:
            if field in original and field in normalized:
                original_value = str(original[field]) if original[field] else ''
                normalized_value = str(normalized[field]) if normalized[field] else ''
                
                if original_value != normalized_value:
                    stats['fields_normalized'] += 1
                    
                    # Calculate length changes
                    original_len = len(original_value)
                    normalized_len = len(normalized_value)
                    stats['length_changes'][field] = {
                        'original': original_len,
                        'normalized': normalized_len,
                        'difference': normalized_len - original_len
                    }
                    
                    # Calculate characters removed
                    if original_len > normalized_len:
                        stats['characters_removed'] += (original_len - normalized_len)
                    
                    # Quality improvements
                    if field == 'name':
                        if self._is_title_case(normalized_value):
                            stats['quality_improvements'].append(f'{field}: converted to title case')
                    elif field == 'description':
                        if len(normalized_value) <= self.max_description_length:
                            stats['quality_improvements'].append(f'{field}: truncated to {self.max_description_length} chars')
        
        return stats
    
    def _is_title_case(self, text: str) -> bool:
        """Check if text is in title case."""
        if not text:
            return False
        
        words = text.split()
        if not words:
            return False
        
        # Check if first word starts with uppercase
        if not words[0][0].isupper():
            return False
        
        # Check other words (should be lowercase except for proper nouns)
        for word in words[1:]:
            if word and word[0].isupper() and word.lower() in ['a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']:
                return False
        
        return True
