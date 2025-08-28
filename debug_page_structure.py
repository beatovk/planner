#!/usr/bin/env python3
"""
Debug Page Structure
Analyze the general structure of the things-to-do page
"""

import sys
from pathlib import Path

# Добавляем tools в Python path
sys.path.insert(0, str(Path('.') / 'tools'))

from fetchers.base import get_html


def main():
    """Debug the general page structure."""
    print("🔍 Debugging Page Structure...")
    print("=" * 60)
    
    # Тестируем страницу things-to-do
    url = "https://www.timeout.com/bangkok/things-to-do"
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
        
        # Ищем все возможные контейнеры
        print("\n🔍 Looking for content containers...")
        
        # Ищем все элементы с классами
        all_elements_with_classes = soup.find_all(attrs={"class": True})
        print(f"Total elements with classes: {len(all_elements_with_classes)}")
        
        # Группируем по тегам
        tag_counts = {}
        for element in all_elements_with_classes:
            tag = element.name
            if tag not in tag_counts:
                tag_counts[tag] = 0
            tag_counts[tag] += 1
        
        print("Elements by tag:")
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {tag}: {count}")
        
        # Ищем статьи с любыми классами
        print("\n🔍 Looking for articles...")
        all_articles = soup.find_all('article')
        print(f"Total articles: {len(all_articles)}")
        
        for i, article in enumerate(all_articles[:5]):
            print(f"  Article {i+1}:")
            print(f"    Classes: {article.get('class', [])}")
            print(f"    ID: {article.get('id', 'No ID')}")
            
            # Ищем заголовки
            headings = article.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if headings:
                for heading in headings:
                    text = heading.get_text(strip=True)
                    print(f"    Heading: {text[:50]}...")
            
            # Ищем ссылки
            links = article.find_all('a', href=True)
            if links:
                for link in links[:2]:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    print(f"    Link: {text[:30]}... -> {href}")
        
        # Ищем div'ы с контентом
        print("\n🔍 Looking for content divs...")
        content_divs = soup.find_all('div', class_=True)
        print(f"Total divs with classes: {len(content_divs)}")
        
        # Показываем первые 10 div'ов с классами
        for i, div in enumerate(content_divs[:10]):
            classes = div.get('class', [])
            print(f"  Div {i+1}: {classes}")
            
            # Ищем заголовки в div
            headings = div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if headings:
                for heading in headings:
                    text = heading.get_text(strip=True)
                    if text and len(text) > 5:
                        print(f"    Heading: {text[:40]}...")
            
            # Ищем ссылки в div
            links = div.find_all('a', href=True)
            if links:
                for link in links[:2]:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    if text and len(text) > 3:
                        print(f"    Link: {text[:30]}... -> {href}")
        
        # Ищем изображения
        print("\n🔍 Looking for images...")
        all_images = soup.find_all('img')
        print(f"Total images: {len(all_images)}")
        
        # Показываем первые 5 изображений
        for i, img in enumerate(all_images[:5]):
            src = img.get('src', '')
            alt = img.get('alt', '')
            classes = img.get('class', [])
            print(f"  Image {i+1}: {src[:50]}...")
            print(f"    Alt: {alt[:30]}...")
            print(f"    Classes: {classes}")
        
    except Exception as e:
        print(f"❌ Error debugging: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
