#!/usr/bin/env python3
"""
Base extractors for different data formats.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Union
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class BaseExtractor:
    """Base class for all extractors."""
    
    def __init__(self, recipe: Any):
        """Initialize extractor with recipe configuration."""
        self.recipe = recipe
    
    def extract(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Extract data from HTML. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement extract method")
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text."""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters if configured
        if self.recipe.cleaning.get('remove_special_chars', False):
            text = re.sub(r'[^\w\s\-.,!?]', '', text)
        
        return text.strip()
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate extracted data according to recipe rules."""
        validation = self.recipe.validation
        
        # Check required fields
        required_fields = validation.get('required_fields', [])
        for field in required_fields:
            if not data.get(field):
                return False
        
        # Check name length
        if 'name' in data:
            name = data['name']
            min_length = validation.get('min_name_length', 0)
            max_length = validation.get('max_name_length', 1000)
            
            if len(name) < min_length or len(name) > max_length:
                return False
        
        # Check description length
        if 'description' in data and data['description']:
            desc = data['description']
            min_length = validation.get('min_description_length', 0)
            
            if len(desc) < min_length:
                return False
        
        return True
    
    def post_process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply post-processing rules to extracted data."""
        post_processing = self.recipe.post_processing
        
        # Trim name
        if post_processing.get('trim_name', False) and 'name' in data:
            data['name'] = self._trim_name(data['name'])
        
        # Convert to title case
        if post_processing.get('title_case', False) and 'name' in data:
            data['name'] = data['name'].title()
        
        # Truncate description
        if post_processing.get('max_description_length') and 'description' in data:
            max_len = post_processing['max_description_length']
            if len(data['description']) > max_len:
                data['description'] = data['description'][:max_len-3] + "..."
        
        # Normalize area
        if post_processing.get('normalize_area', False) and 'area' in data:
            data['area'] = self._normalize_area(data['area'])
        
        # Extract price level
        if post_processing.get('extract_price_level', False):
            price_level = self._extract_price_level(data.get('description', '') + ' ' + data.get('name', ''))
            if price_level:
                data['price_level'] = price_level
        
        return data
    
    def _trim_name(self, name: str) -> str:
        """Remove extra symbols from place names."""
        # Remove common prefixes
        prefixes = ['-', '–', '—', '•', '№', '★', '☆']
        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[1:].strip()
        
        # Remove common suffixes
        suffixes = ['-', '–', '—', '•', '★', '☆']
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-1].strip()
        
        return name
    
    def _normalize_area(self, area: str) -> str:
        """Normalize area names."""
        if not area:
            return ""
        
        # Common area mappings
        area_mappings = {
            'sukhumvit': 'Sukhumvit',
            'silom': 'Silom',
            'siam': 'Siam',
            'pratunam': 'Pratunam',
            'chatuchak': 'Chatuchak',
            'chinatown': 'Chinatown',
            'yaowarat': 'Yaowarat',
            'thonglor': 'Thonglor',
            'ekkamai': 'Ekkamai',
            'phrom phong': 'Phrom Phong',
            'asoke': 'Asoke',
            'nana': 'Nana',
            'ploenchit': 'Ploenchit',
            'chitlom': 'Chitlom',
            'ratchaprasong': 'Ratchaprasong'
        }
        
        area_lower = area.lower().strip()
        return area_mappings.get(area_lower, area.title())
    
    def _extract_price_level(self, text: str) -> Optional[int]:
        """Extract price level from text."""
        text_lower = text.lower()
        
        # Price indicators
        price_indicators = {
            1: ['budget', 'cheap', 'affordable', 'street food', 'local', 'market'],
            2: ['moderate', 'mid-range', 'reasonable', 'casual'],
            3: ['expensive', 'luxury', 'fine dining', 'premium', 'upscale'],
            4: ['ultra luxury', 'exclusive', 'vip', 'high-end']
        }
        
        for level, indicators in price_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    return level
        
        return None


