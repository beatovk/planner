#!/usr/bin/env python3
"""
Test Time Out Bangkok Parser
Test the existing parser to see what's happening
"""

import sys
from pathlib import Path

# Добавляем tools в Python path
sys.path.insert(0, str(Path('.') / 'tools'))

from fetchers.timeout_bkk import fetch as fetch_timeout_bkk, get_timeout_html
from fetchers.base import get_html


def main():
    """Test the Time Out Bangkok parser."""
    print("🧪 Testing Time Out Bangkok Parser...")
    print("=" * 50)
    
    # Тест 1: Проверка базового HTML
    print("📡 Test 1: Testing basic HTML fetching...")
    test_basic_html()
    print()
    
    # Тест 2: Проверка парсера
    print("🔍 Test 2: Testing parser...")
    test_parser()
    print()
    
    # Тест 3: Проверка конкретных URL
    print("🌐 Test 3: Testing specific URLs...")
    test_specific_urls()
    print()


def test_basic_html():
    """Test basic HTML fetching."""
    test_urls = [
        "https://www.timeout.com/bangkok",
        "https://www.timeout.com/bangkok/things-to-do",
        "https://www.timeout.com/bangkok/food-and-drink"
    ]
    
    for url in test_urls:
        print(f"   Testing: {url}")
        
        # Тест 1: get_timeout_html (специализированный)
        try:
            soup = get_timeout_html(url)
            if soup:
                title = soup.find('title')
                title_text = title.get_text() if title else "No title"
                print(f"     ✓ get_timeout_html: Success (Title: {title_text[:50]}...)")
            else:
                print(f"     ✗ get_timeout_html: Failed")
        except Exception as e:
            print(f"     ✗ get_timeout_html: Error - {e}")
        
        # Тест 2: get_html (базовый)
        try:
            soup = get_html(url)
            if soup:
                title = soup.find('title')
                title_text = title.get_text() if title else "No title"
                print(f"     ✓ get_html: Success (Title: {title_text[:50]}...)")
            else:
                print(f"     ✗ get_html: Failed")
        except Exception as e:
            print(f"     ✗ get_html: Error - {e}")
        
        print()


def test_parser():
    """Test the parser function."""
    print("   Testing parser with category: food")
    
    try:
        places = fetch_timeout_bkk(cat_id="food")
        if places:
            print(f"     ✓ Parser success: {len(places)} places")
            
            # Показываем первые 3 места
            for i, place in enumerate(places[:3]):
                print(f"       {i+1}. {place.get('title', 'No title')}")
                print(f"          URL: {place.get('url', 'No URL')}")
                print(f"          Venue: {place.get('venue', 'No venue')}")
                print(f"          Image: {'Yes' if place.get('image') else 'No'}")
                print()
        else:
            print("     ⚠️ Parser returned no places")
            
    except Exception as e:
        print(f"     ✗ Parser error: {e}")


def test_specific_urls():
    """Test specific URLs that should work."""
    specific_urls = [
        "https://www.timeout.com/bangkok/things-to-do",
        "https://www.timeout.com/bangkok/attractions",
        "https://www.timeout.com/bangkok/restaurants"
    ]
    
    for url in specific_urls:
        print(f"   Testing: {url}")
        
        try:
            soup = get_timeout_html(url)
            if soup:
                # Ищем карточки
                cards = soup.select(".card, .event-card, .listing-card, article, .article-card, .feature-card")
                print(f"     ✓ Found {len(cards)} potential cards")
                
                # Показываем первые 3 карточки
                for i, card in enumerate(cards[:3]):
                    title_el = card.select_one("h1, h2, h3, .title, .card-title, .article-title")
                    title = title_el.get_text(strip=True) if title_el else "No title"
                    print(f"       {i+1}. {title[:50]}...")
                    
                    link_el = card.select_one("a")
                    if link_el:
                        href = link_el.get("href", "")
                        print(f"          Link: {href[:50]}...")
                
            else:
                print(f"     ✗ Failed to get HTML")
                
        except Exception as e:
            print(f"     ✗ Error: {e}")
        
        print()


if __name__ == "__main__":
    main()
