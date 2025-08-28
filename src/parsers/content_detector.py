#!/usr/bin/env python3
"""
Intelligent content type detector.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ContentTypeDetector:
    """Intelligent detector for different content types."""
    
    def __init__(self):
        """Initialize content type detector."""
        # URL patterns for different content types
        self.url_patterns = {
            'list': [
                # General patterns
                r'/list', r'/best', r'/top', r'/guide', r'/roundup',
                r'/collection', r'/directory', r'/index', r'/all',
                r'best-', r'top-', r'guide-', r'list-',
                # Timeout specific
                r'/restaurants', r'/cafes', r'/bars', r'/nightlife',
                r'/shopping', r'/art', r'/wellness', r'/attractions',
                r'/things-to-do', r'/events', r'/culture',
                r'/restaurant', r'/cafe', r'/bar',  # Singular forms
                # BK Magazine specific
                r'/guides', r'/features', r'/roundups', r'/lists',
                # Common patterns
                r'best-of', r'top-10', r'ultimate-guide', r'complete-guide'
            ],
            'article': [
                # General patterns
                r'/restaurant/', r'/cafe/', r'/bar/', r'/gallery/',
                r'/museum/', r'/park/', r'/review/', r'/feature/',
                r'/story/', r'/article/', r'/post/', r'/entry/',
                # Timeout specific
                r'/restaurant/', r'/cafe/', r'/bar/', r'/gallery/',
                r'/museum/', r'/park/', r'/attraction/',
                # BK Magazine specific
                r'/feature/', r'/story/', r'/review/',
                # Common patterns
                r'/place/', r'/venue/', r'/spot/'
            ],
            'gallery': [
                # General patterns
                r'/gallery', r'/photos', r'/images', r'/pictures',
                r'/slideshow', r'/visual', r'/tour', r'/walkthrough',
                # Timeout specific
                r'/gallery', r'/photos', r'/pictures', r'/visual',
                # BK Magazine specific
                r'/gallery', r'/photos', r'/visual',
                # Common patterns
                r'photo-', r'image-', r'picture-'
            ],
            'search': [
                # General patterns
                r'/search', r'/results', r'/find', r'/query',
                r'/filter', r'search=', r'q=', r'query=',
                # Timeout specific
                r'/search', r'/results', r'/find',
                # BK Magazine specific
                r'/search', r'/results',
                # Common patterns
                r'search-', r'results-', r'find-'
            ],
            'category': [
                # General patterns
                r'/category/', r'/section/', r'/food-drink',
                r'/restaurants', r'/cafes', r'/bars', r'/art',
                r'/shopping', r'/entertainment', r'/wellness',
                # Timeout specific
                r'/food-drink', r'/restaurants', r'/cafes', r'/bars',
                r'/nightlife', r'/shopping', r'/art', r'/wellness',
                r'/attractions', r'/things-to-do', r'/events', r'/culture',
                # BK Magazine specific
                r'/food', r'/drink', r'/culture', r'/lifestyle',
                r'/travel', r'/shopping', r'/wellness',
                # Common patterns
                r'/food', r'/drink', r'/culture', r'/lifestyle'
            ]
        }
        
        # HTML structure patterns
        self.html_patterns = {
            'list': [
                # HTML elements
                '<ul>', '<ol>', 'list-item', 'list-item',
                # CSS classes
                'grid-item', 'card', 'item', 'entry', 'listing',
                'restaurant-item', 'cafe-item', 'bar-item',
                'place-item', 'venue-item', 'spot-item',
                # Common patterns
                'list-', 'item-', 'card-', 'grid-'
            ],
            'article': [
                # HTML elements
                '<article>', 'article', 'post', 'entry',
                # CSS classes
                'single', 'detail', 'full', 'complete',
                'restaurant-detail', 'cafe-detail', 'bar-detail',
                'place-detail', 'venue-detail', 'spot-detail',
                # Common patterns
                'detail-', 'single-', 'full-', 'complete-'
            ],
            'gallery': [
                # CSS classes
                'gallery', 'slideshow', 'carousel', 'lightbox',
                'photo-grid', 'image-grid', 'visual-tour',
                'image-slider', 'photo-slider', 'image-carousel',
                # Common patterns
                'gallery-', 'photo-', 'image-', 'slide-'
            ],
            'search': [
                # CSS classes
                'search-results', 'search-list', 'results-grid',
                'no-results', 'search-form', 'search-page',
                'results-page', 'find-results', 'query-results',
                # Common patterns
                'search-', 'results-', 'find-', 'query-'
            ],
            'category': [
                # CSS classes
                'category-page', 'section-page', 'directory-page',
                'category-list', 'section-list', 'directory-list',
                'browse-page', 'explore-page', 'discover-page',
                # Common patterns
                'category-', 'section-', 'directory-', 'browse-'
            ]
        }
        
        # Content indicators
        self.content_indicators = {
            'list': [
                # General indicators
                'best restaurants', 'top cafes', 'guide to',
                'our picks', 'recommended', 'favorites',
                'must-visit', 'essential', 'ultimate guide',
                # Timeout specific
                'best of bangkok', 'top places', 'essential bangkok',
                'bangkok guide', 'bangkok picks', 'bangkok favorites',
                # BK Magazine specific
                'bangkok guide', 'thailand guide', 'asia guide',
                # Common patterns
                'best of', 'top 10', 'ultimate guide', 'complete guide',
                'comprehensive guide', 'definitive guide'
            ],
            'article': [
                # General indicators
                'restaurant review', 'cafe review', 'bar review',
                'restaurant guide', 'cafe guide', 'bar guide',
                'restaurant story', 'cafe story', 'bar story',
                # Timeout specific
                'restaurant review bangkok', 'cafe review bangkok',
                'bangkok restaurant', 'bangkok cafe', 'bangkok bar',
                # BK Magazine specific
                'feature story', 'in-depth', 'detailed review',
                # Common patterns
                'review of', 'story about', 'feature on', 'spotlight on'
            ],
            'gallery': [
                # General indicators
                'photo gallery', 'image gallery', 'picture gallery',
                'visual tour', 'photo tour', 'image tour',
                'slideshow', 'carousel', 'lightbox',
                # Timeout specific
                'bangkok photos', 'bangkok gallery', 'bangkok images',
                # BK Magazine specific
                'photo essay', 'visual story', 'image collection',
                # Common patterns
                'photo collection', 'image collection', 'visual collection'
            ],
            'search': [
                # General indicators
                'search results', 'search results for',
                'found results', 'no results found',
                'search query', 'search term',
                # Timeout specific
                'search bangkok', 'find bangkok', 'bangkok search',
                # BK Magazine specific
                'search results', 'find results', 'query results',
                # Common patterns
                'search for', 'find', 'query', 'results for'
            ],
            'category': [
                # General indicators
                'category', 'section', 'directory',
                'all restaurants', 'all cafes', 'all bars',
                'restaurant directory', 'cafe directory',
                # Timeout specific
                'bangkok restaurants', 'bangkok cafes', 'bangkok bars',
                'bangkok food', 'bangkok drink', 'bangkok culture',
                # BK Magazine specific
                'bangkok guide', 'thailand guide', 'asia guide',
                # Common patterns
                'all places', 'directory', 'browse', 'explore'
            ]
        }
        
        # Confidence weights
        self.confidence_weights = {
            'url': 0.4,      # URL patterns
            'html': 0.3,     # HTML structure
            'content': 0.3   # Content text
        }
    
    def detect_content_type(self, url: str, html: str) -> Tuple[str, float]:
        """Detect content type with confidence score."""
        url_score = self._detect_from_url(url)
        html_score = self._detect_from_html(html)
        content_score = self._detect_from_content(html)
        
        # Combine scores
        combined_scores = {}
        for content_type in ['list', 'article', 'gallery', 'search', 'category']:
            score = (
                url_score.get(content_type, 0) * self.confidence_weights['url'] +
                html_score.get(content_type, 0) * self.confidence_weights['html'] +
                content_score.get(content_type, 0) * self.confidence_weights['content']
            )
            combined_scores[content_type] = score
        
        # Find best match
        best_type = max(combined_scores, key=combined_scores.get)
        confidence = combined_scores[best_type]
        
        # If confidence is too low, return unknown
        if confidence < 0.3:
            best_type = 'unknown'
            confidence = 0.0
        
        logger.debug(f"Content type detection: {best_type} (confidence: {confidence:.2f})")
        return best_type, confidence
    
    def _detect_from_url(self, url: str) -> Dict[str, float]:
        """Detect content type from URL patterns."""
        url_lower = url.lower()
        scores = {content_type: 0.0 for content_type in self.url_patterns.keys()}
        
        # Domain-specific enhancements
        domain_enhancements = self._get_domain_enhancements(url_lower)
        
        for content_type, patterns in self.url_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    # Different weights for different pattern types
                    if pattern.startswith('/') and pattern.endswith('/'):
                        # Exact path match (e.g., /restaurant/)
                        scores[content_type] += 0.4
                    elif pattern.startswith('/') and not pattern.endswith('/'):
                        # Path prefix (e.g., /restaurants)
                        scores[content_type] += 0.3
                    elif pattern.endswith('/'):
                        # Path suffix (e.g., restaurant/)
                        scores[content_type] += 0.3
                    elif '=' in pattern:
                        # Query parameter (e.g., search=)
                        scores[content_type] += 0.25
                    else:
                        # General pattern (e.g., best-)
                        scores[content_type] += 0.2
            
            # Apply domain enhancements
            if content_type in domain_enhancements:
                scores[content_type] += domain_enhancements[content_type]
            
            # Normalize scores
            if scores[content_type] > 0:
                scores[content_type] = min(scores[content_type], 1.0)
        
        return scores
    
    def _get_domain_enhancements(self, url_lower: str) -> Dict[str, float]:
        """Get domain-specific enhancements for content type detection."""
        enhancements = {content_type: 0.0 for content_type in self.url_patterns.keys()}
        
        # Timeout.com specific enhancements
        if 'timeout.com' in url_lower:
            if '/bangkok/' in url_lower:
                # Bangkok-specific sections
                if any(section in url_lower for section in ['/restaurants', '/cafes', '/bars']):
                    enhancements['list'] += 0.2
                    enhancements['category'] += 0.1
                elif '/restaurant/' in url_lower or '/cafe/' in url_lower or '/bar/' in url_lower:
                    enhancements['article'] += 0.2
                elif '/gallery' in url_lower:
                    enhancements['gallery'] += 0.2
                elif 'search' in url_lower:
                    enhancements['search'] += 0.2
        
        # BK Magazine specific enhancements
        elif 'bk.asia' in url_lower:
            if '/guides/' in url_lower:
                enhancements['list'] += 0.2
            elif '/feature/' in url_lower:
                enhancements['article'] += 0.2
            elif '/gallery' in url_lower:
                enhancements['gallery'] += 0.2
        
        return enhancements
    
    def _detect_from_html(self, html: str) -> Dict[str, float]:
        """Detect content type from HTML structure."""
        html_lower = html.lower()
        scores = {content_type: 0.0 for content_type in self.html_patterns.keys()}
        
        for content_type, patterns in self.html_patterns.items():
            for pattern in patterns:
                if pattern in html_lower:
                    # Different weights for different pattern types
                    if pattern.startswith('<') and pattern.endswith('>'):
                        # HTML tags (e.g., <ul>, <article>)
                        scores[content_type] += 0.25
                    elif pattern.startswith('list-') or pattern.startswith('item-'):
                        # List-specific classes
                        scores[content_type] += 0.2
                    elif pattern.startswith('detail-') or pattern.startswith('single-'):
                        # Article-specific classes
                        scores[content_type] += 0.2
                    elif pattern.startswith('gallery-') or pattern.startswith('photo-'):
                        # Gallery-specific classes
                        scores[content_type] += 0.2
                    elif pattern.startswith('search-') or pattern.startswith('results-'):
                        # Search-specific classes
                        scores[content_type] += 0.2
                    elif pattern.startswith('category-') or pattern.startswith('section-'):
                        # Category-specific classes
                        scores[content_type] += 0.2
                    else:
                        # General patterns
                        scores[content_type] += 0.15
            
            # Normalize scores
            if scores[content_type] > 0:
                scores[content_type] = min(scores[content_type], 1.0)
        
        return scores
    
    def _detect_from_content(self, html: str) -> Dict[str, float]:
        """Detect content type from content text."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style content
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get visible text
        visible_text = soup.get_text().lower()
        
        scores = {content_type: 0.0 for content_type in self.content_indicators.keys()}
        
        for content_type, indicators in self.content_indicators.items():
            for indicator in indicators:
                if indicator in visible_text:
                    # Different weights for different indicator types
                    if 'bangkok' in indicator:
                        # Bangkok-specific indicators get higher weight
                        scores[content_type] += 0.15
                    elif 'guide' in indicator or 'best' in indicator or 'top' in indicator:
                        # Guide/best/top indicators
                        scores[content_type] += 0.12
                    elif 'review' in indicator or 'story' in indicator:
                        # Review/story indicators
                        scores[content_type] += 0.12
                    elif 'gallery' in indicator or 'photo' in indicator or 'image' in indicator:
                        # Gallery/photo/image indicators
                        scores[content_type] += 0.12
                    elif 'search' in indicator or 'results' in indicator:
                        # Search/results indicators
                        scores[content_type] += 0.12
                    else:
                        # General indicators
                        scores[content_type] += 0.1
            
            # Normalize scores
            if scores[content_type] > 0:
                scores[content_type] = min(scores[content_type], 1.0)
        
        return scores
    
    def get_detailed_analysis(self, url: str, html: str) -> Dict[str, Any]:
        """Get detailed content type analysis."""
        url_score = self._detect_from_url(url)
        html_score = self._detect_from_html(html)
        content_score = self._detect_from_content(html)
        
        # Calculate combined scores
        combined_scores = {}
        for content_type in ['list', 'article', 'gallery', 'search', 'category']:
            score = (
                url_score.get(content_type, 0) * self.confidence_weights['url'] +
                html_score.get(content_type, 0) * self.confidence_weights['html'] +
                content_score.get(content_type, 0) * self.confidence_weights['content']
            )
            combined_scores[content_type] = round(score, 3)
        
        # Find best match
        best_type = max(combined_scores, key=combined_scores.get)
        confidence = combined_scores[best_type]
        
        # If confidence is too low, return unknown
        if confidence < 0.3:
            best_type = 'unknown'
            confidence = 0.0
        
        return {
            'detected_type': best_type,
            'confidence': confidence,
            'url_analysis': url_score,
            'html_analysis': html_score,
            'content_analysis': content_score,
            'combined_scores': combined_scores,
            'weights': self.confidence_weights
        }
    
    def is_list_page(self, url: str, html: str) -> bool:
        """Check if page is a list page."""
        content_type, confidence = self.detect_content_type(url, html)
        return content_type == 'list' and confidence > 0.5
    
    def is_article_page(self, url: str, html: str) -> bool:
        """Check if page is an article page."""
        content_type, confidence = self.detect_content_type(url, html)
        return content_type == 'article' and confidence > 0.5
    
    def is_gallery_page(self, url: str, html: str) -> bool:
        """Check if page is a gallery page."""
        content_type, confidence = self.detect_content_type(url, html)
        return content_type == 'gallery' and confidence > 0.5
    
    def get_page_characteristics(self, html: str) -> Dict[str, Any]:
        """Get detailed page characteristics."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Count different elements
        elements = {
            'images': len(soup.find_all('img')),
            'links': len(soup.find_all('a')),
            'lists': len(soup.find_all(['ul', 'ol'])),
            'articles': len(soup.find_all('article')),
            'sections': len(soup.find_all('section')),
            'divs': len(soup.find_all('div')),
            'paragraphs': len(soup.find_all('p')),
            'headings': len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
        }
        
        # Check for specific classes
        classes = {
            'list_classes': len(soup.find_all(class_=re.compile(r'list|item|card|grid'))),
            'gallery_classes': len(soup.find_all(class_=re.compile(r'gallery|photo|image|slideshow'))),
            'article_classes': len(soup.find_all(class_=re.compile(r'article|post|entry|story'))),
            'search_classes': len(soup.find_all(class_=re.compile(r'search|result|query')))
        }
        
        # Check for JSON-LD
        jsonld_scripts = soup.find_all('script', type='application/ld+json')
        jsonld_count = len(jsonld_scripts)
        
        # Check for Open Graph
        og_tags = soup.find_all('meta', property=re.compile(r'^og:'))
        og_count = len(og_tags)
        
        return {
            'elements': elements,
            'classes': classes,
            'jsonld_count': jsonld_count,
            'og_count': og_count,
            'total_elements': sum(elements.values()),
            'has_structured_data': jsonld_count > 0 or og_count > 0
        }


# Глобальный экземпляр детектора
content_detector = ContentTypeDetector()


def detect_content_type(url: str, html: str) -> Tuple[str, float]:
    """Detect content type with confidence score."""
    return content_detector.detect_content_type(url, html)


def get_detailed_analysis(url: str, html: str) -> Dict[str, Any]:
    """Get detailed content type analysis."""
    return content_detector.get_detailed_analysis(url, html)