class JSONLDExtractor(BaseExtractor):
    """Extractor for JSON-LD structured data."""
    
    def extract(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Extract places from JSON-LD data."""
        soup = BeautifulSoup(html, 'html.parser')
        places = []
        
        # Find JSON-LD scripts
        jsonld_scripts = soup.find_all('script', type='application/ld+json')
        
        for script in jsonld_scripts:
            try:
                data = json.loads(script.string)
                extracted_places = self._extract_from_jsonld(data, url)
                places.extend(extracted_places)
            except (json.JSONDecodeError, AttributeError) as e:
                logger.debug(f"Failed to parse JSON-LD script: {e}")
                continue
        
        return places
    
    def _extract_from_jsonld(self, data: Any, url: str) -> List[Dict[str, Any]]:
        """Extract places from JSON-LD data structure."""
        places = []
        
        # Handle different JSON-LD structures
        if isinstance(data, dict):
            places.extend(self._extract_single_jsonld(data, url))
        elif isinstance(data, list):
            for item in data:
                places.extend(self._extract_single_jsonld(item, url))
        
        return places
    
    def _extract_single_jsonld(self, data: Dict[str, Any], url: str) -> List[Dict[str, Any]]:
        """Extract place from single JSON-LD object."""
        places = []
        
        # Check if this is a place
        if not self._is_place_type(data):
            return places
        
        # Extract basic information
        place_data = {
            'name': self._get_jsonld_value(data, self.recipe.jsonld_selectors.get('name_path', 'name')),
            'description': self._get_jsonld_value(data, self.recipe.jsonld_selectors.get('description_path', 'description')),
            'image_url': self._get_jsonld_value(data, self.recipe.jsonld_selectors.get('image_path', 'image')),
            'url': self._get_jsonld_value(data, self.recipe.jsonld_selectors.get('url_path', 'url'))
        }
        
        # Clean and validate
        place_data = {k: self.clean_text(v) for k, v in place_data.items() if v}
        
        # Add source information
        place_data['source_url'] = url
        place_data['source'] = self.recipe.domain
        
        # Validate data
        if self.validate_data(place_data):
            place_data = self.post_process(place_data)
            places.append(place_data)
        
        return places
    
    def _is_place_type(self, data: Dict[str, Any]) -> bool:
        """Check if JSON-LD data represents a place."""
        place_types = self.recipe.jsonld_selectors.get('place_type', '').split(',')
        place_types = [t.strip() for t in place_types if t.strip()]
        
        if not place_types:
            return True  # Accept all if no types specified
        
        # Check @type field
        jsonld_type = data.get('@type', '')
        if isinstance(jsonld_type, list):
            jsonld_type = ' '.join(jsonld_type)
        
        for place_type in place_types:
            if place_type.lower() in jsonld_type.lower():
                return True
        
        return False
    
    def _get_jsonld_value(self, data: Dict[str, Any], path: str) -> Optional[str]:
        """Get value from JSON-LD data using path."""
        if not path:
            return None
        
        # Simple path resolution
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        if isinstance(current, str):
            return current
        elif isinstance(current, list) and current:
            return str(current[0])
        
        return None


class OpenGraphExtractor(BaseExtractor):
    """Extractor for Open Graph meta tags."""
    
    def extract(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Extract places from Open Graph meta tags."""
        soup = BeautifulSoup(html, 'html.parser')
        places = []
        
        # Extract OG data
        og_data = self._extract_og_tags(soup)
        
        if og_data:
            # Create place data
            place_data = {
                'name': og_data.get('title', ''),
                'description': og_data.get('description', ''),
                'image_url': og_data.get('image', ''),
                'url': og_data.get('url', url)
            }
            
            # Clean data
            place_data = {k: self.clean_text(v) for k, v in place_data.items() if v}
            
            # Add source information
            place_data['source_url'] = url
            place_data['source'] = self.recipe.domain
            
            # Validate and post-process
            if self.validate_data(place_data):
                place_data = self.post_process(place_data)
                places.append(place_data)
        
        return places
    
    def _extract_og_tags(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract Open Graph meta tags."""
        og_data = {}
        
        # Find all meta tags
        meta_tags = soup.find_all('meta')
        
        for tag in meta_tags:
            property_attr = tag.get('property', '')
            content = tag.get('content', '')
            
            if property_attr.startswith('og:'):
                key = property_attr[3:]  # Remove 'og:' prefix
                og_data[key] = content
        
        return og_data


class CSSExtractor(BaseExtractor):
    """Extractor using CSS selectors."""
    
    def extract(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Extract places using CSS selectors."""
        soup = BeautifulSoup(html, 'html.parser')
        places = []
        
        # Find containers
        container_selector = self.recipe.css_selectors.get('container', '')
        if not container_selector:
            logger.warning("No container selector specified for CSS extraction")
            return places
        
        containers = soup.select(container_selector)
        
        for container in containers:
            place_data = self._extract_from_container(container, url)
            if place_data:
                places.append(place_data)
        
        return places
    
    def _extract_from_container(self, container: Tag, url: str) -> Optional[Dict[str, Any]]:
        """Extract place data from a container element."""
        selectors = self.recipe.css_selectors
        
        # Extract basic information
        place_data = {
            'name': self._extract_text(container, selectors.get('name', '')),
            'description': self._extract_text(container, selectors.get('description', '')),
            'image_url': self._extract_attribute(container, selectors.get('image', ''), 'src'),
            'url': self._extract_attribute(container, selectors.get('url', ''), 'href'),
            'area': self._extract_text(container, selectors.get('area', '')),
            'price': self._extract_text(container, selectors.get('price', '')),
            'tags': self._extract_tags(container, selectors.get('tags', ''))
        }
        
        # Clean data
        place_data = {k: self.clean_text(v) if isinstance(v, str) else v for k, v in place_data.items() if v}
        
        # Add source information
        place_data['source_url'] = url
        place_data['source'] = self.recipe.domain
        
        # Validate data
        if self.validate_data(place_data):
            place_data = self.post_process(place_data)
            return place_data
        
        return None
    
    def _extract_text(self, container: Tag, selector: str) -> Optional[str]:
        """Extract text using CSS selector."""
        if not selector:
            return None
        
        element = container.select_one(selector)
        if element:
            return element.get_text(strip=True)
        
        return None
    
    def _extract_attribute(self, container: Tag, selector: str, attr: str) -> Optional[str]:
        """Extract attribute value using CSS selector."""
        if not selector:
            return None
        
        element = container.select_one(selector)
        if element:
            value = element.get(attr, '')
            if value and attr == 'href':
                # Make URL absolute
                return urljoin(container.get('base_url', ''), value)
            return value
        
        return None
    
    def _extract_tags(self, container: Tag, selector: str) -> List[str]:
        """Extract tags using CSS selector."""
        if not selector:
            return []
        
        elements = container.select(selector)
        tags = []
        
        for element in elements:
            tag_text = element.get_text(strip=True)
            if tag_text:
                tags.append(tag_text)
        
        return tags


class UniversalExtractor:
    """Universal extractor that tries multiple methods."""
    
    def __init__(self, recipe: Any):
        """Initialize universal extractor."""
        self.recipe = recipe
        self.extractors = []
        
        # Initialize extractors based on recipe
        if recipe.jsonld_enabled:
            self.extractors.append(JSONLDExtractor(recipe))
        
        if recipe.og_enabled:
            self.extractors.append(OpenGraphExtractor(recipe))
        
        if recipe.css_enabled:
            self.extractors.append(CSSExtractor(recipe))
    
    def extract(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Extract places using all available methods."""
        all_places = []
        
        for extractor in self.extractors:
            try:
                places = extractor.extract(html, url)
                all_places.extend(places)
                logger.debug(f"Extractor {extractor.__class__.__name__} found {len(places)} places")
            except Exception as e:
                logger.error(f"Error in {extractor.__class__.__name__}: {e}")
                continue
        
        # Remove duplicates based on name and URL
        unique_places = self._deduplicate_places(all_places)
        
        logger.info(f"Total places extracted: {len(unique_places)}")
        return unique_places
    
    def _deduplicate_places(self, places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate places."""
        seen = set()
        unique_places = []
        
        for place in places:
            # Create key for deduplication
            key = f"{place.get('name', '')}_{place.get('url', '')}"
            
            if key not in seen:
                seen.add(key)
                unique_places.append(place)
        
        return unique_places


# Фабрика для создания экстракторов
def create_extractor(recipe: Any) -> UniversalExtractor:
    """Create appropriate extractor based on recipe."""
    return UniversalExtractor(recipe)
