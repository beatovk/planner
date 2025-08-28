#!/usr/bin/env python3
"""
Test Page Content
Check what content is actually returned from Time Out Bangkok
"""

import sys
from pathlib import Path

# Добавляем tools в Python path
sys.path.insert(0, str(Path('.') / 'tools'))

from fetchers.base import get_html


def main():
    """Test the page content."""
    print("🧪 Testing Page Content...")
    print("=" * 50)
    
    url = "https://www.timeout.com/bangkok/things-to-do/best-things-to-do-in-bangkok"
    print(f"📡 Testing: {url}")
    
    try:
        soup = get_html(url)
        if not soup:
            print("❌ Failed to get HTML")
            return
        
        print("✅ HTML received successfully")
        
        # Проверяем заголовок страницы
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            print(f"📄 Page title: {title_text}")
        
        # Проверяем все изображения
        all_images = soup.find_all('img')
        print(f"📸 Total images found: {len(all_images)}")
        
        if all_images:
            print("  First 5 images:")
            for i, img in enumerate(all_images[:5]):
                src = img.get('src', '')
                alt = img.get('alt', '')
                print(f"    {i+1}. src: {src[:50]}...")
                print(f"       alt: {alt[:30]}...")
        
        # Проверяем все заголовки
        all_headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        print(f"📝 Total headings found: {len(all_headings)}")
        
        if all_headings:
            print("  First 5 headings:")
            for i, heading in enumerate(all_headings[:5]):
                text = heading.get_text(strip=True)
                tag = heading.name
                print(f"    {i+1}. <{tag}> {text[:50]}...")
        
        # Проверяем все параграфы
        all_paragraphs = soup.find_all('p')
        print(f"📄 Total paragraphs found: {len(all_paragraphs)}")
        
        if all_paragraphs:
            print("  First 3 paragraphs:")
            for i, p in enumerate(all_paragraphs[:3]):
                text = p.get_text(strip=True)
                if text and len(text) > 10:
                    print(f"    {i+1}. {text[:80]}...")
        
        # Проверяем все ссылки
        all_links = soup.find_all('a', href=True)
        print(f"🔗 Total links found: {len(all_links)}")
        
        if all_links:
            print("  First 5 links:")
            for i, link in enumerate(all_links[:5]):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                if text and len(text) > 3:
                    print(f"    {i+1}. {text[:30]}... -> {href[:50]}...")
        
        # Проверяем размер HTML
        html_text = soup.get_text()
        print(f"📊 Total text length: {len(html_text)} characters")
        print(f"📊 First 200 characters: {html_text[:200]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
