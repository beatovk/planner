#!/usr/bin/env python3
"""
Parser for Timeout Bangkok places.
Extracts real places data from timeout.com/bangkok articles.
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
import re
import logging
from urllib.parse import urljoin, urlparse
import time

logger = logging.getLogger(__name__)

class TimeoutBangkokPlacesParser:
    """Parser for extracting places data from Timeout Bangkok."""
    
    def __init__(self):
        self.base_url = "https://www.timeout.com/bangkok"
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Категории и их URL-пути
        self.categories = {
            "food_dining": [
                "/food-drink",
                "/restaurants", 
                "/cafes"
            ],
            "art_exhibits": [
                "/art",
                "/things-to-do"
            ],
            "bars": [
                "/bars",
                "/music-nightlife"
            ],
            "shopping": [
                "/shopping",
                "/markets"
            ],
            "entertainment": [
                "/entertainment",
                "/movies"
            ],
            "wellness": [
                "/health-beauty",
                "/spas"
            ],
            "rooftop": [
                "/bars",  # Многие rooftop бары в разделе bars
                "/restaurants"  # И rooftop рестораны
            ]
        }
        
        # Заголовки для имитации браузера
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_page_content(self, url: str) -> Optional[str]:
        """Get HTML content of a page."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        try:
            full_url = urljoin(self.base_url, url)
            logger.info(f"Fetching: {full_url}")
            
            async with self.session.get(full_url) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"Successfully fetched {len(content)} characters from {full_url}")
                    return content
                else:
                    logger.warning(f"Failed to fetch {full_url}, status: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_article_links(self, html: str, category: str) -> List[Dict[str, str]]:
        """Extract article links from a category page."""
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        # Ищем ссылки на статьи
        # Timeout использует разные селекторы для статей
        article_selectors = [
            'a[href*="/food-drink/"]',
            'a[href*="/restaurants/"]',
            'a[href*="/art/"]',
            'a[href*="/things-to-do/"]',
            'a[href*="/bars/"]',
            'a[href*="/shopping/"]',
            'a[href*="/entertainment/"]',
            'a[href*="/health-beauty/"]',
            'a[href*="/movies/"]',
            'a[href*="/cafes/"]',
            'a[href*="/markets/"]',
            'a[href*="/spas/"]'
        ]
        
        for selector in article_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and href.startswith('/'):
                    # Извлекаем заголовок
                    title_elem = link.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    title = title_elem.get_text(strip=True) if title_elem else "Untitled"
                    
                    articles.append({
                        'url': href,
                        'title': title,
                        'category': category
                    })
        
        # Убираем дубликаты по URL
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        logger.info(f"Found {len(unique_articles)} unique articles for category {category}")
        return unique_articles
    
    def extract_place_data(self, html: str, article_url: str, category: str) -> List[Dict]:
        """Extract place data from an article page."""
        soup = BeautifulSoup(html, 'html.parser')
        places = []
        
        # Ищем места в статье
        # Это может быть список мест, отдельные описания и т.д.
        
        # Метод 1: Ищем списки мест
        list_selectors = [
            'ul li',
            'ol li', 
            '.list-item',
            '.place-item',
            '.venue-item'
        ]
        
        for selector in list_selectors:
            items = soup.select(selector)
            for item in items:
                place = self._extract_place_from_item(item, article_url, category)
                if place:
                    places.append(place)
        
        # Метод 2: Ищем заголовки, которые могут быть названиями мест
        heading_selectors = ['h2', 'h3', 'h4']
        for selector in heading_selectors:
            headings = soup.select(selector)
            for heading in headings:
                text = heading.get_text(strip=True)
                # Проверяем, похоже ли это на название места
                if self._looks_like_place_name(text):
                    place = self._extract_place_from_heading(heading, article_url, category)
                    if place:
                        places.append(place)
        
        # Метод 3: Ищем блоки с описаниями мест
        content_selectors = [
            '.article-content p',
            '.content p',
            'p'
        ]
        
        for selector in content_selectors:
            paragraphs = soup.select(selector)
            for p in paragraphs:
                text = p.get_text(strip=True)
                if self._contains_place_info(text):
                    place = self._extract_place_from_text(text, article_url, category)
                    if place:
                        places.append(place)
        
        logger.info(f"Extracted {len(places)} places from article {article_url}")
        return places
    
    def _extract_place_from_item(self, item, article_url: str, category: str) -> Optional[Dict]:
        """Extract place data from a list item."""
        text = item.get_text(strip=True)
        if len(text) < 20:  # Слишком короткий текст
            return None
        
        # Ищем название места (обычно в начале)
        lines = text.split('\n')
        name = lines[0].strip() if lines else text[:50]
        
        # Очищаем название
        name = re.sub(r'^\d+\.\s*', '', name)  # Убираем нумерацию
        name = re.sub(r'^\s*[-–—]\s*', '', name)  # Убираем дефисы
        
        if len(name) < 3:
            return None
        
        return {
            'name': name,
            'description': text,
            'source': 'timeout_bangkok',
            'url': urljoin(self.base_url, article_url),
            'flags': [category],
            'area': self._extract_area(text),
            'price_level': self._infer_price_level(text)
        }
    
    def _extract_place_from_heading(self, heading, article_url: str, category: str) -> Optional[Dict]:
        """Extract place data from a heading."""
        name = heading.get_text(strip=True)
        
        # Ищем описание после заголовка
        description = ""
        next_elem = heading.find_next_sibling()
        if next_elem and next_elem.name == 'p':
            description = next_elem.get_text(strip=True)
        
        if len(name) < 3:
            return None
        
        return {
            'name': name,
            'description': description,
            'source': 'timeout_bangkok',
            'url': urljoin(self.base_url, article_url),
            'flags': [category],
            'area': self._extract_area(description or name),
            'price_level': self._infer_price_level(description or name)
        }
    
    def _extract_place_from_text(self, text: str, article_url: str, category: str) -> Optional[Dict]:
        """Extract place data from text content."""
        # Ищем паттерны названий мест
        place_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Restaurant|Cafe|Bar|Club|Gallery|Museum|Park|Market|Spa|Hotel))',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Thai|Chinese|Japanese|Italian|French|Mexican))',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|Road|Avenue|Lane))'
        ]
        
        for pattern in place_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) > 3:  # Минимальная длина названия
                    return {
                        'name': match,
                        'description': text[:200] + "..." if len(text) > 200 else text,
                        'source': 'timeout_bangkok',
                        'url': urljoin(self.base_url, article_url),
                        'flags': [category],
                        'area': self._extract_area(text),
                        'price_level': self._infer_price_level(text)
                    }
        
        return None
    
    def _looks_like_place_name(self, text: str) -> bool:
        """Check if text looks like a place name."""
        if len(text) < 3 or len(text) > 100:
            return False
        
        # Проверяем паттерны названий мест
        place_indicators = [
            'restaurant', 'cafe', 'bar', 'club', 'gallery', 'museum',
            'park', 'market', 'spa', 'hotel', 'mall', 'center', 'plaza'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in place_indicators)
    
    def _contains_place_info(self, text: str) -> bool:
        """Check if text contains information about places."""
        if len(text) < 50:
            return False
        
        place_keywords = [
            'restaurant', 'cafe', 'bar', 'food', 'drink', 'eat',
            'visit', 'go to', 'located', 'address', 'area', 'district'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in place_keywords)
    
    def _extract_area(self, text: str) -> Optional[str]:
        """Extract area/district from text."""
        # Известные районы Бангкока
        bangkok_areas = [
            'Sukhumvit', 'Silom', 'Siam', 'Pratunam', 'Chatuchak',
            'Thonglor', 'Ekkamai', 'Asoke', 'Phrom Phong', 'Ari',
            'Ratchada', 'Ladphrao', 'Bang Na', 'On Nut', 'Phra Khanong',
            'Thonglor', 'Ekkamai', 'Asoke', 'Phrom Phong', 'Ari',
            'Ratchada', 'Ladphrao', 'Bang Na', 'On Nut', 'Phra Khanong'
        ]
        
        text_lower = text.lower()
        for area in bangkok_areas:
            if area.lower() in text_lower:
                return area
        
        return None
    
    def _infer_price_level(self, text: str) -> Optional[int]:
        """Infer price level from text description."""
        text_lower = text.lower()
        
        # Дешево
        if any(word in text_lower for word in ['cheap', 'budget', 'affordable', 'street food', 'local']):
            return 1
        
        # Средне
        if any(word in text_lower for word in ['mid-range', 'moderate', 'reasonable']):
            return 2
        
        # Дорого
        if any(word in text_lower for word in ['expensive', 'luxury', 'high-end', 'premium', 'fine dining']):
            return 4
        
        # Очень дорого
        if any(word in text_lower for word in ['ultra-luxury', 'exclusive', 'VIP']):
            return 5
        
        # По умолчанию средний уровень
        return 2
    
    async def scrape_category(self, category: str, subcategory_url: str) -> List[Dict]:
        """Scrape places from a specific category."""
        logger.info(f"Scraping category {category} from {subcategory_url}")
        
        # Получаем страницу категории
        html = await self.get_page_content(subcategory_url)
        if not html:
            return []
        
        # Извлекаем ссылки на статьи
        articles = self.extract_article_links(html, category)
        logger.info(f"Found {len(articles)} articles in category {category}")
        
        all_places = []
        
        # Обрабатываем каждую статью
        for i, article in enumerate(articles[:10]):  # Ограничиваем для тестирования
            logger.info(f"Processing article {i+1}/{len(articles)}: {article['title']}")
            
            try:
                # Получаем содержимое статьи
                article_html = await self.get_page_content(article['url'])
                if article_html:
                    # Извлекаем места из статьи
                    places = self.extract_place_data(article_html, article['url'], category)
                    all_places.extend(places)
                
                # Небольшая задержка между запросами
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing article {article['url']}: {e}")
                continue
        
        logger.info(f"Total places extracted from category {category}: {len(all_places)}")
        return all_places
    
    async def scrape_all_categories(self) -> List[Dict]:
        """Scrape places from all categories."""
        all_places = []
        
        for category, urls in self.categories.items():
            logger.info(f"Starting to scrape category: {category}")
            
            for url in urls:
                try:
                    places = await self.scrape_category(category, url)
                    all_places.extend(places)
                    
                    # Задержка между категориями
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error scraping category {category} from {url}: {e}")
                    continue
        
        # Убираем дубликаты по названию
        seen_names = set()
        unique_places = []
        for place in all_places:
            if place['name'] not in seen_names:
                seen_names.add(place['name'])
                unique_places.append(place)
        
        logger.info(f"Total unique places extracted: {len(unique_places)}")
        return unique_places


async def main():
    """Test function."""
    logging.basicConfig(level=logging.INFO)
    
    async with TimeoutBangkokPlacesParser() as parser:
        # Тестируем на одной категории
        places = await parser.scrape_category("food_dining", "/food-drink")
        
        print(f"Extracted {len(places)} places:")
        for i, place in enumerate(places[:5]):  # Показываем первые 5
            print(f"{i+1}. {place['name']}")
            print(f"   Description: {place['description'][:100]}...")
            print(f"   Area: {place['area']}")
            print(f"   Price: {place['price_level']}")
            print()


if __name__ == "__main__":
    asyncio.run(main())
