#!/usr/bin/env python3
"""
Simple test script for Timeout Bangkok parser.
This script works independently without complex imports.
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin
import re

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleTimeoutParser:
    """Simple parser for testing Timeout Bangkok."""
    
    def __init__(self):
        self.base_url = "https://www.timeout.com/bangkok"
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def test_food_dining(self):
        """Test parsing food & dining category."""
        print("🍽️ Testing food & dining category...")
        
        try:
            # Тестируем на главной странице food-drink
            url = f"{self.base_url}/food-drink"
            print(f"🔗 Fetching: {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    print(f"✅ Successfully fetched {len(html)} characters")
                    
                    # Парсим HTML
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Ищем заголовки статей
                    headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
                    print(f"📰 Found {len(headings)} headings")
                    
                    # Показываем первые 10 заголовков
                    print("\n📋 Sample headings:")
                    for i, heading in enumerate(headings[:10], 1):
                        text = heading.get_text(strip=True)
                        if text and len(text) > 5:
                            print(f"{i}. {text}")
                    
                    # Ищем ссылки на статьи
                    links = soup.find_all('a', href=True)
                    article_links = []
                    
                    for link in links:
                        href = link.get('href')
                        if href and any(keyword in href for keyword in ['/food-drink/', '/restaurants/', '/cafes/']):
                            text = link.get_text(strip=True)
                            if text and len(text) > 5:
                                article_links.append({
                                    'url': href,
                                    'text': text
                                })
                    
                    print(f"\n🔗 Found {len(article_links)} article links")
                    
                    # Показываем первые 5 ссылок
                    print("\n📋 Sample article links:")
                    for i, link in enumerate(article_links[:5], 1):
                        print(f"{i}. {link['text']}")
                        print(f"   URL: {link['url']}")
                    
                    return {
                        'success': True,
                        'headings_count': len(headings),
                        'article_links_count': len(article_links),
                        'sample_headings': [h.get_text(strip=True) for h in headings[:5] if h.get_text(strip=True)],
                        'sample_links': article_links[:5]
                    }
                    
                else:
                    print(f"❌ Failed to fetch {url}, status: {response.status}")
                    return {'success': False, 'error': f'HTTP {response.status}'}
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_art_exhibits(self):
        """Test parsing art & exhibits category."""
        print("\n🎨 Testing art & exhibits category...")
        
        try:
            url = f"{self.base_url}/art"
            print(f"🔗 Fetching: {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    print(f"✅ Successfully fetched {len(html)} characters")
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Ищем заголовки
                    headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
                    print(f"📰 Found {len(headings)} headings")
                    
                    # Показываем первые 5 заголовков
                    print("\n📋 Sample headings:")
                    for i, heading in enumerate(headings[:5], 1):
                        text = heading.get_text(strip=True)
                        if text and len(text) > 5:
                            print(f"{i}. {text}")
                    
                    return {'success': True, 'headings_count': len(headings)}
                    
                else:
                    print(f"❌ Failed to fetch {url}, status: {response.status}")
                    return {'success': False, 'error': f'HTTP {response.status}'}
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return {'success': False, 'error': str(e)}

async def main():
    """Main test function."""
    print("🚀 Starting Timeout Bangkok parser test...")
    print("=" * 50)
    
    async with SimpleTimeoutParser() as parser:
        # Тестируем food & dining
        food_result = await parser.test_food_dining()
        
        # Тестируем art & exhibits
        art_result = await parser.test_art_exhibits()
        
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        print(f"🍽️  Food & Dining: {'✅ Success' if food_result['success'] else '❌ Failed'}")
        if food_result['success']:
            print(f"   📰 Headings: {food_result['headings_count']}")
            print(f"   🔗 Article links: {food_result['article_links_count']}")
        
        print(f"🎨 Art & Exhibits: {'✅ Success' if art_result['success'] else '❌ Failed'}")
        if art_result['success']:
            print(f"   📰 Headings: {art_result['headings_count']}")
        
        print("\n🎯 Next steps:")
        print("1. Install aiohttp: pip install aiohttp")
        print("2. Run the full parser: python core/fetchers/timeout_bangkok_parser.py")
        print("3. Use the CLI: python scripts/timeout_places_cli.py test")

if __name__ == "__main__":
    asyncio.run(main())
