#!/usr/bin/env python3
"""
Universal extractor engine for different content types.
"""

import logging
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Union, Tuple
from urllib.parse import urljoin, urlparse
from pathlib import Path
import time

from .recipe_engine import SourceRecipe
from .extractors import create_extractor, UniversalExtractor

logger = logging.getLogger(__name__)


class ContentType:
    """Content type enumeration."""
    LIST = "list"           # List of places (e.g., "Best restaurants")
    ARTICLE = "article"      # Single place article
    GALLERY = "gallery"     # Image gallery with places
    SEARCH = "search"       # Search results
    CATEGORY = "category"   # Category page
    UNKNOWN = "unknown"     # Unknown content type


class ExtractorEngine:
    """Universal extractor engine for different content types."""
    
    def __init__(self, recipe: SourceRecipe):
        """Initialize extractor engine with recipe."""
        self.recipe = recipe
        self.extractor = create_extractor(recipe)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Performance settings
        self.request_delay = recipe.performance.get('request_delay', 1.0)
        self.timeout = recipe.performance.get('timeout', 30)
        self.max_retries = recipe.performance.get('max_retries', 3)
        self.user_agent = recipe.performance.get('user_agent', 'Mozilla/5.0 (compatible; BangkokPlacesParser/1.0)')
        
        # Content type detection patterns
        self.content_patterns = {
            ContentType.LIST: [
                'list', 'best', 'top', 'guide', 'roundup', 'collection',
                'restaurants', 'cafes', 'bars', 'places', 'venues'
            ],
            ContentType.ARTICLE: [
                'restaurant', 'cafe', 'bar', 'gallery', 'museum', 'park',
                'review', 'feature', 'story', 'article'
            ],
            ContentType.GALLERY: [
                'gallery', 'photos', 'images', 'pictures', 'slideshow',
                'visual', 'tour', 'walkthrough'
            ],
            ContentType.SEARCH: [
                'search', 'results', 'find', 'query', 'filter'
            ],
            ContentType.CATEGORY: [
                'category', 'section', 'directory', 'index'
            ]
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={'User-Agent': self.user_agent},
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def extract_from_url(self, url: str, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract places from a specific URL."""
        try:
            # Detect content type if not provided
            if not content_type:
                content_type = self._detect_content_type_from_url(url)
            
            logger.info(f"Extracting from {url} (type: {content_type})")
            
            # Fetch HTML content
            html = await self._fetch_html(url)
            if not html:
                return []
            
            # Extract places based on content type
            if content_type == ContentType.LIST:
                places = await self._extract_from_list_page(html, url)
            elif content_type == ContentType.ARTICLE:
                places = await self._extract_from_article_page(html, url)
            elif content_type == ContentType.GALLERY:
                places = await self._extract_from_gallery_page(html, url)
            elif content_type == ContentType.SEARCH:
                places = await self._extract_from_search_page(html, url)
            elif content_type == ContentType.CATEGORY:
                places = await self._extract_from_category_page(html, url)
            else:
                # Fallback to universal extraction
                places = self.extractor.extract(html, url)
            
            # Apply quality filtering
            places = self._filter_by_quality(places)
            
            # Add metadata
            for place in places:
                place['content_type'] = content_type
                place['extracted_at'] = time.time()
            
            logger.info(f"Extracted {len(places)} places from {url}")
            return places
            
        except Exception as e:
            logger.error(f"Error extracting from {url}: {e}")
            return []
    
    async def extract_from_category(self, category_name: str, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """Extract places from a specific category."""
        try:
            # Find category in recipe
            category = self._find_category(category_name)
            if not category:
                logger.warning(f"Category '{category_name}' not found in recipe")
                return []
            
            logger.info(f"Extracting from category: {category_name}")
            
            # Get category URL
            category_url = urljoin(self.recipe.base_url, category['url'])
            
            # Extract from category page
            all_places = []
            current_url = category_url
            page_count = 0
            
            max_pages = max_pages or self.recipe.max_pages
            
            while current_url and page_count < max_pages:
                logger.info(f"Processing page {page_count + 1}: {current_url}")
                
                # Extract places from current page
                places = await self.extract_from_url(current_url, ContentType.CATEGORY)
                all_places.extend(places)
                
                # Find next page
                next_url = await self._find_next_page(current_url)
                if next_url == current_url:  # No more pages
                    break
                
                current_url = next_url
                page_count += 1
                
                # Respect rate limiting
                if self.request_delay > 0:
                    await asyncio.sleep(self.request_delay)
            
            # Remove duplicates
            unique_places = self._deduplicate_places(all_places)
            
            logger.info(f"Extracted {len(unique_places)} unique places from category '{category_name}'")
            return unique_places
            
        except Exception as e:
            logger.error(f"Error extracting from category '{category_name}': {e}")
            return []
    
    async def extract_all_categories(self, max_pages_per_category: Optional[int] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Extract places from all categories."""
        try:
            all_categories = {}
            
            for category in self.recipe.categories:
                category_name = category['name']
                logger.info(f"Processing category: {category_name}")
                
                places = await self.extract_from_category(category_name, max_pages_per_category)
                all_categories[category_name] = places
                
                # Respect rate limiting between categories
                if self.request_delay > 0:
                    await asyncio.sleep(self.request_delay)
            
            return all_categories
            
        except Exception as e:
            logger.error(f"Error extracting from all categories: {e}")
            return {}
    
    def _detect_content_type_from_url(self, url: str) -> str:
        """Detect content type from URL."""
        url_lower = url.lower()
        
        for content_type, patterns in self.content_patterns.items():
            for pattern in patterns:
                if pattern in url_lower:
                    return content_type
        
        return ContentType.UNKNOWN
    
    def _detect_content_type_from_html(self, html: str) -> str:
        """Detect content type from HTML content."""
        html_lower = html.lower()
        
        # Check for list indicators
        if any(indicator in html_lower for indicator in ['<ul>', '<ol>', 'list-item', 'list-item']):
            return ContentType.LIST
        
        # Check for article indicators
        if any(indicator in html_lower for indicator in ['<article>', 'article', 'post', 'entry']):
            return ContentType.ARTICLE
        
        # Check for gallery indicators
        if any(indicator in html_lower for indicator in ['gallery', 'slideshow', 'carousel', 'lightbox']):
            return ContentType.GALLERY
        
        # Check for search indicators
        if any(indicator in html_lower for indicator in ['search', 'results', 'query']):
            return ContentType.SEARCH
        
        return ContentType.UNKNOWN
    
    async def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL with retries."""
        if not self.session:
            logger.error("Session not initialized. Use async context manager.")
            return None
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
        return None
    
    async def _extract_from_list_page(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Extract places from a list page."""
        logger.debug(f"Extracting from list page: {url}")
        
        # Use universal extractor with list-specific optimizations
        places = self.extractor.extract(html, url)
        
        # List pages typically have multiple places
        if len(places) < 2:
            logger.debug(f"List page {url} returned only {len(places)} places, might not be a list")
        
        return places
    
    async def _extract_from_article_page(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Extract places from an article page."""
        logger.debug(f"Extracting from article page: {url}")
        
        # Article pages should have detailed information
        places = self.extractor.extract(html, url)
        
        # Enhance article data if possible
        for place in places:
            # Try to extract more detailed information
            place = await self._enhance_place_data(place, html)
        
        return places
    
    async def _extract_from_gallery_page(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Extract places from a gallery page."""
        logger.debug(f"Extracting from gallery page: {url}")
        
        # Gallery pages focus on images
        places = self.extractor.extract(html, url)
        
        # Prioritize places with images
        places_with_images = [p for p in places if p.get('image_url')]
        places_without_images = [p for p in places if not p.get('image_url')]
        
        # Return places with images first
        return places_with_images + places_without_images
    
    async def _extract_from_search_page(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Extract places from a search results page."""
        logger.debug(f"Extracting from search page: {url}")
        
        # Search pages are similar to list pages
        return await self._extract_from_list_page(html, url)
    
    async def _extract_from_category_page(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Extract places from a category page."""
        logger.debug(f"Extracting from category page: {url}")
        
        # Category pages are typically list pages
        return await self._extract_from_list_page(html, url)
    
    async def _enhance_place_data(self, place: Dict[str, Any], html: str) -> Dict[str, Any]:
        """Enhance place data with additional information from HTML."""
        # This is a placeholder for future enhancement logic
        # Could include:
        # - Price extraction
        # - Opening hours
        # - Contact information
        # - Reviews/ratings
        return place
    
    async def _find_next_page(self, current_url: str) -> Optional[str]:
        """Find next page URL for pagination."""
        if not self.recipe.next_page_selector:
            return None
        
        try:
            html = await self._fetch_html(current_url)
            if not html:
                return None
            
            # Use BeautifulSoup to find next page link
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            next_link = soup.select_one(self.recipe.next_page_selector)
            if next_link and next_link.get('href'):
                next_url = urljoin(current_url, next_link['href'])
                if next_url != current_url:
                    return next_url
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding next page for {current_url}: {e}")
            return None
    
    def _find_category(self, category_name: str) -> Optional[Dict[str, Any]]:
        """Find category by name."""
        for category in self.recipe.categories:
            if category['name'].lower() == category_name.lower():
                return category
        return None
    
    def _filter_by_quality(self, places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter places by quality score."""
        min_score = self.recipe.min_quality_score
        
        filtered_places = []
        for place in places:
            # Calculate quality score
            quality_score = self._calculate_quality_score(place)
            place['quality_score'] = quality_score
            
            # Filter by minimum score
            if quality_score >= min_score:
                filtered_places.append(place)
            else:
                logger.debug(f"Place {place.get('name', 'Unknown')} filtered out (score: {quality_score})")
        
        return filtered_places
    
    def _calculate_quality_score(self, place: Dict[str, Any]) -> float:
        """Calculate quality score for a place."""
        scoring = self.recipe.quality_scoring
        score = 0.0
        
        # Check for required elements
        if place.get('name'):
            score += scoring.get('has_name', 10)
        
        if place.get('description'):
            score += scoring.get('has_description', 30)
        
        if place.get('image_url'):
            score += scoring.get('has_image', 20)
        
        if place.get('area'):
            score += scoring.get('has_area', 15)
        
        if place.get('price_level'):
            score += scoring.get('has_price', 10)
        
        if place.get('tags'):
            score += scoring.get('has_tags', 15)
        
        # Normalize to 0-1 range
        max_possible_score = sum(scoring.values())
        if max_possible_score > 0:
            score = score / max_possible_score
        
        return min(score, 1.0)
    
    def _deduplicate_places(self, places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate places based on name and URL."""
        seen = set()
        unique_places = []
        
        for place in places:
            # Create unique key
            key = f"{place.get('name', '')}_{place.get('url', '')}"
            
            if key not in seen:
                seen.add(key)
                unique_places.append(place)
        
        return unique_places
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        return {
            'recipe_name': self.recipe.name,
            'recipe_domain': self.recipe.domain,
            'extraction_methods': self.recipe.get_extraction_methods(),
            'quality_threshold': self.recipe.min_quality_score,
            'performance_settings': {
                'request_delay': self.request_delay,
                'timeout': self.timeout,
                'max_retries': self.max_retries
            }
        }


# Фабрика для создания движка извлечения
def create_extractor_engine(recipe: SourceRecipe) -> ExtractorEngine:
    """Create and return an extractor engine instance."""
    return ExtractorEngine(recipe)
