#!/usr/bin/env python3
"""
Debug Things To Do Page
Analyze the things-to-do page for places structure
"""

import sys
from pathlib import Path

# Добавляем tools в Python path
sys.path.insert(0, str(Path('.') / 'tools'))

from fetchers.base import get_html


def main():
    """Debug the things-to-do page structure."""
    print("🔍 Debugging Things To Do Page...")
    print("=" * 60)
    
    # Тестируем страницу things-to-do
    url = "https://www.timeout.com/bangkok/things-to-do"
    print(f"📡 Debugging: {url}")
    
    try:
        soup = get_html(url)
        if not soup:
            print("❌ Failed to get HTML")
            return
        
        # Ищем все статьи
        articles = soup.find_all('article', class_='_article_a9wsr_1')
        print(f"📊 Total articles found: {len(articles)}")
        
        if articles:
            print("\n🔍 Analyzing articles for places structure:")
            
            for i, article in enumerate(articles[:10]):  # Анализируем первые 10 статей
                print(f"\n--- Article {i+1} ---")
                analyze_article_structure(article, i+1)
        
    except Exception as e:
        print(f"❌ Error debugging: {e}")
        import traceback
        traceback.print_exc()


def analyze_article_structure(article, article_num):
    """Analyze the structure of a single article."""
    try:
        print(f"  📄 Article structure:")
        print(f"    Tag: {article.name}")
        print(f"    Classes: {article.get('class', [])}")
        
        # Ищем заголовок статьи
        article_title = article.find('h3', class_='_h3_c6c0h_1')
        if article_title:
            title_text = article_title.get_text(strip=True)
            print(f"    Article Title: {title_text[:60]}...")
        
        # Ищем все изображения в статье
        all_images = article.find_all('img')
        print(f"    Total images: {len(all_images)}")
        
        for j, img in enumerate(all_images):
            src = img.get('src', '')
            alt = img.get('alt', '')
            classes = img.get('class', [])
            print(f"      Image {j+1}: {src[:50]}...")
            print(f"        Alt: {alt[:40]}...")
            print(f"        Classes: {classes}")
        
        # Ищем все ссылки в статье
        all_links = article.find_all('a', href=True)
        print(f"    Total links: {len(all_links)}")
        
        for j, link in enumerate(all_links):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            classes = link.get('class', [])
            
            if text and len(text) > 3 and href.startswith('/'):
                print(f"      Link {j+1}: {text[:40]}... -> {href}")
                print(f"        Classes: {classes}")
        
        # Ищем теги/категории
        print(f"    Content analysis:")
        
        # Ищем в тексте статьи
        article_text = article.get_text()
        
        # Ищем известные категории
        categories = [
            'restaurants', 'food', 'dining', 'bars', 'nightlife', 'clubs',
            'markets', 'shopping', 'malls', 'museums', 'galleries', 'art',
            'parks', 'gardens', 'nature', 'spas', 'wellness', 'yoga',
            'hotels', 'accommodation', 'theaters', 'cinemas', 'concerts',
            'attractions', 'things to do', 'events', 'activities'
        ]
        
        found_categories = []
        for category in categories:
            if category in article_text.lower():
                found_categories.append(category)
        
        if found_categories:
            print(f"      Found categories: {', '.join(found_categories)}")
        
        # Ищем в URL
        if all_links:
            first_link = all_links[0]
            href = first_link.get('href', '')
            if href:
                url_parts = href.split('/')
                if len(url_parts) > 2:
                    section = url_parts[2]
                    print(f"      URL section: {section}")
        
    except Exception as e:
        print(f"  ❌ Error analyzing article: {e}")


if __name__ == "__main__":
    main()
