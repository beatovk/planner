#!/usr/bin/env python3
"""
Debug Time Out Bangkok Structure
Detailed inspection of HTML structure to understand article layout
"""

import sys
from pathlib import Path

# Добавляем tools в Python path
sys.path.insert(0, str(Path('.') / 'tools'))

from fetchers.base import get_html


def main():
    """Debug the Time Out Bangkok HTML structure in detail."""
    print("🔍 Debugging Time Out Bangkok Structure...")
    print("=" * 60)
    
    # Тестируем главную страницу
    url = "https://www.timeout.com/bangkok"
    print(f"📡 Debugging: {url}")
    
    try:
        soup = get_html(url)
        if not soup:
            print("❌ Failed to get HTML")
            return
        
        # Получаем заголовок страницы
        title = soup.find('title')
        title_text = title.get_text() if title else "No title"
        print(f"📄 Page Title: {title_text}")
        
        # Ищем все статьи
        articles = soup.find_all('article')
        print(f"📊 Total articles found: {len(articles)}")
        
        if articles:
            print("\n🔍 Analyzing first 3 articles in detail:")
            
            for i, article in enumerate(articles[:3]):
                print(f"\n--- Article {i+1} ---")
                analyze_article_structure(article, i+1)
        
        # Ищем альтернативные структуры
        print("\n🔍 Looking for alternative structures...")
        look_for_alternative_structures(soup)
        
    except Exception as e:
        print(f"❌ Error debugging: {e}")
        import traceback
        traceback.print_exc()


def analyze_article_structure(article, article_num):
    """Analyze the structure of a single article."""
    try:
        print(f"  Tag: {article.name}")
        print(f"  Classes: {article.get('class', [])}")
        print(f"  ID: {article.get('id', 'No ID')}")
        
        # Ищем заголовки
        headings = article.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        print(f"  Headings found: {len(headings)}")
        
        for j, heading in enumerate(headings):
            heading_text = heading.get_text(strip=True)
            heading_tag = heading.name
            heading_classes = heading.get('class', [])
            print(f"    {j+1}. <{heading_tag}> {heading_text[:50]}...")
            print(f"       Classes: {heading_classes}")
        
        # Ищем ссылки
        links = article.find_all('a', href=True)
        print(f"  Links found: {len(links)}")
        
        for j, link in enumerate(links[:3]):  # Показываем первые 3
            href = link.get('href', '')
            text = link.get_text(strip=True)
            classes = link.get('class', [])
            print(f"    {j+1}. {text[:40]}... -> {href}")
            print(f"       Classes: {classes}")
        
        # Ищем изображения
        images = article.find_all('img')
        print(f"  Images found: {len(images)}")
        
        for j, img in enumerate(images):
            src = img.get('src', '')
            alt = img.get('alt', '')
            classes = img.get('class', [])
            print(f"    {j+1}. {src[:50]}...")
            print(f"       Alt: {alt[:30]}...")
            print(f"       Classes: {classes}")
        
        # Ищем параграфы
        paragraphs = article.find_all('p')
        print(f"  Paragraphs found: {len(paragraphs)}")
        
        for j, p in enumerate(paragraphs[:2]):  # Показываем первые 2
            text = p.get_text(strip=True)
            if text and len(text) > 10:
                print(f"    {j+1}. {text[:80]}...")
        
        # Ищем div'ы с контентом
        content_divs = article.find_all('div', class_=True)
        print(f"  Content divs found: {len(content_divs)}")
        
        for j, div in enumerate(content_divs[:3]):  # Показываем первые 3
            classes = div.get('class', [])
            text = div.get_text(strip=True)
            if text and len(text) > 10:
                print(f"    {j+1}. Classes: {classes}")
                print(f"       Text: {text[:60]}...")
        
    except Exception as e:
        print(f"  ❌ Error analyzing article: {e}")


def look_for_alternative_structures(soup):
    """Look for alternative content structures."""
    print("  🔍 Checking for content containers...")
    
    # Ищем контейнеры с контентом
    content_selectors = [
        '[class*="content"]',
        '[class*="article"]',
        '[class*="post"]',
        '[class*="item"]',
        '[class*="listing"]',
        '[class*="card"]',
        '[class*="tile"]'
    ]
    
    for selector in content_selectors:
        try:
            elements = soup.select(selector)
            if elements:
                print(f"    ✓ {selector}: {len(elements)} elements")
                
                # Показываем структуру первого элемента
                if len(elements) > 0:
                    first = elements[0]
                    print(f"      First element: {first.name}, classes: {first.get('class', [])}")
                    
                    # Ищем заголовок и изображение
                    title_el = first.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    if title_el:
                        title_text = title_el.get_text(strip=True)
                        print(f"      Title: {title_text[:40]}...")
                    
                    img_el = first.find('img')
                    if img_el:
                        src = img_el.get('src', '')
                        print(f"      Image: {src[:40]}...")
                    
                    break
                    
            else:
                print(f"    ⚠️ {selector}: No elements")
                
        except Exception as e:
            print(f"    ✗ {selector}: Error - {e}")
    
    # Ищем все элементы с изображениями
    print("\n  🔍 Looking for all image containers...")
    all_images = soup.find_all('img')
    print(f"    Total images on page: {len(all_images)}")
    
    # Группируем изображения по родительским элементам
    image_parents = {}
    for img in all_images:
        parent = img.parent
        if parent:
            parent_tag = parent.name
            parent_classes = parent.get('class', [])
            parent_key = f"{parent_tag}:{','.join(parent_classes)}"
            
            if parent_key not in image_parents:
                image_parents[parent_key] = []
            
            src = img.get('src', '')
            alt = img.get('alt', '')
            image_parents[parent_key].append({
                'src': src,
                'alt': alt
            })
    
    print(f"    Image parent types: {len(image_parents)}")
    for parent_type, images in list(image_parents.items())[:5]:  # Показываем первые 5
        print(f"      {parent_type}: {len(images)} images")
        if images:
            first_img = images[0]
            print(f"        Example: {first_img['src'][:40]}...")
            if first_img['alt']:
                print(f"        Alt: {first_img['alt'][:30]}...")


if __name__ == "__main__":
    main()
