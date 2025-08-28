#!/usr/bin/env python3
"""
Inspect Time Out Bangkok Structure
Look at the actual HTML structure to understand how to parse it
"""

import sys
from pathlib import Path

# Добавляем tools в Python path
sys.path.insert(0, str(Path('.') / 'tools'))

from fetchers.base import get_html


def main():
    """Inspect the Time Out Bangkok HTML structure."""
    print("🔍 Inspecting Time Out Bangkok Structure...")
    print("=" * 60)
    
    # Тестируем работающие URL
    working_urls = [
        "https://www.timeout.com/bangkok",
        "https://www.timeout.com/bangkok/things-to-do"
    ]
    
    for url in working_urls:
        print(f"📡 Inspecting: {url}")
        inspect_page_structure(url)
        print()


def inspect_page_structure(url):
    """Inspect the structure of a specific page."""
    try:
        soup = get_html(url)
        if not soup:
            print("   ❌ Failed to get HTML")
            return
        
        # Получаем заголовок
        title = soup.find('title')
        title_text = title.get_text() if title else "No title"
        print(f"   📄 Title: {title_text}")
        
        # Ищем все возможные селекторы для карточек
        print("   🔍 Looking for card selectors...")
        
        selectors_to_try = [
            ".card", ".event-card", ".listing-card", "article", ".article-card", 
            ".feature-card", ".post", ".item", ".listing", ".result",
            "[class*='card']", "[class*='article']", "[class*='post']",
            "[class*='listing']", "[class*='item']"
        ]
        
        for selector in selectors_to_try:
            try:
                elements = soup.select(selector)
                if elements:
                    print(f"     ✓ {selector}: {len(elements)} elements")
                    
                    # Показываем структуру первого элемента
                    if len(elements) > 0:
                        first_element = elements[0]
                        print(f"       First element structure:")
                        print(f"         Tag: {first_element.name}")
                        print(f"         Classes: {first_element.get('class', [])}")
                        
                        # Ищем заголовок
                        title_el = first_element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                        if title_el:
                            title_text = title_el.get_text(strip=True)
                            print(f"         Title: {title_text[:50]}...")
                        
                        # Ищем ссылку
                        link_el = first_element.find('a')
                        if link_el:
                            href = link_el.get('href', '')
                            print(f"         Link: {href[:50]}...")
                        
                        # Ищем изображение
                        img_el = first_element.find('img')
                        if img_el:
                            src = img_el.get('src', '')
                            print(f"         Image: {src[:50]}...")
                        
                        break
                        
                else:
                    print(f"     ⚠️ {selector}: No elements found")
                    
            except Exception as e:
                print(f"     ✗ {selector}: Error - {e}")
        
        # Ищем альтернативные структуры
        print("   🔍 Looking for alternative structures...")
        
        # Ищем все заголовки
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        print(f"     Total headings: {len(headings)}")
        
        # Показываем первые 5 заголовков
        for i, heading in enumerate(headings[:5]):
            text = heading.get_text(strip=True)
            if text and len(text) > 5:
                print(f"       {i+1}. {text[:60]}...")
        
        # Ищем все ссылки
        links = soup.find_all('a', href=True)
        print(f"     Total links: {len(links)}")
        
        # Показываем первые 5 ссылок с текстом
        link_count = 0
        for link in links:
            text = link.get_text(strip=True)
            href = link.get('href', '')
            if text and len(text) > 5 and href.startswith('/'):
                print(f"       {link_count+1}. {text[:40]}... -> {href}")
                link_count += 1
                if link_count >= 5:
                    break
        
        # Ищем все изображения
        images = soup.find_all('img')
        print(f"     Total images: {len(images)}")
        
        # Показываем первые 3 изображения
        for i, img in enumerate(images[:3]):
            src = img.get('src', '')
            alt = img.get('alt', '')
            if src:
                print(f"       {i+1}. {src[:50]}... (alt: {alt[:30]}...)")
        
    except Exception as e:
        print(f"   ❌ Error inspecting page: {e}")


if __name__ == "__main__":
    main()
