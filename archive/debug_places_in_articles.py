#!/usr/bin/env python3
"""
Debug Places Inside Articles
Analyze how places are organized within Time Out Bangkok articles
"""

import sys
from pathlib import Path

# Добавляем tools в Python path
sys.path.insert(0, str(Path('.') / 'tools'))

from fetchers.base import get_html


def main():
    """Debug how places are organized within articles."""
    print("🔍 Debugging Places Inside Articles...")
    print("=" * 60)
    
    # Тестируем главную страницу
    url = "https://www.timeout.com/bangkok"
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
            
            for i, article in enumerate(articles[:5]):  # Анализируем первые 5 статей
                print(f"\n--- Article {i+1} ---")
                analyze_places_in_article(article, i+1)
        
    except Exception as e:
        print(f"❌ Error debugging: {e}")
        import traceback
        traceback.print_exc()


def analyze_places_in_article(article, article_num):
    """Analyze how places are organized within a single article."""
    try:
        print(f"  📄 Article structure:")
        print(f"    Tag: {article.name}")
        print(f"    Classes: {article.get('class', [])}")
        
        # Ищем заголовок статьи
        article_title = article.find('h3', class_='_h3_c6c0h_1')
        if article_title:
            title_text = article_title.get_text(strip=True)
            print(f"    Article Title: {title_text[:60]}...")
        
        # Ищем все ссылки в статье
        all_links = article.find_all('a', href=True)
        print(f"    Total links: {len(all_links)}")
        
        # Анализируем каждую ссылку как потенциальное место
        places_in_article = []
        
        for j, link in enumerate(all_links):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            classes = link.get('class', [])
            
            # Пропускаем технические ссылки
            if any(skip in text.lower() for skip in ['read more', 'readmore', '...']):
                continue
            
            if text and len(text) > 3 and href.startswith('/'):
                print(f"      Link {j+1}: {text[:40]}... -> {href}")
                print(f"        Classes: {classes}")
                
                # Ищем изображение рядом с этой ссылкой
                nearby_image = find_image_near_link(link)
                if nearby_image:
                    src = nearby_image.get('src', '')
                    alt = nearby_image.get('alt', '')
                    print(f"        Nearby Image: {src[:40]}...")
                    print(f"        Image Alt: {alt[:30]}...")
                
                # Ищем теги/категории рядом
                nearby_tags = find_tags_near_link(link)
                if nearby_tags:
                    print(f"        Nearby Tags: {nearby_tags}")
                
                places_in_article.append({
                    'title': text,
                    'url': href,
                    'image': nearby_image.get('src', '') if nearby_image else None,
                    'alt': nearby_image.get('alt', '') if nearby_image else None,
                    'tags': nearby_tags
                })
        
        print(f"    📍 Places found in article: {len(places_in_article)}")
        
        # Показываем детали каждого места
        for k, place in enumerate(places_in_article):
            print(f"      Place {k+1}: {place['title']}")
            print(f"        URL: {place['url']}")
            if place['image']:
                print(f"        Image: {place['image'][:40]}...")
            if place['alt']:
                print(f"        Description: {place['alt'][:50]}...")
            if place['tags']:
                print(f"        Tags: {', '.join(place['tags'])}")
        
    except Exception as e:
        print(f"  ❌ Error analyzing article: {e}")


def find_image_near_link(link_element):
    """Find image near a link element."""
    try:
        # Ищем изображение в родительском элементе
        parent = link_element.parent
        if parent:
            # Ищем изображение в том же контейнере
            img = parent.find('img')
            if img:
                return img
            
            # Ищем в соседних элементах
            siblings = parent.find_next_siblings()
            for sibling in siblings[:3]:  # Проверяем первые 3 соседа
                img = sibling.find('img')
                if img:
                    return img
        
        # Ищем в дочерних элементах ссылки
        img = link_element.find('img')
        if img:
            return img
        
        return None
        
    except Exception:
        return None


def find_tags_near_link(link_element):
    """Find tags/categories near a link element."""
    try:
        tags = []
        
        # Ищем в родительском элементе
        parent = link_element.parent
        if parent:
            # Ищем теги в тексте родителя
            parent_text = parent.get_text()
            
            # Ищем известные категории
            categories = [
                'restaurants', 'food', 'dining', 'bars', 'nightlife', 'clubs',
                'markets', 'shopping', 'malls', 'museums', 'galleries', 'art',
                'parks', 'gardens', 'nature', 'spas', 'wellness', 'yoga',
                'hotels', 'accommodation', 'theaters', 'cinemas', 'concerts'
            ]
            
            for category in categories:
                if category in parent_text.lower():
                    tags.append(category)
        
        return tags
        
    except Exception:
        return []


if __name__ == "__main__":
    main()
